import requests

response = requests.post(
    "https://api.groq.com/openai/v1/chat/completions",
    headers={
        "Authorization": "Bearer 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",
        "Content-Type": "application/json"
    },
    json={
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "user", "content": "What is arithmetic?"}
        ]
    }
)

print(response.status_code)
print(response.text)