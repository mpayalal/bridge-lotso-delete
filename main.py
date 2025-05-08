import os
import json
import logging
from models.User import User
from db.db import engine, Base
from aio_pika import connect_robust, Message
from fastapi import FastAPI, HTTPException, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from dependencies.auth import get_current_user

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

@app.on_event("startup")
async def startup_db_client():
    try:
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    # Close any open connections or perform cleanup
    logger.info("Shutting down application")

@app.post("/v1/events/documents/deleteFile")
async def delete_file_from_bucket(
    user: User = Depends(get_current_user),
    file_name: str = Form(...)
):
    try:
        # Mensaje para RabbitMQ
        message = {
            "client_email": user.email,
            "file_name": f"{user.documentNumber}/{file_name}"
        }

        # Mandamos mensaje
        await publish_to_rabbitmq('delete_file', message)

        return {"message": f"El archivo '{file_name}' del cliente {user.documentNumber} está siendo procesado para eliminación."}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/v1/events/documents/sendFile")
async def send_document_to_email(
    user: User = Depends(get_current_user),
    file_name: str = Form(...), 
    to_email: str = Form(...)
):
    try:
        # Mensaje para RabbitMQ
        message = {
            "action": "sendFile",
            "to_email": to_email,
            "client_name": user.name,
            "file_name": f"{user.documentNumber}/{file_name}"
        }

        # Mandamos mensaje
        await publish_to_rabbitmq('notifications', message)

        return {"message": f"El archivo '{file_name}' está siendo procesado para enviarlo al correo {to_email}."}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.put("/v1/events/documents/authenticateFile")
async def authenticate_file(
    user: User = Depends(get_current_user),
    url_document: str = Form(...),
    file_name: str = Form(...),
):
    try:
        # Mensaje para RabbitMQ
        message = {
            "client_id": user.documentNumber,
            "url_document": url_document,
            "file_name": file_name,
            "client_email": user.email
        }

        # Mandamos mensaje
        await publish_to_rabbitmq('authenticate_file', message)

        return {"message": f"El archivo '{file_name}' del cliente {user.documentNumber} está siendo procesado para autenticación."}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")