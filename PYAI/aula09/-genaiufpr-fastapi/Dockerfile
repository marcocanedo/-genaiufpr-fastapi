FROM python:3.13-slim

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY clima_api.py /app/clima_api.py

EXPOSE 8000

CMD ["uvicorn", "clima_api:app", "--host", "0.0.0.0", "--port", "8000"]
