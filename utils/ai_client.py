import os
from dotenv import load_dotenv
import openai

load_dotenv(dotenv_path='.env')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
openai_client = openai.AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url='https://api.deepseek.com')
