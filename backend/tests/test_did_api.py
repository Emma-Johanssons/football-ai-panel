import os
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth

# Ladda miljövariabler från .env-filen
load_dotenv()

# Hämta hela nyckeln och splitta upp i användarnamn + lösenord
api_key = os.environ.get("DID_API_KEY")
if not api_key or ":" not in api_key:
    raise ValueError("DID_API_KEY är inte korrekt satt eller saknar ':'")

username, password = api_key.split(":", 1)

# JSON-data (exakt som i Postman)
data = {
    "script": {
        "type": "text",
        "input": "I love to make simple API calls"
    }
}

# Skicka POST-request
response = requests.post(
    "https://api.d-id.com/talks",
    auth=HTTPBasicAuth(username, password),
    headers={"Content-Type": "application/json"},
    json=data
)

# Skriv ut svar
print("Status code:", response.status_code)
print("Response body:", response.text)
