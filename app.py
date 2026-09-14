from flask import Flask, jsonify
import imaplib
import email
from email.header import decode_header
import requests
import os
import threading
import time

app = Flask(__name__)

IMAP_SERVER = "imap.mail.me.com"
EMAIL_USER = os.environ["ICLOUD_EMAIL"]
EMAIL_PASS = os.environ["ICLOUD_APP_PASSWORD"]
OLLAMA_URL = "http://192.168.86.150:11434/api/generate"

cache = {"summary": "Loading...", "count": 0, "emails": []}

def get_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition"))
            if content_type == "text/plain" and "attachment" not in disposition:
                try:
                    return part.get_payload(decode=True).decode(errors="ignore")
                except Exception:
                    continue
        return ""
    else:
        try:
            return msg.get_payload(decode=True).decode(errors="ignore")
        except Exception:
            return ""

def fetch_recent_emails(limit=5):
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_USER, EMAIL_PASS)
    mail.select("inbox")
    status, messages = mail.search(None, "UNSEEN")
    email_ids = messages[0].split()[-limit:]
    results = []
    for eid in reversed(email_ids):
        status, msg_data = mail.fetch(eid, "(RFC822)")
        raw_email = None
        for part in msg_data:
            if isinstance(part, tuple):
                raw_email = part[1]
                break
        if raw_email is None:
            continue
        msg = email.message_from_bytes(raw_email)
        subject, encoding = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or "utf-8", errors="ignore")
        sender = msg.get("From", "")
        body = get_body(msg).strip()
        snippet = " ".join(body.split())[:250]
        results.append({"subject": subject, "from": sender, "snippet": snippet})
    mail.logout()
    return results

def refresh_cache():
    while True:
        try:
            emails = fetch_recent_emails()
            cache["emails"] = emails
            if not emails:
                cache["summary"] = "No new unread emails."
                cache["count"] = 0
            else:
                email_list = "\n".join(f"- From {e['from']}: {e['subject']}" for e in emails)
                prompt = f"Summarize these unread emails in 2-3 short sentences, mentioning anything urgent:\n{email_list}"
                res = requests.post(OLLAMA_URL, json={"model": "llama3.2", "prompt": prompt, "stream": False}, timeout=60)
                cache["summary"] = res.json().get("response", "Could not generate summary.")
                cache["count"] = len(emails)
        except Exception as e:
            cache["summary"] = f"Error: {e}"
        time.sleep(900)

@app.route("/summary")
def summary():
    return jsonify(cache)

if __name__ == "__main__":
    threading.Thread(target=refresh_cache, daemon=True).start()
    app.run(host="0.0.0.0", port=5051)
