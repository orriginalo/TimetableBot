import asyncio
import asyncpg

async def test_db():
  conn = await asyncpg.connect(user="timetablebot", password="timetablebot", database="timetablebot", host="localhost")
  print("Connected successfully!")
  await conn.close()

asyncio.run(test_db())