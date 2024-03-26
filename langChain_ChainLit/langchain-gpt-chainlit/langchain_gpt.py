import chainlit as cl
import os
from openai import OpenAI

key = os.environ['OPENAI_API_KEY']

client = OpenAI(api_key=key)

openai_model = "gpt-3.5-turbo"


@cl.on_chat_start
async def on_chat_start():
    elements = [
    cl.Image(name="image1", display="inline", path="mixtral.jpg")
    ]
    await cl.Message(content="Hello there, I am GPT. How can I help you ?", elements=elements).send()


@cl.on_message
async def handle_message(message: cl.Message):
    response = client.chat.completions.create(
        messages = [
            {"role": "system", "content": "You are a very knowledgeable historian."},
            {"role": "user", "content": message.content},
            ],
        model=openai_model,
        max_tokens=1024,  # Control response length
        n=1,
        stop=None,
        temperature=0.7
    )

    await cl.Message(content=response.choices[0].message.content).send()