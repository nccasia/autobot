from langchain_community.document_loaders import Docx2txtLoader
from langchain_text_splitters import CharacterTextSplitter
import os
import hashlib
import pickle
from docx import Document


def process_docx_files(directory):
    contents = []
    filenames = [f for f in os.listdir(directory) if f.endswith(".docx")]
    filenames.sort()
    for filename in filenames:
        loader = Docx2txtLoader(os.path.join(directory, filename))
        text_splitter = CharacterTextSplitter(chunk_size=20000, chunk_overlap=0)
        docs = text_splitter.split_documents(loader.load())
        contents.extend(docs)
    return contents


def hash_docx_content(file_path):
    doc = Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    content = "\n".join(full_text)
    hasher = hashlib.sha256()
    hasher.update(content.encode("utf-8"))
    return hasher.hexdigest()


def hash_all_docs(directory):
    hashes = []
    filenames = [f for f in os.listdir(directory) if f.endswith(".docx")]
    filenames.sort()
    for filename in filenames:
        file_hash = hash_docx_content(os.path.join(directory, filename))
        hashes.append(file_hash)
    return hashes


def load_last_hashes(pickle_file):
    if os.path.exists(pickle_file):
        with open(pickle_file, "rb") as f:
            return pickle.load(f)
    return {}


def save_last_hashes(pickle_file, hashes):
    with open(pickle_file, "wb") as f:
        pickle.dump(hashes, f)
