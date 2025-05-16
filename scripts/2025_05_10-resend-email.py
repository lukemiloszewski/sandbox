import resend

resend.api_key = ...

params: resend.Emails.SendParams = {
    "from": "MEMEX LTD <hello@memex.sh>",
    "to": ["lukemiloszewski@gmail.com"],
    "subject": "Testing 123",
    "html": "<p>It works!</p>"
}

email = resend.Emails.send(params)
print(email)
