FROM python:3.12-slim
WORKDIR /app

COPY . /app
# COPY .env /app/.env 
RUN pip install -r requirements.txt

EXPOSE 8001
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]

# docker build -t authservice:1.0 .
# docker run -p 8001:8001 authservice:1.0