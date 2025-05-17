from fastapi import FastAPI,HTTPException,Response,Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse,Response
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from typing import List,Dict,Optional,Any
from enum import Enum
import asyncio
from datetime import datetime
import uuid
import emails
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client
import os
from dotenv import load_dotenv
load_dotenv('example.env')
print("Environment Variables:")
print(f"EMAIL_SENDER: {os.getenv('EMAIL_SENDER')}")
print(f"SMTP_HOST: {os.getenv('SMTP_HOST')}")
print(f"SMTP_PORT: {os.getenv('SMTP_PORT')}")
print(f"SMTP_USER: {os.getenv('SMTP_USER')}")
print(f"TWILIO_ACCOUNT_SID: {os.getenv('TWILIO_ACCOUNT_SID')}")
print(f"TWILIO_PHONE_NUMBER: {os.getenv('TWILIO_PHONE_NUMBER')}")
app = FastAPI(title="Notification Service")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.middleware("http")
async def add_response_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Content-Type"] ="application/json"
    return response
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
twilio_client = Client(TWILIO_ACCOUNT_SID,TWILIO_AUTH_TOKEN)

notifications_store: Dict[str, List[Dict]] = {}
notification_queue: List[Dict] = []

class NotificationType(str,Enum):
    EMAIL ="email"
    SMS ="sms"
    IN_APP ="in_app"

class NotificationCreate(BaseModel):
    user_id: str
    types: List[NotificationType]
    title: str
    message: str
    recipient_email: Optional[str] = None
    recipient_phone: Optional[str] = None

class Notification(BaseModel):
    id: str
    user_id: str
    type: NotificationType
    title: str
    message: str
    status: str
    created_at: str
    recipient_email: Optional[str] = None
    recipient_phone: Optional[str] = None

def send_email(to_email: str,subject: str,message: str) -> bool:
    try:
        print(f"Attempting to send email to {to_email}")
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))

        with smtplib.SMTP(SMTP_HOST,SMTP_PORT) as server:
            print("Connecting to SMTP server...")
            server.starttls()
            print(f"Logging in with user: {SMTP_USER}")
            server.login(SMTP_USER, SMTP_PASSWORD)
            print(f"Sending email to: {to_email}")
            server.send_message(msg)
            print("Email sent successfully!")
            return True

    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

def send_sms(to_phone: str, message: str) -> bool:
    try:
        print(f"Attempting to send SMS to {to_phone}")
        message = twilio_client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=to_phone
        )
        print(f"SMS sent successfully! SID: {message.sid}")
        return True
    except Exception as e:
        print(f"Error sending SMS: {str(e)}")
        return False

def process_email_notification(notification: dict):
    if not notification.get('recipient_email'):
        print("No recipient email provided")
        return False
        
    print(f"Processing email notification to: {notification['recipient_email']}")
    success = send_email(
        to_email=notification['recipient_email'],
        subject=notification['title'],
        message=notification['message']
    )
    print(f"Email processing result: {'success' if success else 'failed'}")
    return success
    
def process_sms_notification(notification: dict):
    if not notification.get('recipient_phone'):
        print("No recipient phone number provided")
        return False

    print(f"Processing SMS notification to: {notification['recipient_phone']}")
    success = send_sms(
        to_phone=notification['recipient_phone'],
        message=f"{notification['title']}\n{notification['message']}"
    )
    print(f"SMS processing result: {'success' if success else 'failed'}")
    return success

def process_in_app_notification(notification: dict):
    user_id = notification['user_id']
    if user_id not in notifications_store:
        notifications_store[user_id] = []
    notifications_store[user_id].append(notification)
    return True

async def process_notification(notification: dict,max_retries: int = 3):
    processors = {
        'email': process_email_notification,
        'sms': process_sms_notification,
        'in_app': process_in_app_notification
    }
    
    processor =processors.get(notification['type'])
    if not processor:
        return False

    retries = 0
    while retries < max_retries:
        try:
            print(f"Processing notification attempt {retries + 1}/{max_retries}")
            success = processor(notification)
            if success:
                notification['status'] = 'delivered'
                return True
            print(f"Processing failed, will retry in {2 ** retries} seconds")
        except Exception as e:
            print(f"Error processing notification: {e}")
        await asyncio.sleep(2 ** retries)
        retries += 1
    
    notification['status'] ='failed'
    return False

@app.post("/notifications")
async def send_notification(notification: NotificationCreate):
    try:
        results = []
        
        for notification_type in notification.types:
            notification_dict ={
                "id": str(uuid.uuid4()),
                "user_id":notification.user_id,
                "type": str(notification_type.value) if isinstance(notification_type,NotificationType) else str(notification_type),
                "title" :str(notification.title),
                "message": str(notification.message),
                "status": "pending",
                "created_at": datetime.utcnow().isoformat(),
                "recipient_email": str(notification.recipient_email) if notification.recipient_email else None,
                "recipient_phone": str(notification.recipient_phone) if notification.recipient_phone else None
            }

            if notification_type ==NotificationType.EMAIL and not notification.recipient_email:
                return {"ok": False, "error":"Email address is required for email notifications"}

            if notification_type == NotificationType.SMS and not notification.recipient_phone:
                return {"ok": False, "error":"Phone number is required for SMS notifications"}

            success =await process_notification(notification_dict)
            
            if success:
                if notification.user_id not in notifications_store:
                    notifications_store[notification.user_id] = []
                notifications_store[notification.user_id].append(notification_dict)
                results.append(notification_dict)
            else:
                results.append({
                    "type": notification_type,
                    "status": "failed",
                    "error": f"Failed to process {notification_type} notification"
                })

        return {
            "ok": True,
            "data": results
        }

    except Exception as e:
        print(f"Error in send_notification:{str(e)}")
        return {"ok": False, "error":str(e)}

@app.get("/users/{user_id}/notifications")
async def get_user_notifications(user_id: str):
    try:
        notifications =notifications_store.get(user_id, [])
        return {
            "ok": True,
            "data": notifications
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}

async def process_queue():
    while True:
        try:
            if notification_queue:
                notification =notification_queue.pop(0)
                await process_notification(notification)
            await asyncio.sleep(1)
        except Exception as e:
            print(f"Error processing queue: {e}")
            await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(process_queue()) 
