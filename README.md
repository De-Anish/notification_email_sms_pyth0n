
A FastAPI-based notification service that supports Email, SMS, and In-App notifications.

## Features

- Email notifications using SMTP
- SMS notifications using Twilio
- In-App notifications with in-memory storage
- Retry mechanism for failed notifications
- Environment variable configuration
- CORS support

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables in `.env` file:
   ```env
   # Email Configuration
   EMAIL_SENDER=your.email@example.com
   SMTP_HOST=smtp.example.com
   SMTP_PORT=587
   SMTP_USER=your.email@example.com
   SMTP_PASSWORD=your_app_password

   # Twilio Configuration
   TWILIO_ACCOUNT_SID=your_twilio_account_sid
   TWILIO_AUTH_TOKEN=your_twilio_auth_token
   TWILIO_PHONE_NUMBER=your_twilio_phone_number
   ```

## Running the Service

```bash
uvicorn main:app --reload
```

## API Endpoints

### Send Notification

`POST /notifications`

Request body:
```json
{
    "user_id": "user123",
    "types": ["email", "sms", "in_app"],
    "title": "Test Notification",
    "message": "This is a test notification",
    "recipient_email": "user@example.com",
    "recipient_phone": "+1234567890"
}
```

### Get User Notifications

`GET /users/{user_id}/notifications`

Returns all notifications for a specific user.

## Example Usage

```python
import requests

url = "http://localhost:8000/notifications"
payload = {
    "user_id": "user123",
    "types": ["email", "sms", "in_app"],
    "title": "Test Notification",
    "message": "This is a test notification",
    "recipient_email": "user@example.com",
    "recipient_phone": "+1234567890"
}

response = requests.post(url, json=payload)
print(response.json())
```
``` Send a notification (Email + SMS + In-App)
POST http://localhost:8000/notifications
Content-Type: application/json

{
    "user_id": "test_user1",
    "types": ["email", "sms", "in_app"],
    "title": "Test Combined Notification",
    "message": "This is a test notification via Email, SMS and In-App",
    "recipient_email": "user@example.com",
    "recipient_phone": "+1234567890"
}
```
## Screenshots

### Email Notification
*Screenshot showing successful delivery of email notification with the test message*
![Notification On email](https://github.com/user-attachments/assets/863a47eb-05fe-450c-aa24-b63bfa1bb594)

### SMS Notification
*Screenshot showing successful delivery of SMS notification with the test message*
[Notification_on_mobile]<img src="https://github.com/user-attachments/assets/bc8a6615-47f1-4ea7-a292-adb66baa323f" width="300" />



## Environment Variables

| Variable | Description |
|----------|-------------|
| EMAIL_SENDER | Email address for sending emails |
| SMTP_HOST | SMTP server host (smtp.example.com) |
| SMTP_PORT | SMTP server port (587) |
| SMTP_USER | SMTP username |
| SMTP_PASSWORD | Email service password |
| TWILIO_ACCOUNT_SID | Twilio Account SID |
| TWILIO_AUTH_TOKEN | Twilio Auth Token |
| TWILIO_PHONE_NUMBER | Twilio Phone Number |

## Security Notes

1. Never commit `.env` file with real credentials
2. Use environment variables for sensitive information
3. Keep your API keys and tokens secure
4. Use app-specific passwords for email services
5. Enable 2FA for better security 
