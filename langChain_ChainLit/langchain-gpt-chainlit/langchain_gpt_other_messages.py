import chainlit as cl
import os
from openai import OpenAI

key = os.environ['OPENAI_API_KEY']

client = OpenAI(api_key=key)

openai_model = "gpt-4-turbo-preview"


@cl.on_chat_start
async def on_chat_start():
    elements = [
    cl.Image(name="image1", display="inline", path="ChatGPT-Logo.png")
    ]
    await cl.Message(content="Hello there, I am GPT4. How can I help you ?", elements=elements).send()


@cl.on_message
async def handle_message(message: cl.Message):
    response = client.chat.completions.create(
       messages = [
           OpenAI.ChatCompletionMessageParam(role="system", content="You are a helpful and friendly AI assistant."),
           OpenAI.ChatCompletionMessageParam(role="user", content="What is the weather like in Paris today?")
            ],
        model=openai_model,
        max_tokens=1024,  # Control response length
        n=1,
        stop=None,
        temperature=0.7
    )

    await cl.Message(content=response.choices[0].message.content).send()