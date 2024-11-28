import asyncio

import httpx

url = "http://localhost:8000/api/v1"


async def send_request(text: str, task_id: int):
    data = {
        "service_type": "text2img",
        "params": {
            "text": text,
        },
        "client_task_id": task_id,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=data)
        print(resp.json())
        await asyncio.sleep(0.2)


async def test():
    await send_request("1boy", 100)
    await send_request("2boys", 101)
    await send_request("3boys", 102)
    await send_request("4boys", 103)
    await send_request("5boys", 104)
    await send_request("6boys", 105)
    await send_request("7boys", 106)
    await send_request("8boys", 107)
    await send_request("9boys", 108)
    await send_request("10boys", 109)


if __name__ == "__main__":
    asyncio.run(test())
