# ComfyUI-server
Due to the incomplete backend API interface provided by ComfyUI, it is very inconvenient to deploy ComfyUI related workflow microservices in one's own application. Therefore, I wrote this project as an enhanced backend implementation solution for ComfyUI.

## Features
- Support deploying **any** ComfyUI workflow in a factory-like manner.
- Store the generated image in S3.
- Monitor ComfyUI service and notify the client through **webhook** when image generation is complete.
- Automatically clean up excess local input and output image files.
- Record task flow and save error files.

The system architecture diagram is as follows:
![flow_chart](./images/flow_chart.png)

## Usage
1. clone this repository
```bash
git clone https://github.com/Poseidon-fan/ComfyUI-server.git
```

2. configure your environment variables

Create `.env` file in ComfyS3 root folder with the following variables:
```text
COMFY_HOST = "localhost"                               # ComfyUI service host
COMFY_PORT = "8188"                                    # ComfyUI service port
COMFY_CLIENT_ID = "7777777"                            # ComfyUI server client id, could be specified arbitrarily

AWS_SECRET_ACCESS_KEY = "your_secret_access_key"       # AWS secret access key
AWS_ACCESS_KEY_ID = "your_access_key_id"               # AWS access key id
S3_BUCKET = "your_S3_bucket_name"                      # S3 bucket name
S3_REGION_NAME = "your_S3_region_name"                 # S3 region

RDB_USERNAME = "root"                                  # Postgres username
RDB_PASSWORD = "123456"                                # Postgres password
RDB_HOST = "localhost"                                 # Postgres host
RDB_PORT = "5432"                                      # Postgres port
RDB_NAME = "comfy"                                     # Postgres database name

CALL_BACK_BASE_URL = "http://localhost:8000/callback"  # webhook callback url
FALLBACK_PATH = "fallback"                             # fallback local path for error files
SERVICE_PORT = 8000                                    # server port
ROUTE_PREFIX = "/api/v1"                               # api route prefix
```

3. install [fileCleaner node](https://github.com/Poseidon-fan/ComfyUI-fileCleaner)

make sure your comfyUI has already installed this custom node.

4. run the server
```bash
cd ComfyUI-server
python -m venv venv  # create virtual environment
# activate virtual environment
# on windows, use venv\Scripts\activate
source venv/bin/activate  
pip install -r requirements.txt
cd src
python main.py
```

## How it works
You could refer to the flow chart above to understand the workflow of this project. Here is a brief introduction to the main components:

### interact with ComfyUI
By default, the APi working mode of ComfyUI is:
- The information sent by the user to ComfyUI contains two fields:
  - `prompt`: contains workflow information for ComfyUI
  - `clientId`: request sender's identification
  
  Once received a prompt, ComfyUI will generate a prompt_id and send back.
  
- You can establish a websocket connection to ComfyUI based on the clientId. ComfyUI will send the processing information for requests with the same clientId.
- The SaveImage and LoadImage nodes native to ComfyUI can only retrieve/output files from local folders.

So, by using an environment variable to write a dead ClientId, this ID is always included in every request sent, and a background task is started to maintain the connection with ComfyUI. 
I manually filtered out the information of task completion and traced back to the results of the task

### Provide external interfaces
I use fastapi, which is a python web framework, to provide external interfaces.
The core code is in `src/api` folder, which contains the following files:
```python
# src/api/__init__.py

class ServiceType(Enum):
    TEXT2IMG = 'text2img'
    IMG2IMG = 'img2img'


class RequestDTO(BaseModel):
    service_type: ServiceType
    id: int
    params: dict

@router.post('')
async def queue_prompt(request_dto: RequestDTO):
    """commit a prompt to the comfy server"""
    service_func = getattr(Service, request_dto.service_type.value)
    return await service_func(request_dto.id, request_dto.params)
```
The ServiceType enum class contains the service types that can be provided, and the RequestDTO class is used to receive the request parameters. The `queue_prompt` function is the main entry point for the external interface, which will call the corresponding service function according to the service type.

```python
# src/api/service.py
class Service:
    @staticmethod
    async def text2img(id: int, params: dict) -> Record:
        text = params.get('text')
        prompt_str = TEXT2IMG_PROMPT_TEMPLATE.substitute(text=text)
        prompt_json = json.loads(prompt_str)
        return await comfy_client.queue_prompt(id, prompt_json)

    @staticmethod
    async def img2img(id: int, params: dict) -> Record:
        text = params.get('text')
        image_base64 = params.get('image')

        # upload image to comfyui
        image_bytes = base64.b64decode(image_base64)
        resp = await comfy_client.upload_image(image_bytes)
        image_path = resp['name']
        if resp['subfolder']:
            image_path = f"{resp['subfolder']}/{image_path}"

        # create prompt
        prompt_str = IMG2IMG_PROMPT_TEMPLATE.substitute(text=text, image=image_path)
        prompt_json = json.loads(prompt_str)
        try:
            return await comfy_client.queue_prompt(id, prompt_json)
        finally:
            # clean up the input file after the prompt is queued
            await comfy_client.clean_file(is_input=True, image_path=image_path)
```
The `Service` class contains the service functions that can be provided. The above are two examples.

The workflow templates are stored in `src/workflows`, which can be configured according to your workflow requirements.

### Upload result image to S3
The code could be found in `src/s3`, it's just a basic encapsulation of the aiobotocore library.

### Webhook
In this system setup, a client-side `client_url` needs to be configured in the environment variable, 
and every time the client sends a request, it must include the client's `id`. 
When this service detects that ComfyUI has completed a prompt processing information and sent the file to S3 storage, 
it will access the `client_url/id` and include detailed result information in the request body.

### clean local input and output images
Please refer to this custom node of ComfyUI: [https://github.com/Poseidon-fan/ComfyUI-fileCleaner](https://github.com/Poseidon-fan/ComfyUI-fileCleaner)

### record task flow and save error files 
I use postgres as rdb to record these information:

| field          | introduction                       |
|----------------|------------------------------------|
| id             | the id from the client             |
| prompt_id      | the prompt_id generated by ComfyUI |
| s3_key         | key of the s3 object               |
| comfy_filepath | image path locally                 |

when there's an error when uploading to s3 or webhook, the error file will be saved in the fallback path. It's path is the same as comfy_filepath.

## How to add a new workflow
Here, I take the example of the text production workflow of the flux model in the repository.
1. go to your comfyui and export workflow API:

![export_api](./images/export_api.png)

2. create a new file in `src/workflows` folder, and paste the exported API into it. Replace the parameters you want to configure with $ (python template string format).
3. add a enum member in `src/api/__init__.py` ServiceType class.
4. create a function in `src/api/service.py` Service class, make sure the function name is the same as the enum member you added. And implement the function according to the workflow you exported.

Now you can use the new workflow in your application.

The base request json format is:
```json
{
    "service_type": "service type. example: text2img",
    "params": {
        // base on your workflow
        "text": "prompt text",
        "image": "base64_format "
    },
    "id": 1  // id from client
}
```
The immediate response and the webhook request format is:
```json
{
  "prompt_id": "d8f9e16e-af8a-4315-9584-5e669bbdf3af", 
  "s3_key": "fa39816b-e89f-4702-bce6-24351825e2ae.png", 
  "id": 101, 
  "comfy_filepath": "ComfyUI_00157_.png"
}
```

**Contributions are welcome! Feel free to star, fork, and submit PRs to help improve this project. 😊**