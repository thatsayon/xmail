import imaplib
import email
from email.header import decode_header
import logging
from bs4 import BeautifulSoup
import html
import re 
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class EmailClient:
    def __init__(self, imap_server: str, email_user: str, email_password: str, folder: str = "INBOX"):
        self.server = imap_server
        self.user = email_user
        self.password = email_password
        self.folder = folder
        self.mail = None

    def connect(self):
        try:
            self.mail = imaplib.IMAP4_SSL(self.server)
            self.mail.login(self.user, self.password)
            self.mail.select(self.folder)
        except Exception as e:
            logger.exception("Failed to connect to email server")
            raise e

    def fetch_unread_emails(self, limit: int = 10) -> List[Dict]:
        try:
            status, messages = self.mail.search(None, 'UNSEEN')
            if status != "OK":
                logger.error("Failed to search emails")
                return []

            email_ids = messages[0].split()[-limit:]
            emails = []

            for e_id in email_ids:
                res, msg_data = self.mail.fetch(e_id, "(RFC822)")
                if res != "OK":
                    continue

                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        parsed_email = self.parse_email(msg)
                        if parsed_email:
                            emails.append(parsed_email)

            return emails

        except Exception as e:
            logger.exception("Error fetching unread emails")
            return []
    
    def parse_email(self, msg) -> Optional[Dict]:
        try:
            subject = self.decode_header(msg["Subject"])
            from_email = self.decode_header(msg.get("From"))
            to_email = self.decode_header(msg.get("To"))
            date = msg.get("Date")

            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))

                    if "attachment" in content_disposition:
                        continue

                    if content_type in ["text/plain", "text/html"]:
                        part_payload = part.get_payload(decode=True)
                        if part_payload:
                            decoded = part_payload.decode(errors="ignore")
                            if content_type == "text/html":
                                body = self.clean_html(decoded)
                            else:
                                body = decoded
                            break
            else:
                body = self.clean_html(msg.get_payload(decode=True).decode(errors="ignore"))

            return {
                "subject": subject,
                "from": from_email,
                "to": to_email,
                "date": date,
                "body": body.strip()
            }
        except Exception as e:
            logger.exception("Failed to parse email")
            return None
        
    def decode_header(self, value):
        if not value:
            return ""
        decoded_parts = decode_header(value)
        return ''.join(
            str(part[0], part[1] or 'utf-8') if isinstance(part[0], bytes) else str(part[0])
            for part in decoded_parts
        )

    def clean_html(self, html_text: str) -> str:
        soup = BeautifulSoup(html_text, "html.parser")
        text = soup.get_text()
        text = html.unescape(text)
        return re.sub(r'\s+', ' ', text)

    def mark_as_read(self, e_id):
        self.mail.store(e_id, '+FLAGS', '\\Seen')

    def close(self):
        if self.mail:
            self.mail.logout()