from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from .prompt import SYSTEM_PROMPT
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import os
from app.constants import data_directory, chroma_directory, last_hashes_file
from app.utils.file_utils import (
    hash_all_docs,
    load_last_hashes,
    save_last_hashes,
    process_docx_files,
)
from dotenv import load_dotenv

load_dotenv()

embeddings = HuggingFaceEmbeddings(model_name=os.getenv("EMBEDDINGS_MODEL_NAME"))
llm = ChatGoogleGenerativeAI(model=os.getenv("LLM_MODEL"))


def setup_chroma_db():
    current_hashes = hash_all_docs(data_directory)
    last_hashes = load_last_hashes(last_hashes_file)

    if not os.path.exists(chroma_directory) or set(current_hashes) != set(last_hashes):
        docs = process_docx_files(data_directory)
        vectordb = Chroma.from_documents(
            docs, embeddings, persist_directory=chroma_directory
        )
        save_last_hashes(last_hashes_file, current_hashes)

    else:
        vectordb = Chroma(
            persist_directory=chroma_directory, embedding_function=embeddings
        )
    return vectordb


def create_chain(vectordb):

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("user", "{input}"),
        ]
    )
    retriever = vectordb.as_retriever(search_kwargs={"k": 2})
    combine_docs_chain = create_stuff_documents_chain(llm, prompt)
    retrieval_chain = create_retrieval_chain(retriever, combine_docs_chain)

    return retrieval_chain


def process_chat(chain, question):
    response = chain.invoke(
        {
            "input": question,
        }
    )
    return response["answer"]
