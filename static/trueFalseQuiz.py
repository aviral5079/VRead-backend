import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts.prompt import PromptTemplate
from static.RESPONSE_CODES import TF_JSON

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

template = """
Text : {text}
You are an expert quiz maker. Given the above text, it is your job to\
create a quiz of {number} true false questions.
Make sure that questions are not repeated and check all questions to be conforming to the text as well.
Make sure to format your response like the TF_JSON below and use it as a guide.
Ensure to make the {number} questions.
{response_json}
"""

quiz_generation_prompt = PromptTemplate(
    input_variables=["text", "number", "tf_json"], template=template
)

quiz_chain = LLMChain(llm=llm, prompt=quiz_generation_prompt, verbose=True)
