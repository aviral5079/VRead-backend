import os
from langchain_community.document_loaders import (
    DirectoryLoader,
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
)
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from static.logger import log_info, log_error, log_critical, log_debug
import sys

load_dotenv()
from static.utils import Utils
from config.cfg import text_embedding_model

# We load the files from the uploads folder and use them to make the embeddings


def create_vector_database(user_id):
    try:
        pdf_loader = DirectoryLoader(
            f"uploads/{user_id}", glob="**/*.pdf", loader_cls=PyPDFLoader
        )

        markdown_loader = DirectoryLoader(
            f"uploads/{user_id}", glob="**/*.md", loader_cls=UnstructuredMarkdownLoader
        )

        text_loader = DirectoryLoader(
            f"uploads/{user_id}", glob="**/*.txt", loader_cls=TextLoader
        )

        all_loaders = [pdf_loader, markdown_loader, text_loader]
    except Exception as e:
        log_error("Error Loading Documents into Directory Loader while Ingest")
        log_debug(
            f"Module Name : {__name__},Function Name : {sys._getframe().f_code.co_name}"
        )

    loaded_documents = []
    for loader in all_loaders:
        loaded_documents.extend(loader.load())

    try:
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=40)
        chunked_documents = text_splitter.split_documents(loaded_documents)
        log_info("Document Spilt and Chunked into Doc[List]")
    except Exception as e:
        log_error("Error Splitting Documents into text chunks")
        log_debug(
            f"Module Name : {__name__},Function Name : {sys._getframe().f_code.co_name}"
        )

    embeddings = OpenAIEmbeddings(
        openai_api_key=os.getenv("OPENAI_API_KEY"), model=text_embedding_model
    )

    vector_database = Chroma.from_documents(
        documents=chunked_documents,
        embedding=embeddings,
        persist_directory=Utils.get_db_path(),
    )

    vector_database.persist()
