import os
import streamlit as st
from langchain_groq import ChatGroq
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
import time
from dotenv import load_dotenv
import pickle

load_dotenv()

class SimpleDocument:
    def __init__(self, text, metadata=None):  # Add optional metadata
        self.page_content = text
        self.metadata = metadata

groq_api_key = os.environ['GROQ_API_KEY']

uploaded_file = None
uploaded_file = st.file_uploader("Upload a text file for processing:")

st.title("Chat with Docs - Groq Edition :) ")

def createLLM():

    llm = ChatGroq(
                groq_api_key=groq_api_key,
                #model_name='llama2-70b-4096'
                model_name='mixtral-8x7b-32768'
        )
    return llm

def createPrompt():
    
    prompt = ChatPromptTemplate.from_template("""
    Answer the following question based only on the provided context. 
    Think step by step before providing a detailed answer. 
    I will tip you $200 if the user finds the answer helpful. 
    <context>
    {context}
    </context>

    Question: {input}""")
    return prompt

def chain(llm,prompt):

    document_chain = create_stuff_documents_chain(llm, prompt)

    retriever = st.session_state.vector.as_retriever()
    retrieval_chain = create_retrieval_chain(retriever, document_chain)

    prompt = st.text_input("Input your prompt here")


    # If the user hits enter
    if prompt:

        # Then pass the prompt to the LLM
        start = time.process_time()
        response = retrieval_chain.invoke({"input": prompt})
        print(f"Response time: {time.process_time() - start}")

        st.write(response["answer"])

        # With a streamlit expander
        with st.expander("Document Similarity Search"):
            # Find the relevant chunks
            for i, doc in enumerate(response["context"]):
                # print(doc)
                # st.write(f"Source Document # {i+1} : {doc.metadata['source'].split('/')[-1]}")
                st.write(doc.page_content)
                st.write("--------------------------------")

#if "vector" not in st.session_state:
if uploaded_file is not None:

    st.session_state.embeddings = OllamaEmbeddings(model="mistral:7b-instruct-v0.2-fp16")

    bytes_data = uploaded_file.read()
    text_data = bytes_data.decode("utf-8")  # Assuming UTF-8 encoding
    st.session_state.uploaded_text = text_data

    st.session_state.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200) 

    st.session_state.documents = st.session_state.text_splitter.split_documents(
    [SimpleDocument(st.session_state.uploaded_text, metadata={"filename": "uploaded_file.txt"})]
    )

    st.session_state.vector = FAISS.from_documents(st.session_state.documents, st.session_state.embeddings)

    
    with open("vectors/paulgraham.com_greatwork.pkl", "wb") as f:
        pickle.dump(st.session_state.vector, f)

    llm = createLLM()

    prompt = createPrompt()

    chain(llm, prompt)
