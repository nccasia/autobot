from fastapi import FastAPI
from pydantic import BaseModel
from langchain_chroma import Chroma
from fastapi.middleware.cors import CORSMiddleware
from process import get_docs, create_chain, process_chat
from langchain_community.embeddings import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
# vectordb = Chroma(persist_directory="chroma_db", embedding_function=embeddings)
vectordb = Chroma.from_documents(get_docs(), embeddings, persist_directory="chroma_db")
chain = create_chain(vectordb)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/")
async def hello():
    return {"Hello": "World"}


class Message(BaseModel):
    text: str


@app.post("/chatbot")
async def chatbot_handler(message: Message):
    user_input = message.text
    response = process_chat(chain, user_input)

    return {"Response": response}
