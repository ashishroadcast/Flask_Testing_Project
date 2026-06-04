import time

from app import celery

@celery.task
def send_welcome_email(email):
    time.sleep(5)

    print(f"Sending email to {email}")

    return {
        "status": "success",
        "email": email
    }