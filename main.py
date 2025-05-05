import os
import json
from aio_pika import connect_robust, Message
from fastapi import FastAPI, HTTPException, Form

app = FastAPI()

rabbitmq_user = os.getenv("RABBITMQ_USER") 
rabbitmq_pass = os.getenv("RABBITMQ_PASSWORD")
rabbitmq_host = os.getenv("RABBITMQ_HOST")
rabbitmq_port = os.getenv("RABBITMQ_PORT")

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
    client_id: str = Form(...),
    file_name: str = Form(...)
):
    try:
        # Mensaje para RabbitMQ
        message = f"{client_id}/{file_name}"

        # Mandamos mensaje
        await publish_to_rabbitmq('delete_file', message)

        return {"message": f"El archivo '{file_name}' del cliente {client_id} está siendo procesado para eliminación."}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/v1/events/documents/sendFile")
async def send_document_to_email(
    client_id: str = Form(...),
    file_name: str = Form(...),
    to_email: str = Form(...)
):
    try:
        # Mensaje para RabbitMQ
        message = {
            "action": "sendFile",
            "to_email": to_email,
            "file_name": f"{client_id}/{file_name}"
        }

        # Mandamos mensaje
        await publish_to_rabbitmq('notifications', message)

        return {"message": f"El archivo '{file_name}' está siendo procesado para enviarlo al correo {to_email}."}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
