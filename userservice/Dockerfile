FROM python:3.12-slim
WORKDIR /app

COPY . /app
COPY .env /app/.env 
RUN pip install -r requirements.txt

EXPOSE 8002
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]

# docker build -t userservice:1.0 .
# docker run -p 8002:8002 userservice:1.0