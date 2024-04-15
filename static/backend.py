from langchain.chains import RetrievalQA
from langchain_openai import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
from static.utils import Utils
from static.logger import log_critical, log_debug, log_error, log_info
from config.cfg import gpt_model

load_dotenv()

# embeddings is the object which we set for what type of Embeddings we want, it can be from OpenAI or FAISS or Huggingface (LLAMA/Misral/Mixtral)

embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))

# db is the database we select which will be used to retrieved the embeddings from, this can also be from Chroma, Pinecone etc.

db = Chroma(persist_directory=Utils.get_db_path(), embedding_function=embeddings)

# For particular pdf using prompt

prompt_template = """Use the following pieces of context to answer the user's question. Please follow the following rules:
1. If you don't know the answer, don't try to make up an answer. Just say **I can't find the final answer**
2. If you find the answer, write the answer in a concise way
The example of your response should be:

Context: {context}

Question: {question}
Helpful answer: """

prompt = PromptTemplate(
    template=prompt_template, input_variables=["context", "question"]
)

# We define the QA chain which will be run to get the answer to the user's query.
# In this chain, we pass our db as the retriever

try:
    qa = RetrievalQA.from_chain_type(
        llm=ChatOpenAI(
            model_name=gpt_model,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
        ),
        chain_type="stuff",
        retriever=db.as_retriever(search_kwargs={"k": 6}),
        chain_type_kwargs={"prompt": prompt},
    )
except Exception as e:
    log_error("QARetrieval Chain Failed")
    log_debug(f"{str(e)}")
