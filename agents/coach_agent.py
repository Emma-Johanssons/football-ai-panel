from openai_client import client

def get_coach_response(message: str):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Du är en coach."},
            {"role": "user", "content": message}
        ]
    )
    return response.choices[0].message.content
