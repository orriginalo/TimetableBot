import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv(override=True)


class Config(BaseModel):
  BOT_TOKEN: str = os.getenv("BOT_TOKEN")
  
  LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
  
  API_HOST: str = os.getenv("API_HOST")
  API_PORT: str = os.getenv("API_PORT")
  
  POSTGRES_HOST: str = os.getenv("POSTGRES_HOST")
  POSTGRES_PORT: str = os.getenv("POSTGRES_PORT")
  POSTGRES_USER: str = os.getenv("POSTGRES_USER")
  POSTGRES_DB: str = os.getenv("POSTGRES_DB")
  POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD")
  
  @property
  def API_URL(self) -> str:
    return f"http://{self.API_HOST}:{self.API_PORT}"
  
  @property
  def SQLALCHEMY_URL(self) -> str:
    return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
  
  @property
  def SQLALCHEMY_URL_SYNC(self) -> str:
    return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
settings = Config()