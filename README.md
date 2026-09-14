\# Glance Email Widget



A small Flask service that connects to iCloud Mail via IMAP, fetches recent unread emails, and uses a local \[Ollama](https://ollama.com) instance to generate a plain-English AI summary — designed to feed into a \[Glance](https://github.com/glanceapp/glance) dashboard widget.



\## How it works



\- Runs a background thread that polls IMAP every 15 minutes

\- Extracts subject, sender, and a body snippet from each unread email

\- Sends the batch to a local LLM for summarization

\- Serves the cached result instantly via `/summary`, avoiding slow live fetches on every dashboard load



\## Environment variables



\- `ICLOUD\_EMAIL` — your iCloud email address

\- `ICLOUD\_APP\_PASSWORD` — an \[app-specific password](https://appleid.apple.com) (not your main Apple ID password)



\## Endpoint



`GET /summary` returns:

```json

{

&#x20; "count": 5,

&#x20; "summary": "AI-generated summary text",

&#x20; "emails": \[

&#x20;   { "subject": "...", "from": "...", "snippet": "..." }

&#x20; ]

}

```

