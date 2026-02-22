import imaplib
import email
import email.header
import re
import os
from typing import Optional


def extract_order_number(transaction_string: str) -> Optional[str]:
    """
    Extract the Amazon order number from a transaction string.
    Input:  "AMAZON PAYMENTS 306-6340477-5787538"
    Output: "306-6340477-5787538"

    Amazon order numbers follow the pattern: digits-digits-digits (3-7-7).
    """
    pattern = r'\b(\d{3}-\d{7}-\d{7})\b'
    match = re.search(pattern, transaction_string)
    if match:
        return match.group(1)
    return None


def search_amazon_email(order_number: str) -> Optional[str]:
    """
    Connect to IMAP mailbox and search for the Amazon order confirmation
    email matching the given order number.

    Searches in email body (not just subject) since order number appears in text.
    Returns the plain text or HTML body of the email, or None if not found.
    """
    host = os.getenv('IMAP_HOST', 'imap.hostinger.com')
    port = int(os.getenv('IMAP_PORT', '993'))
    user = os.getenv('HOSTINGER_EMAIL')
    password = os.getenv('HOSTINGER_PASSWORD')

    try:
        mail = imaplib.IMAP4_SSL(host, port)
        mail.login(user, password)
        mail.select('INBOX')

        # Server-side search: BODY contains order number (searches in email text)
        # This finds emails where the order number appears in the body
        search_criteria = f'BODY "{order_number}"'
        status, message_ids = mail.search(None, search_criteria)

        if status != 'OK' or not message_ids[0]:
            # Fallback: search by subject if body search fails
            search_criteria = f'SUBJECT "{order_number}"'
            status, message_ids = mail.search(None, search_criteria)

            if status != 'OK' or not message_ids[0]:
                mail.logout()
                return None

        # Take the last (most recent) match
        ids = message_ids[0].split()
        latest_id = ids[-1]

        # Fetch the full RFC822 message
        status, msg_data = mail.fetch(latest_id, '(RFC822)')
        mail.logout()

        if status != 'OK':
            return None

        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        # Extract body - prefer plain text, fall back to HTML
        body = _extract_body(msg)
        return body

    except Exception as e:
        raise RuntimeError(f"IMAP search failed: {e}") from e


def _extract_body(msg: email.message.Message) -> Optional[str]:
    """
    Walk a multipart email and extract the most useful body part.
    Priority: text/plain > text/html
    """
    text_plain = None
    text_html = None

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get('Content-Disposition', ''))

            # Skip attachments
            if 'attachment' in disposition:
                continue

            if content_type == 'text/plain' and text_plain is None:
                payload = part.get_payload(decode=True)
                if payload:
                    text_plain = payload.decode(
                        part.get_content_charset() or 'utf-8',
                        errors='replace'
                    )
            elif content_type == 'text/html' and text_html is None:
                payload = part.get_payload(decode=True)
                if payload:
                    text_html = payload.decode(
                        part.get_content_charset() or 'utf-8',
                        errors='replace'
                    )
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            text_plain = payload.decode(
                msg.get_content_charset() or 'utf-8',
                errors='replace'
            )

    # Return best available representation
    if text_plain:
        # Truncate to 4000 chars to stay within Claude's practical context
        return text_plain[:4000]
    if text_html:
        # Strip HTML tags to reduce token noise
        clean = re.sub(r'<[^>]+>', ' ', text_html)
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean[:4000]
    return None
