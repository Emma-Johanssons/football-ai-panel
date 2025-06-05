from fastapi import FastAPI
from agents.openai_client import client

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Fotbolls AI-panel API is running"}

@app.get("/chat")
async def chat(message: str):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Du är en fotbollsexpert."},
            {"role": "user", "content": message}
        ]
    )
    answer = response.choices[0].message.content
    return {"answer": answer}
