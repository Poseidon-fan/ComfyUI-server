"""
this is an example of the client code written by fastapi that will interact with the server
"""
import uvicorn
from fastapi import FastAPI

app = FastAPI()


@app.post("/callback")
async def callback(data: dict):
    print(f"callback client data: {data}")


if __name__ == "__main__":
    uvicorn.run("client_example:app", host="0.0.0.0", port=9000)
