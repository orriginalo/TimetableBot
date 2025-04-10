FROM python:3.12.7-slim

RUN apt-get update && apt-get install -y \
  poppler-utils \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
CMD ["python", "main.py"]