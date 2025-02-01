FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
  chromium \
  chromium-driver \
  poppler-utils \
  && rm -rf /var/lib/apt/lists/*
  
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python", "main.py"]