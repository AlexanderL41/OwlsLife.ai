import os
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

messages = [
    {"role": "system", "content": "You are a helpful assistant."}
]

def chat():
    print("Groq Chatbot ready! Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ")

        if user_input.lower() == "exit":
            break

        # add user message to memory
        messages.append({"role": "user", "content": user_input})

        # send to Groq
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages
        )

        answer = response.choices[0].message.content

        # store assistant response
        messages.append({"role": "assistant", "content": answer})

        print("\nAI:", answer, "\n")


chat()