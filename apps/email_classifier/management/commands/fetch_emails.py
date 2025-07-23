from django.core.management.base import BaseCommand, CommandError
from email_classifier.services.email_reader import EmailClient

class Command(BaseCommand):
    help = 'Fetch emails from email server'

    def handle(self, *args, **options):
        client = EmailClient(
            imap_server="imap.hostinger.com",
            email_user="no-reply@dailo.app",
            email_password="Anaya+Ayan2022",
            folder="INBOX"
        )
        client.connect()
        emails = client.fetch_unread_emails(limit=10)
        client.close()

        for email_data in emails:
            # Send to classifier
            print(email_data["subject"], email_data["body"])
