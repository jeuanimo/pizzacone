import imaplib
import re
import smtplib
from email import policy
from email.header import decode_header
from email.message import EmailMessage
from email.parser import BytesParser
from email.utils import parseaddr, parsedate_to_datetime

from django.conf import settings

_SEEN_FLAG = '\\Seen'
_FOLDER_OPEN_ERROR = 'Unable to open that folder.'


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


def _parse_list_response(raw_line):
    """Parses one line of an IMAP LIST response — '(flags) "delim" name' —
    into (flags, mailbox_name). Written as plain string parsing rather than
    a regex since the flags/name sections are unbounded-length and a
    regex covering both invites needless backtracking risk for little gain.
    """
    line = raw_line.decode('utf-8', errors='replace') if isinstance(raw_line, bytes) else raw_line
    if not line.startswith('('):
        return '', ''
    close_idx = line.find(')')
    if close_idx == -1:
        return '', ''
    flags = line[1:close_idx]
    rest = line[close_idx + 1:].strip()
    _, _, name = rest.partition(' ')
    name = name.strip()
    if name.startswith('"') and name.endswith('"'):
        name = name[1:-1]
    return flags, name


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
    FOLDER_INBOX = 'inbox'
    FOLDER_SENT = 'sent'
    FOLDER_TRASH = 'trash'

    # Gmail exposes RFC 6154 SPECIAL-USE flags on LIST, which is a more
    # reliable way to find these folders than guessing at literal names —
    # "[Gmail]/Sent Mail" etc. varies by the account's language setting.
    _SPECIAL_USE_FLAGS = {
        FOLDER_SENT: '\\Sent',
        FOLDER_TRASH: '\\Trash',
    }
    # Only used as a fallback if SPECIAL-USE flags aren't present.
    _FALLBACK_NAMES = {
        FOLDER_SENT: ['[Gmail]/Sent Mail', 'Sent Mail', 'Sent Items', 'Sent'],
        FOLDER_TRASH: ['[Gmail]/Trash', 'Deleted Items', 'Trash'],
    }

    def __init__(self):
        # Defense in depth: strip whitespace (including non-breaking spaces
        # picked up from copy-pasting an app password) even though settings.py
        # already cleans these — a raw \xa0 here causes an opaque
        # UnicodeEncodeError deep inside imaplib/smtplib instead of a clear
        # login failure.
        self.username = re.sub(r'\s+', '', settings.EMAIL_HOST_USER or '')
        self.password = re.sub(r'\s+', '', settings.EMAIL_HOST_PASSWORD or '')
        self.imap_host = getattr(settings, 'GMAIL_IMAP_HOST', 'imap.gmail.com')
        self.imap_port = int(getattr(settings, 'GMAIL_IMAP_PORT', 993))
        self.smtp_host = settings.EMAIL_HOST
        self.smtp_port = int(settings.EMAIL_PORT)
        self.email_timeout = int(getattr(settings, 'EMAIL_TIMEOUT', 20))

        if not self.username or not self.password:
            raise ValueError('Gmail credentials are not configured. Set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD.')

    def _imap_connect(self):
        # A timeout is essential here — without one, a network hiccup or
        # Gmail throttling hangs the connection indefinitely, which outlasts
        # gunicorn's worker timeout and surfaces to the user as a bare 502
        # instead of a clean, catchable error.
        imap_conn = imaplib.IMAP4_SSL(self.imap_host, self.imap_port, timeout=self.email_timeout)
        imap_conn.login(self.username, self.password)
        return imap_conn

    def _find_folder_by_special_use(self, imap_conn, special_flag):
        status, list_data = imap_conn.list()
        if status != 'OK' or not list_data:
            return None
        for raw_line in list_data:
            flags, name = _parse_list_response(raw_line)
            if name and special_flag in flags:
                return name
        return None

    def _find_folder_by_fallback_name(self, imap_conn, folder):
        for candidate in self._FALLBACK_NAMES.get(folder, []):
            status, _ = imap_conn.select(candidate, readonly=True)
            if status == 'OK':
                return candidate
        return None

    def _resolve_folder(self, imap_conn, folder):
        """Maps a logical folder ('inbox'/'sent'/'trash') to the account's
        real IMAP mailbox name, or None if it can't be found.
        """
        if folder == self.FOLDER_INBOX:
            return 'INBOX'

        special_flag = self._SPECIAL_USE_FLAGS.get(folder)
        if special_flag:
            found = self._find_folder_by_special_use(imap_conn, special_flag)
            if found:
                return found

        return self._find_folder_by_fallback_name(imap_conn, folder)

    def list_messages(self, folder=FOLDER_INBOX, limit=30):
        with self._imap_connect() as imap_conn:
            mailbox_name = self._resolve_folder(imap_conn, folder)
            if not mailbox_name:
                return []
            status, _ = imap_conn.select(mailbox_name)
            if status != 'OK':
                return []
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
                is_seen = _SEEN_FLAG in envelope_data

                results.append({
                    'uid': uid.decode('utf-8'),
                    'subject': _decode_header_value(parsed.get('Subject', '(No subject)')),
                    'from': _decode_header_value(parsed.get('From', 'Unknown sender')),
                    'from_email': parseaddr(parsed.get('From', ''))[1],
                    'date': parsed_date,
                    'is_unread': not is_seen,
                })
            return results

    def read_message(self, uid, folder=FOLDER_INBOX):
        with self._imap_connect() as imap_conn:
            mailbox_name = self._resolve_folder(imap_conn, folder)
            if not mailbox_name or imap_conn.select(mailbox_name)[0] != 'OK':
                raise ValueError(_FOLDER_OPEN_ERROR)

            status, fetch_data = imap_conn.fetch(uid.encode('utf-8'), '(RFC822 FLAGS)')
            if status != 'OK' or not fetch_data or not fetch_data[0]:
                raise ValueError('Unable to load the requested message.')

            raw_bytes = fetch_data[0][1]
            parsed = BytesParser(policy=policy.default).parsebytes(raw_bytes)
            envelope_data = fetch_data[0][0].decode('utf-8', errors='ignore')

            return {
                'uid': uid,
                'folder': folder,
                'subject': _decode_header_value(parsed.get('Subject', '(No subject)')),
                'from': _decode_header_value(parsed.get('From', 'Unknown sender')),
                'from_email': parseaddr(parsed.get('From', ''))[1],
                'to': _decode_header_value(parsed.get('To', '')),
                'date': parsed.get('Date', ''),
                'message_id': parsed.get('Message-ID', ''),
                'body': _extract_preferred_body(parsed),
                'is_unread': _SEEN_FLAG not in envelope_data,
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

    def delete_message(self, uid, folder=FOLDER_INBOX):
        with self._imap_connect() as imap_conn:
            mailbox_name = self._resolve_folder(imap_conn, folder)
            if not mailbox_name or imap_conn.select(mailbox_name)[0] != 'OK':
                raise ValueError(_FOLDER_OPEN_ERROR)
            imap_conn.store(uid.encode('utf-8'), '+FLAGS', '\\Deleted')
            imap_conn.expunge()

    def mark_unread(self, uid, folder=FOLDER_INBOX):
        with self._imap_connect() as imap_conn:
            mailbox_name = self._resolve_folder(imap_conn, folder)
            if not mailbox_name or imap_conn.select(mailbox_name)[0] != 'OK':
                raise ValueError(_FOLDER_OPEN_ERROR)
            imap_conn.store(uid.encode('utf-8'), '-FLAGS', _SEEN_FLAG)
