FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
  poppler-utils \
  && rm -rf /var/lib/apt/lists/*
  
COPY . /app
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "main.py"]