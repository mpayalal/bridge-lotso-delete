import os
import json
import logging
from aio_pika import connect_robust, Message
from fastapi import FastAPI, HTTPException, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from dependencies.auth import get_current_user_id

app = FastAPI()

rabbitmq_user = os.getenv("RABBITMQ_USER") 
rabbitmq_pass = os.getenv("RABBITMQ_PASSWORD")
rabbitmq_host = os.getenv("RABBITMQ_HOST")
rabbitmq_port = os.getenv("RABBITMQ_PORT")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

async def connect_to_rabbit():
    try:
        connection = await connect_robust(
            host=rabbitmq_host,
            login=rabbitmq_user,
            password=rabbitmq_pass
        )
        print(connection)
        return connection
    except Exception as e:
        raise Exception(f"RabbitMQ connection error: {e}")
    
async def publish_to_rabbitmq(queue: str, message_body):
    try:
        connection = await connect_to_rabbit()
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue(queue, durable=True)
            message =  Message(body=json.dumps(message_body).encode())
            await channel.default_exchange.publish(message, routing_key=queue.name)
    except Exception as e:
        raise Exception(f"RabbitMQ publish error: {e}")

@app.post("/v1/events/documents/deleteFile")
async def delete_file_from_bucket(
    user_id: str = Depends(get_current_user_id),
    file_name: str = Form(...)
):
    try:
        # Mensaje para RabbitMQ
        message = {
            "user_id": user_id,
            "file_name": file_name
        }

        # Mandamos mensaje
        await publish_to_rabbitmq('delete_file', message)

        return {"message": f"El archivo '{file_name}' del cliente está siendo procesado para eliminación."}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/v1/events/documents/sendFile")
async def send_document_to_email(
    user_id: str = Depends(get_current_user_id),
    file_name: str = Form(...), 
    to_email: str = Form(...)
):
    try:
        # Mensaje para RabbitMQ
        message = {
            "action": "sendFile",
            "to_email": to_email,
            "user_id": user_id,
            "file_name": file_name
        }

        # Mandamos mensaje
        await publish_to_rabbitmq('notifications', message)

        return {"message": f"El archivo '{file_name}' está siendo procesado para enviarlo al correo {to_email}."}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.put("/v1/events/documents/authenticateFile")
async def authenticate_file(
    user_id: str = Depends(get_current_user_id),
    url_document: str = Form(...),
    file_name: str = Form(...),
):
    try:
        # Mensaje para RabbitMQ
        message = {
            "user_id": user_id,
            "url_document": url_document,
            "file_name": file_name,
        }

        # Mandamos mensaje
        await publish_to_rabbitmq('authenticate_file', message)

        return {"message": f"El archivo '{file_name}' del cliente está siendo procesado para autenticación."}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")