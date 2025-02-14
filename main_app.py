# /// script
# requires-python = ">=3.8"  # Updated to a valid version
# dependencies = [
#    "fastapi",
#    "uvicorn",
#    "requests"
# ]
# ///

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import os 
import json
import subprocess
from subprocess import run
import urllib.request

app = FastAPI()

response_format = {
    "type": "json_schema",
    "json_schema": {
        "name": "task_runner",
        "schema": {
            "type": "object",
            "properties": {
                "python_code": {
                    "type": "string",
                    "description": "Python code to perform the task"
                },
                "python_dependencies": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "module": {
                                "type": "string",
                                "description": "Name of the python module"
                            }
                        },
                        "required": ["module"],
                        "additionalProperties": False
                    }
                }
            },
            "required": ["python_code", "python_dependencies"],
            "additionalProperties": False
        }
    }
}


response_format_script = {
    "type": "json_schema",
    "json_schema": {
        "name": "script_runner",
        "schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The url provided to run the python script"
                },
                "email": {
                    "type": "string",
                    "description": "The email id provided. It should have an @ symbol. Example abc@abc.com. If it is not present you can return user@example.com"
                }
            },
            "required": ["url", "email"],
            "additionalProperties": False
        }
    }
}

primary_prompt = """
You are an agent that writes Python code.
Assume uv and python is preinstalled.
Assume that the code you generate will be executed inside a docker container.
Inorder to perform any task if some python package is required to install, provide name of those modules.
If it is a task to extract information from dates, consider different date formats like 2005/09/12 07:16:01, 2000-02-19, Jul 07, 2023, 16-Jan-2007 and so on.
"""
script_prompt = """
You are an agent that identifies the url provided and the email provided to run a script.
"""

app.add_middleware (
    CORSMiddleware,
    allow_origins = ['*'],
    allow_credentials = True,
    allow_methods = ['GET', 'POST'],
    allow_headers = ['*']
)
AIPROXY_TOKEN=os.getenv("AIPROXY_TOKEN")

AIPROXY_TOKEN = 'eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIzZHMzMDAwMTg1QGRzLnN0dWR5LmlpdG0uYWMuaW4ifQ.zjOoLtUcmCP0HZ62lm1c_xf8mCb3uBff9SxAXXRxdcU'

url = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"

headers = {
        "Content-type":"application/json",
        "Authorization": f"Bearer {AIPROXY_TOKEN}"
    }

@app.get ("/")
def home():
    return {"We have just started our project"}

def task_runner (task: str):
    url = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"

    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role":"user",
                "content": task
            },
            {
                "role": "system",
                "content":f"""{primary_prompt}"""
            }
        ],
        "response_format": response_format
               
    }
    response = requests.post(url=url,headers = headers, json= data)
    r=response.json()
    code = json.loads(r['choices'][0]['message']['content'])['python_code']
    dependency = json.loads(r['choices'][0]['message']['content'])['python_dependencies']
    # if dependency == '':

    # uv_script = f"""
# /// script
# requires-python = ">=3.8"  # Updated to a valid version
# dependencies = 
#    {dependency}
# 
# ///
    # """
    with open("llm_code.py","w") as f:
        f.write(code)

    output= run(["uv","run","llm_code.py"],capture_output=True,text=True,cwd=os.getcwd())
    return(f"successfully written the code in the file. The output after executing the script is {output}")

@app.get("/try")
def install_script(in_url: str, in_email: str):
    return (f"The url is {in_url} and the email is {in_email}")
    """
    Endpoint to download and run a script.
    Args:
        in_url (str): URL of the script to download.
        in_email (str): User email.
    Returns:
        dict: Result of the operation.
    """
    # Ensure `USER_EMAIL` is set
    user_email = in_email
    if not user_email:
        return {"error": "USER_EMAIL is not provided."}

    # Download the `datagen.py` script
    script_url = in_url
    script_name = "datagen.py"
    try:
        urllib.request.urlretrieve(script_url, script_name)
    except Exception as e:
        return {"error": f"Failed to download the script: {e}"}

    # Run the script with the provided email
    try:
        result = subprocess.run(
            ["uv", "run", script_name, user_email], 
            check=True, 
            capture_output=True, 
            text=True
        )
        return {"message": "Script executed successfully.", "output": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"error": f"Error executing {script_name}: {e}", "output": e.stderr}

@app.post ("/run")
def script_runner (task: str):
    url = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"

    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role":"user",
                "content": task
            },
            {
                "role": "system",
                "content":f"""{script_prompt}"""
            }
        ],
        "response_format": response_format_script
               
    }
    response = requests.post(url=url,headers = headers, json= data)
    r=response.json()
    input_url = json.loads(r['choices'][0]['message']['content'])['url']
    input_email = json.loads(r['choices'][0]['message']['content'])['email']
    if input_email=='user@example.com':
        output = task_runner(task)
    else:
        output= install_script(input_url, input_email)
    return output

if __name__ == '__main__':
    import uvicorn
    uvicorn.run (app, host="0.0.0.0", port=8000)
