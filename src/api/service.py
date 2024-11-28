import base64
import json

from comfyui import comfyui_servers
from database import ComfyUIRecord
from workflows.img2img import IMG2IMG_COMFYUI_PROMPT_TEMPLATE
from workflows.text2img import TEXT2IMG_COMFYUI_PROMPT_TEMPLATE


def _get_comfyui_server():
    """schedule the comfyui server with the least queue remaining"""
    return min(comfyui_servers, key=lambda x: x.queue_remaining)


class Service:
    @staticmethod
    async def text2img(client_task_id: str, client_callback_url: str, params: dict) -> ComfyUIRecord:
        comfyui_server = _get_comfyui_server()
        text = params.get("text")
        prompt_str = TEXT2IMG_COMFYUI_PROMPT_TEMPLATE.substitute(text=text)
        prompt_json = json.loads(prompt_str)
        return await comfyui_server.queue_prompt(client_task_id, client_callback_url, prompt_json)

    @staticmethod
    async def img2img(client_task_id: str, client_callback_url: str, params: dict) -> ComfyUIRecord:
        comfyui_server = _get_comfyui_server()
        text = params.get("text")
        image_base64 = params.get("image")

        # upload image to comfyui
        image_bytes = base64.b64decode(image_base64)
        resp = await comfyui_server.upload_image(image_bytes)
        image_path = resp["name"]
        if resp["subfolder"]:
            image_path = f"{resp['subfolder']}/{image_path}"

        # create prompt
        prompt_str = IMG2IMG_COMFYUI_PROMPT_TEMPLATE.substitute(text=text, image=image_path)
        prompt_json = json.loads(prompt_str)
        try:
            return await comfyui_server.queue_prompt(client_task_id, client_callback_url, prompt_json)
        finally:
            # clean up the input file after the prompt is queued
            await comfyui_server.clean_local_file(is_input=True, image_path=image_path)
