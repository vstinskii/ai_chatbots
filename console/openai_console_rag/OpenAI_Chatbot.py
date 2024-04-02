import os
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma

from langchain.chains.question_answering import load_qa_chain
from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory

with open('text/how_to_do_great_work.txt', encoding='utf-8') as f:
    mytext = f.read()
print("prepearing how_to_do_great_work.txt file")

key = os.environ['OPENAI_API_KEY']

text_splitter = RecursiveCharacterTextSplitter(chunk_size=256, chunk_overlap=100)
texts = text_splitter.split_text(mytext)

embeddings = OpenAIEmbeddings()

docsearch = Chroma.from_texts(
    texts,
    embeddings,
    metadatas=[{"source": i} for i in range(len(texts))])
print("how_to_do_great_work.txt file is ready to work!")

template = """You are a chatbot having a conversation with a human.

Given the following extracted parts of a long document
and a question, create a final answer.

Directly cite the text and do not rephrase any wording.

Please do not include any text aside from the citation.
{context}

{chat_history}
Human: {human_input}
Chatbot:"""

prompt = PromptTemplate(
    input_variables=["chat_history", "human_input", "context"],
    template=template
)

memory = ConversationBufferMemory(memory_key="chat_history", input_key="human_input")
chain = load_qa_chain(
    OpenAI(temperature=0),
    chain_type="stuff",
    memory=memory,
    prompt=prompt
)

query = ""
print("AI: Hi! How can I help you?")
while True:
    query = input("User: ")
    if query=="exit":
        exit()

    docs = docsearch.similarity_search(query)
    answer = chain.invoke({"input_documents": docs, "human_input": query}, return_only_outputs=True)["output_text"]
    print("AI: " + answer)
    memory.save_context({"human_input": query}, {"chat_history":answer})
