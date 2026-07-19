import imaplib
import smtplib
from email import policy
from email.header import decode_header
from email.message import EmailMessage
from email.parser import BytesParser
from email.utils import parseaddr, parsedate_to_datetime

from django.conf import settings


def _decode_header_value(raw_value):
    if not raw_value:
        return ''

    decoded_parts = decode_header(raw_value)
    output = []
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            output.append(part.decode(encoding or 'utf-8', errors='replace'))
        else:
            output.append(part)
    return ''.join(output).strip()


def _extract_preferred_body(email_message):
    if email_message.is_multipart():
        for part in email_message.walk():
            content_type = part.get_content_type()
            disposition = (part.get('Content-Disposition') or '').lower()
            if content_type == 'text/plain' and 'attachment' not in disposition:
                payload = part.get_payload(decode=True)
                if payload is None:
                    continue
                charset = part.get_content_charset() or 'utf-8'
                return payload.decode(charset, errors='replace')

        for part in email_message.walk():
            content_type = part.get_content_type()
            disposition = (part.get('Content-Disposition') or '').lower()
            if content_type == 'text/html' and 'attachment' not in disposition:
                payload = part.get_payload(decode=True)
                if payload is None:
                    continue
                charset = part.get_content_charset() or 'utf-8'
                return payload.decode(charset, errors='replace')
        return ''

    payload = email_message.get_payload(decode=True)
    if payload is None:
        return ''
    charset = email_message.get_content_charset() or 'utf-8'
    return payload.decode(charset, errors='replace')


class GmailClient:
    def __init__(self):
        self.username = settings.EMAIL_HOST_USER
        self.password = settings.EMAIL_HOST_PASSWORD
        self.imap_host = getattr(settings, 'GMAIL_IMAP_HOST', 'imap.gmail.com')
        self.imap_port = int(getattr(settings, 'GMAIL_IMAP_PORT', 993))
        self.smtp_host = settings.EMAIL_HOST
        self.smtp_port = int(settings.EMAIL_PORT)
        self.email_timeout = int(getattr(settings, 'EMAIL_TIMEOUT', 20))

        if not self.username or not self.password:
            raise ValueError('Gmail credentials are not configured. Set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD.')

    def _imap_connect(self):
        imap_conn = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
        imap_conn.login(self.username, self.password)
        return imap_conn

    def list_inbox_messages(self, limit=30):
        with self._imap_connect() as imap_conn:
            imap_conn.select('INBOX')
            status, data = imap_conn.search(None, 'ALL')
            if status != 'OK' or not data or not data[0]:
                return []

            message_ids = data[0].split()[-limit:]
            results = []
            for uid in reversed(message_ids):
                status, fetch_data = imap_conn.fetch(uid, '(RFC822.HEADER FLAGS RFC822.SIZE)')
                if status != 'OK' or not fetch_data or not fetch_data[0]:
                    continue

                header_bytes = fetch_data[0][1]
                parsed = BytesParser(policy=policy.default).parsebytes(header_bytes)
                date_header = parsed.get('Date')
                try:
                    parsed_date = parsedate_to_datetime(date_header) if date_header else None
                except (TypeError, ValueError):
                    parsed_date = None

                envelope_data = fetch_data[0][0].decode('utf-8', errors='ignore')
                is_seen = '\\Seen' in envelope_data

                results.append({
                    'uid': uid.decode('utf-8'),
                    'subject': _decode_header_value(parsed.get('Subject', '(No subject)')),
                    'from': _decode_header_value(parsed.get('From', 'Unknown sender')),
                    'from_email': parseaddr(parsed.get('From', ''))[1],
                    'date': parsed_date,
                    'is_unread': not is_seen,
                })
            return results

    def read_message(self, uid):
        with self._imap_connect() as imap_conn:
            imap_conn.select('INBOX')
            status, fetch_data = imap_conn.fetch(uid.encode('utf-8'), '(RFC822 FLAGS)')
            if status != 'OK' or not fetch_data or not fetch_data[0]:
                raise ValueError('Unable to load the requested message.')

            raw_bytes = fetch_data[0][1]
            parsed = BytesParser(policy=policy.default).parsebytes(raw_bytes)
            envelope_data = fetch_data[0][0].decode('utf-8', errors='ignore')

            return {
                'uid': uid,
                'subject': _decode_header_value(parsed.get('Subject', '(No subject)')),
                'from': _decode_header_value(parsed.get('From', 'Unknown sender')),
                'from_email': parseaddr(parsed.get('From', ''))[1],
                'to': _decode_header_value(parsed.get('To', '')),
                'date': parsed.get('Date', ''),
                'message_id': parsed.get('Message-ID', ''),
                'body': _extract_preferred_body(parsed),
                'is_unread': '\\Seen' not in envelope_data,
            }

    def send_message(self, to_email, subject, body, in_reply_to=None, references=None):
        email_message = EmailMessage()
        email_message['From'] = settings.DEFAULT_FROM_EMAIL or self.username
        email_message['To'] = to_email
        email_message['Subject'] = subject
        if in_reply_to:
            email_message['In-Reply-To'] = in_reply_to
        if references:
            email_message['References'] = references
        email_message.set_content(body)

        with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=self.email_timeout) as smtp_conn:
            if settings.EMAIL_USE_TLS:
                smtp_conn.starttls()
            smtp_conn.login(self.username, self.password)
            smtp_conn.send_message(email_message)

    def delete_message(self, uid):
        with self._imap_connect() as imap_conn:
            imap_conn.select('INBOX')
            imap_conn.store(uid.encode('utf-8'), '+FLAGS', '\\Deleted')
            imap_conn.expunge()
