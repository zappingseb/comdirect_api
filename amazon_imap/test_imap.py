#!/usr/bin/env python3
"""Quick IMAP test to verify connection and search"""
import imaplib
import os
from dotenv import load_dotenv

load_dotenv()

host = os.getenv('IMAP_HOST')
port = int(os.getenv('IMAP_PORT', '993'))
user = os.getenv('HOSTINGER_EMAIL')
password = os.getenv('HOSTINGER_PASSWORD')

print(f"Connecting to {host}:{port} as {user}...")

try:
    mail = imaplib.IMAP4_SSL(host, port)
    mail.login(user, password)
    print("✓ Login successful")

    # List folders
    status, mailboxes = mail.list()
    print(f"\nAvailable folders:")
    for mb in mailboxes:
        print(f"  {mb}")

    # Select INBOX
    mail.select('INBOX')
    status, count = mail.status('INBOX', '(MESSAGES)')
    print(f"\n✓ INBOX has messages: {count}")

    # Search for Amazon emails
    print("\nSearching for Amazon emails...")
    status, ids = mail.search(None, 'FROM "amazon"')
    if ids and ids[0]:
        email_ids = ids[0].split()
        print(f"Found {len(email_ids)} Amazon emails")

        # Show last 3
        print("\nLast 3 Amazon emails:")
        for eid in email_ids[-3:]:
            status, msg_data = mail.fetch(eid, '(BODY[HEADER.FIELDS (SUBJECT FROM DATE)])')
            if msg_data:
                print(f"\n  Email {eid}:")
                print(f"  {msg_data[0][1].decode()}")
    else:
        print("No Amazon emails found")

    mail.logout()
    print("\n✓ Connection closed")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
