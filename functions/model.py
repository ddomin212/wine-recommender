async def predict_hf(text):
    import requests
    import os

    API_URL = (
        "https://api-inference.huggingface.co/models/tiiuae/falcon-7b-instruct"
    )
    headers = {"Authorization": f"Bearer {os.getenv('HG_API_KEY')}"}

    def query(payload):
        response = requests.post(API_URL, headers=headers, json=payload)
        return response.json()

    prompt = f'''You are a wine consierge. A customer comes in and asks for a wine with this description, delimited by """.
                """{text}""". You are to recommend a wine that is best suited for this very brief description.
                You only include the names of the wine you recommend and nothing else.'''
    output = query({"inputs": prompt, "wait_for_model": True})
    print(output)
    return output[0]["generated_text"][len(prompt) :]
