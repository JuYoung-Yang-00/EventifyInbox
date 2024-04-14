from langchain_openai import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
# from langchain_openai import OpenAIEmbeddings
from config import Config

openai_api_key = Config.OPENAI_API_KEY

def get_response_from_llm(email_content):
    
    llm = OpenAI(model="gpt-3.5-turbo-instruct")
    
    prompt = PromptTemplate(
        input_variables=["email_content"],
        template="""
            You are a helpful email/calendar agent that can decide whether a new calendar event should be created based on an email.
            Based on the json object of the email provided below, determine whether a new calendar event should be created.
            Only use the context and content in the email to make your decision.
            If you think the event should be created, say "yes". If you think the event should not be created, say "no".
            If you are not sure about the answer, say "no".
            If you think the event should be created, you must provide the "grant_id", "title", "start_time", "end_time", and "location", "description", "attendees" of the event if you know them.
            The following is a json object of the email with the necessary information included: "${email_content}"
        """,
    )
    chain = LLMChain(llm=llm, prompt=prompt, output_key="answer")
        
    response = chain.invoke({"email_content": email_content}) 
    
    print (response["answer"])
    return response["answer"]