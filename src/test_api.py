import requests
import json
from config import DEEPSEEK_API_KEY

def call_deepseek(prompt, code_sample):
    url = "https://api.deepseek.com/v1/chat/completions"   # check actual endpoint
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",   # or "deepseek-coder"
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": code_sample}
        ],
        "temperature": 0.3,
        "max_tokens": 2000
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        print("Error:", response.status_code, response.text)
        return None

if __name__ == "__main__":
    # Test with a tiny Python function
    test_code = "def add(a, b):\n    return a + b"
    prompt = "Generate documentation for this code in Markdown."
    doc = call_deepseek(prompt, test_code)
    print(doc)