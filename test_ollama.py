import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")


async def generate_response(prompt: str):

    async with httpx.AsyncClient(timeout=120) as client:

        response = await client.post(
            f"{OLLAMA_URL}/api/chat",
            headers={
                "ngrok-skip-browser-warning": "true"
            },
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "stream": False
            }
        )

        response.raise_for_status()

        data = response.json()

        return data["message"]["content"]


async def main():

    data = await generate_response("what is fastapi")

    print("this is AI response:", data)


asyncio.run(main())