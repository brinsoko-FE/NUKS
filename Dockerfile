FROM python:3.11-slim
COPY . .
COPY requirements.txt .
RUN pip install -r requirements.txt
WORKDIR /app
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]