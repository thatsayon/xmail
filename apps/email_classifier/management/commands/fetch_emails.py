from django.core.management.base import BaseCommand, CommandError
from email_classifier.services.email_reader import EmailClient
from email_classifier.ml.classifier import classify_email
from email_classifier.services.email_forward import forward_email
from email.utils import parseaddr
import environ

env = environ.Env()

class Command(BaseCommand):
    help = 'Fetch emails from email server'

    def handle(self, *args, **options):

        client = EmailClient(
            imap_server=env('SMTP_SERVER'),
            email_user=env('SMTP_USER'),
            email_password=env('SMTP_PASS'),
            folder="INBOX"
        )
        client.connect()
        emails = client.fetch_unread_emails(limit=10)
        client.close()

        for email_data in emails:
            print(email_data)
            # Send to classifier
            email_data["department"] = classify_email(email_data["body"])
            # Print to console
            print(email_data["department"])
            forward_email(
                original_from=parseaddr(email_data["from"])[1],
                original_subject=email_data["subject"],
                original_body=email_data["body"],
                department=email_data["department"]
            )
            print(email_data["subject"], email_data["body"])
