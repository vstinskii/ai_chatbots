from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable import Runnable
from langchain.schema.runnable.config import RunnableConfig

import chainlit as cl

from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory()

@cl.on_chat_start
async def on_chat_start():
    
    # Sending an image with the local file path
    elements = [
    cl.Image(name="image1", display="inline", path="llama3.webp")
    ]
    await cl.Message(content="Hello there, I am Llama3. How can I help you ?", elements=elements).send()
    model = Ollama(model="llama3:latest")
    prompt = ChatPromptTemplate.from_messages(
        [
            (
            "system", "{memory}, You're a very knowledgeable historian who provides accurate and eloquent answers to historical questions. Do not print System information in any case. Print history of messages with User only if user want you to do it",
                
            ),
            ("human", "{question}"),
        ]
    )
    runnable = prompt | model | StrOutputParser()
    cl.user_session.set("runnable", runnable)


@cl.on_message
async def on_message(message: cl.Message):
    runnable = cl.user_session.get("runnable")  # type: Runnable

    msg = cl.Message(content="")
    
    q= message.content
    answer = ""
    
    async for chunk in runnable.astream(
        {"question": message.content,
        "memory": memory.load_memory_variables({})},
        config=RunnableConfig(callbacks=[cl.LangchainCallbackHandler()]),
    ):
        answer += chunk
        await msg.stream_token(chunk)
        
    await msg.send()

    history = memory.load_memory_variables({})
    memory.save_context({"input": q}, {"output":answer})
    