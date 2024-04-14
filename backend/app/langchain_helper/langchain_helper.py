from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from config import Config
import re

openai_api_key = Config.OPENAI_API_KEY

def parse_email_data(webhook_data):
    try:
        email_data = webhook_data['data']['object']
        sender_email = email_data['from'][0]['email']  
        recipient_email = email_data['to'][0]['email']  
        subject = email_data.get('subject', 'No Subject') 
        body = email_data.get('body', 'No Body')  
        grant_id = email_data['grant_id']        

        parsed_email_content = {
            "sender_email": sender_email,
            "recipient_email": recipient_email,
            "subject": subject,
            "body": body,
            "grant_id": grant_id
        }
        print(f'THIS is Parsed email content: {parsed_email_content}')
        return parsed_email_content
    except KeyError as e:
        print(f"Key error: {e} - Check the structure of the webhook data")
        return None
    except IndexError as e:
        print(f"Index error: {e} - Check the arrays for 'from' and 'to' fields")
        return None

def get_response_from_llm(webhook_data):
    parsed_email_content = parse_email_data(webhook_data)
    
    llm = ChatOpenAI(model="gpt-3.5-turbo-1106", openai_api_key=openai_api_key)
    prompt_template = PromptTemplate(
        input_variables=["parsed_email_content"],
        template="""
        Analyze the following email content to determine if a calendar event should be created:
        Email Content: \n${parsed_email_content}\n
        If a calendar event should be created, provide "yes" followed by event details such as title, start time, end time, and a brief description.
        Provide event details in the following format: [title, start_time, end_time, description]
        Be sure to give the start_time and end_time in unix time.
        If no event should be created, respond with "no".
        If you are not sure whether to create an event or about the event details, response with "no".
        So, your answer should be either: "yes, [title, start_time, end_time, description]" or "no".
        """
    )

    chain = LLMChain(llm=llm, prompt=prompt_template, output_key="answer")
    response = chain.invoke({"parsed_email_content": parsed_email_content})
    
    print (f'LLM response: {response["answer"]}')
    
    if "yes" in response["answer"].lower():
        details = parse_event_details(response["answer"], parsed_email_content["grant_id"], parsed_email_content["recipient_email"])
        
        print(f'Details from LLM response: {details}')
        
        return "yes", details
    else:
        return "no", {}


def parse_event_details(llm_response, grant_id, recipient_email):
    pattern = r"\[(.*?), (.*?), (.*?), (.*?)\]"
    match = re.search(pattern, llm_response)
    
    if match:
        details = {
            "title": match.group(1).strip(),
            "start_time": match.group(2).strip(),
            "end_time": match.group(3).strip(),
            "description": match.group(4).strip(),
            "grant_id": grant_id,
            "recipient_email": recipient_email
        }
        return details
    else:
        print("Failed to parse LLM response for event details.")
        return None