from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from prompt import SYSTEM_PROMPT
from langchain_community.document_loaders import Docx2txtLoader
from langchain_text_splitters import CharacterTextSplitter
from dotenv import load_dotenv

load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest")


def create_chain(vectorStore):

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("user", "{input}"),
        ]
    )
    retriever = vectorStore.as_retriever(search_kwargs={"k": 2})
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


def get_docs():
    loader = Docx2txtLoader("NCC.docx")
    data = loader.load()
    text_splitter = CharacterTextSplitter(chunk_size=20000, chunk_overlap=0)
    docs = text_splitter.split_documents(data)
    return docs
