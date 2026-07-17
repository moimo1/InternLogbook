FROM python:3.11-slim

RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# FIXED: Explicitly forcing the openpyxl installation layer here
RUN pip install --no-cache-dir openpyxl

COPY . .

CMD ["python", "app.py"]