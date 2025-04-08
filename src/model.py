import os
from dotenv import load_dotenv
import google.generativeai as genai
from openai import OpenAI 
from groq import Groq
import time
import tiktoken
from src.video_info import GetVideo

class Model:
    def __init__(self):
        load_dotenv()

    @staticmethod
    def google_gemini(transcript, prompt, extra=""):
        load_dotenv()
        genai.configure(api_key=os.getenv("GOOGLE_GEMINI_API_KEY"))
        model = genai.GenerativeModel("gemini-pro")
        try:
            response = model.generate_content(prompt + extra + transcript)
            return response.text
        except Exception as e:
            response_error = "⚠️ There is a problem with the API key or with python module."
            return response_error,e
    
    
    @staticmethod
    def openai_chatgpt(transcript, prompt, extra=""):
        load_dotenv()
        client =   OpenAI(api_key=os.getenv("OPENAI_CHATGPT_API_KEY"))
        model="gpt-3.5-turbo"
        message = [{"role": "system", "content": prompt + extra + transcript}]
        try:
            response = client.chat.completions.create(model=model, messages=message)
            return response.text
        except Exception as e:
            response_error = "⚠️ There is a problem with the API key or with python module."
            return response_error,e

    
    @staticmethod
    def groq(transcript, prompt, extra=""):
        load_dotenv()
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        client.last_request_time = 0
        client.tokens_used = 0

        try:
            current_time = time.time()
            if current_time - client.last_request_time < 60 / 6000:  # Check if the time since the last request is less than 1 minute
                time.sleep(60 / 6000 - (current_time - client.last_request_time))  # Wait for the remaining time to be used

            # Limit the number of tokens used in each request
            max_tokens = 6000
            while True:
                response = client.chat.completions.create(
                    messages=[{"role": "system", "content": prompt + extra + transcript[:max_tokens]}],
                    model="llama-3.3-70b-versatile",
                )

                client.tokens_used += len(response.choices[0].message.content)  # Update tokens used
                client.last_request_time = time.time()

                if client.tokens_used < max_tokens:
                    break

                # If the request exceeds the TPM limit, wait for the remaining tokens to be used
                time.sleep((max_tokens - client.tokens_used) / 60)

            return response.choices[0].message.content
        except Exception as e:
            response_error = "⚠️ There is a problem with the API key or with python module."
            return response_error, e
        
    @staticmethod
    def groq_chunked(transcript, prompt,extra):
        load_dotenv()
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        model_name ="llama3-70b-8192"
        MAX_CONTENT_TOKENS = 6000  
        TPM_LIMIT = 1000000
        try:
            full_response = []
            tokens_used = 0
            window_start = time.time()

            chunks = Model.chunk_transcript(
                text=transcript,
                model_name=model_name,
                max_tokens=MAX_CONTENT_TOKENS)
            
            for chunk in chunks:
                elapsed = time.time() - window_start
                if elapsed > 60:
                    tokens_used = 0 
                    window_start = time.time()

                if tokens_used >= TPM_LIMIT * 0.95:
                    sleep_time = 60 - (elapsed % 60)
                    time.sleep(max(sleep_time,0))
                    tokens_used = 0 
                    window_start = time.time()

                # ✅ Include response formatting example
                formatted_prompt = f"""
                    {prompt}
                    EXAMPLE RESPONSE:
                    1. [00:00:00](URL?t=0) Introduction
                    2. [00:05:00](URL?t=300) First Topic
                    
                    ACTUAL TRANSCRIPT:
                    {chunk}
                """

                response = client.chat.completions.create(
                    messages=[{
                        "role":"system",
                        "content":formatted_prompt + extra
                    }],
                    model=model_name,
                    temperature=0.3,
                    max_tokens=1024
                )
                if response.choices[0].message.content:
                    full_response.append(response.choices[0].message.content)
                tokens_used += response.usage.total_tokens

                time.sleep(0.2)

            return "\n".join(full_response) if full_response else "No response generated"
            
        except Exception as e:
            return f"⚠️ Error: {str(e)}", e
        
    @staticmethod
    def chunk_transcript(text, model_name,max_tokens):
        encoder = tiktoken.encoding_for_model(model_name)
        tokens = encoder.encode(text)

        return [encoder.decode(chunk) for chunk in [tokens[i:i+max_tokens]
                    for i in range(0,len(tokens),max_tokens)]]
    

if __name__ == "__main__":
    load_dotenv()
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    print(Groq().models.list())  # Check available models
    test_text = "Sample transcript content"
    print(len(Model.chunk_transcript(test_text, "llama3-70b-8192", 100)))
