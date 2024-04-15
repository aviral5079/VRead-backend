import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts.prompt import PromptTemplate
from static.RESPONSE_CODES import MCQ_JSON


llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

template = """

Text : {text}
You are an expert MCQ maker. Given the above text, it is your job to\
create a quiz of {number} multiple choice questions.
Make sure that questions are not repeated and check all questions to be conforming to the text as well.
Make sure to format your reponse like the RESPONSE_JSON below and use it as a guide.\
Ensure to make the {number} MCQs.
{response_json}
"""

quiz_generation_prompt = PromptTemplate(
    input_variables=["text", "number", "response_json"], template=template
)

quiz_chain = LLMChain(llm=llm, prompt=quiz_generation_prompt, verbose=True)
