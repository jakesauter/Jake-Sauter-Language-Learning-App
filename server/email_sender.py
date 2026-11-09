"""Send account emails (password-reset codes) through any SMTP server.

Settings come from a JSON file mounted read-only into the container:
    keys: host (e.g. smtp.gmail.com), port (587), username, password (a Gmail app password), from

For tests, POLYLANG_EMAIL_OUTBOX names a folder where emails are written as files instead of sent.
"""

import json
import os
import smtplib
import ssl
import time
from email.message import EmailMessage

SETTINGS_FILE = os.environ.get("POLYLANG_EMAIL_SETTINGS", "/run/secrets/email.json")
TEST_OUTBOX = os.environ.get("POLYLANG_EMAIL_OUTBOX", "")


def settings():
    try:
        with open(SETTINGS_FILE) as settings_file:
            return json.load(settings_file)
    except (OSError, ValueError):
        return None


def can_send():
    return bool(TEST_OUTBOX or settings())


def send(to_address, subject, body):
    if TEST_OUTBOX:
        os.makedirs(TEST_OUTBOX, exist_ok=True)
        with open(os.path.join(TEST_OUTBOX, f"{time.time():.6f}.json"), "w") as outbox_file:
            json.dump({"to": to_address, "subject": subject, "body": body}, outbox_file)
        return
    config = settings()
    if not config:
        raise RuntimeError("email is not set up on this server")
    message = EmailMessage()
    message["From"] = config.get("from") or config["username"]
    message["To"] = to_address
    message["Subject"] = subject
    message.set_content(body)
    port = int(config.get("port", 587))
    context = ssl.create_default_context()
    if port == 465:
        with smtplib.SMTP_SSL(config["host"], port, context=context, timeout=20) as server:
            server.login(config["username"], config["password"])
            server.send_message(message)
    else:
        with smtplib.SMTP(config["host"], port, timeout=20) as server:
            server.starttls(context=context)
            server.login(config["username"], config["password"])
            server.send_message(message)
