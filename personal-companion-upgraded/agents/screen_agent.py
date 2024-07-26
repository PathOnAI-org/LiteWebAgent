import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from openai import OpenAI

import os, shutil
from playwright.async_api import Page

from dotenv import load_dotenv

import random
import string
import re

load_dotenv()

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))


def clear_directory(directory_path):
    if not os.path.exists(directory_path):
        return

    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            pass

class ScreenAgent:
    def __init__(self, host_page: Page, path: str = 'cache'):
        self.config =  {
            "temperature": 0.0,
            # "top_p": 0.95,
            # "top_k": 64,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }

        self.model = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

        self.function_root = f'{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/cache/'
        self.webpage_path = f'{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/cache/{path}.txt'

        clear_directory(f'{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/cache')

        self.current_url: str = ''
        self.page = host_page

    def set_url(self, p: str):
        self.current_url = p
        return self
    
    async def read_page(self, navigate=False):
        if navigate:
            await self.page.goto(self.current_url, wait_until='domcontentloaded')
            self.current_url = self.page.url

        self.current_url = self.page.url

        main_content = await self.page.content()

        with open(self.webpage_path, 'w+', encoding="utf-8") as f:
            f.write(main_content)

        return self
    
    def _remove_code_markers(self, text: str):
        if text.startswith("```python\n"):
            text = text[10:]
        if text.endswith("\n```"):
            text = text[:-4]
        return text
    
    
    async def build_action(self, action: str, code_path: str | None = None):
        with open(self.webpage_path, 'a+', encoding='utf-8') as f:
            f.seek(0)
            webpage_content = f.read()

        if code_path:
            with open(code_path, 'r') as file:
                code = file.read()
        
        uploaded_file = genai.upload_file(path=f'{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/cache/snapshot.png', display_name='__')

        template = f"""
            HTML Code: {webpage_content}
            Page Snapshot: {uploaded_file}

            Using the HTML and Page Snapshot {_inject_2} above for {self.current_url}, write a python playwright code function that takes a SINGLE argument of a playwright Page object and {action}. 
            Output ONLY the function with proper indents, nothing else. Do NOT use type annotations. Make sure that the playwright code is as specific and accurate as possible.

           ALSO, wait_for_navigation IS NOT A VALID PLAYWRIGHT FUNCTION

           Avoid using global page functions directly, instead using query_selector_all and then executing functions upon that \
           so for example instead of doing

           await page.click(".test:nth-child(1)")

           you would do

           elements = await page.locator("test").all()
           await elements[0].click()

           Avoid using css selectors like >, instead just target elements specifically using id or class or names or etc

           Remember to target <input> elements when trying to enter text! Remember to read the HTML itself and focus on it. Remember, you don't need to click on
           input elements to fill them, you can directly fill(). Be sure to use the HTML itself to generate the code, so that the generated playwright python code will work.

           Don't use networkidle as a load state to wait for, instead use domcontentloaded. No going to other tabs.

            An example output (for formatting, etc) is 
            ```python\nasync def search_test(page):\n    await page.fill(\"#APjFqb\", \"cows\")\n    await page.click(\"input[name='btnK']\")\n```
        """

        response = self.model.generate_content(template)
        response = response.text
        response = self._remove_code_markers(response)

        function_path = generate_random_string()

        with open(f'{self.function_root}{function_path}.py', 'w+') as f:
            print(response)
            f.write(response)

        return function_path
    
