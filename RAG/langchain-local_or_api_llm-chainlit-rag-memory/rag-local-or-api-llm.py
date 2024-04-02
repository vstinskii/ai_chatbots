from typing import List
import PyPDF2
from io import BytesIO
from langchain_community.embeddings import OllamaEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.chains import (
    ConversationalRetrievalChain,
)
from langchain.docstore.document import Document
from langchain_community.llms import Ollama

from langchain_community.chat_models import ChatOllama

from langchain.memory import ChatMessageHistory, ConversationBufferMemory

from langchain_community.document_loaders import TextLoader
from langchain_openai import OpenAI
from langchain_openai import OpenAIEmbeddings

import chainlit as cl

import os

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)

key = os.environ['OPENAI_API_KEY']

@cl.on_chat_start
async def on_chat_start():
    files = None

    # Wait for the user to upload a file
    while files is None:
        files = await cl.AskFileMessage(
            content="Please upload a pdf file to begin!",
            accept=["application/pdf", "text/csv", "text/plain"],
            max_size_mb=20,
            timeout=180,
        ).send()

    file = files[0]
    print(file)

    msg = cl.Message(content=f"Processing `{file.name}`...")
    await msg.send()

    # Read the PDF file
        
    #pdf_stream = BytesIO(content)
    if type(file.path) == "application/pdf":
       pdf = PyPDF2.PdfReader(file.path)
       document = ""
       for page in pdf.pages:
           document += page.extract_text()
    else:
        loader = TextLoader(file.path)
        document = loader.load()
        #convert langchain document to string
        document = document[0].page_content
        
    print(document)
    # Split the text into chunks
    texts = text_splitter.split_text(document)

    # Create a metadata for each chunk
    metadatas = [{"source": f"{i}-pl"} for i in range(len(texts))]

    # Create a Chroma vector store
    #embeddings model switcher
    #embeddings = OllamaEmbeddings(model="mistral")
    embeddings = OpenAIEmbeddings(openai_api_type="openai")
    docsearch = await cl.make_async(Chroma.from_texts)(
        texts, embeddings, metadatas=metadatas
    )

    message_history = ChatMessageHistory()

    memory = ConversationBufferMemory(
        memory_key="chat_history",
        output_key="answer",
        chat_memory=message_history,
        return_messages=True,
    )


    #model switcher
    llm = OpenAI()
    #llm = ChatOllama(model="mistral"),

    # Create a chain that uses the Chroma vector store
    chain = ConversationalRetrievalChain.from_llm(
        llm,
        chain_type="stuff",
        retriever=docsearch.as_retriever(),
        memory=memory,
        return_source_documents=True,
    )

    # Let the user know that the system is ready
    msg.content = f"Processing `{file.name}` done. You can now ask questions!"
    await msg.update()

    cl.user_session.set("chain", chain)


@cl.on_message
async def main(message: cl.Message):
    chain = cl.user_session.get("chain")  # type: ConversationalRetrievalChain
    cb = cl.AsyncLangchainCallbackHandler()

    res = await chain.ainvoke(message.content, callbacks=[cb])
    answer = res["answer"]
    source_documents = res["source_documents"]  # type: List[Document]

    text_elements = []  # type: List[cl.Text]

    if source_documents:
        for source_idx, source_doc in enumerate(source_documents):
            source_name = f"source_{source_idx}"
            # Create the text element referenced in the message
            text_elements.append(
                cl.Text(content=source_doc.page_content, name=source_name)
            )
        source_names = [text_el.name for text_el in text_elements]

        if source_names:
            answer += f"\nSources: {', '.join(source_names)}"
        else:
            answer += "\nNo sources found"

    await cl.Message(content=answer, elements=text_elements).send()