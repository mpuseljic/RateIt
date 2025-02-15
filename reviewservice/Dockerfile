FROM python:3.12-slim
WORKDIR /app

COPY . /app
# COPY .env /app/.env 
RUN pip install -r requirements.txt

EXPOSE 8003
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]

# docker build -t reviewservice:1.0 .
# docker run -p 8003:8003 reviewservice:1.0