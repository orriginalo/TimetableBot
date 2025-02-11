import asyncio
import aiohttp


async def fetch_progress():
    url = "http://localhost:8000/screenshots/пдо-16/full"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            async for line in response.content:
                if line:
                    # Строки приходят в формате: "data: сообщение\n\n"
                    decoded_line = line.decode("utf-8")
                    if decoded_line.startswith("data:"):
                        progress = decoded_line[5:].strip()
                        print(f"Прогресс: {progress}")
                        
asyncio.run(fetch_progress())