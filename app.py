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
from subprocess import run

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


primary_prompt = """
You are an automated agent, so generate python code that does the specified task.
Assume uv and python is preinstalled.
If you need to run any uv script then use uv run {nameofscript} arguments.
Assume that the code you generate will be executed inside a docker container.
Inorder to perform any task if some python package is required to install, provide name of those modules.
"""
app.add_middleware (
    CORSMiddleware,
    allow_origins = ['*'],
    allow_credentials = True,
    allow_methods = ['GET', 'POST'],
    allow_headers = ['*']
)

tools = [
    {
        "type": "function",
        "function": {
            "name": "script-runner",
            "description": "Install a package and run a script from a url with provided arguments",
            "parameters": {
                "type": "object",
                "properties": {
                    "script_url": {
                        "type": "string",
                        "description": "The url of the script to run"
                    },
                    "args": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of arguments to be passed to the script"
                    }                    
                },
                "required": ["script_url", "args"]
            }
        } 
    }
]

AIPROXY_TOKEN=os.getenv("AIPROXY_TOKEN")

AIPROXY_TOKEN = 'eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIzZHMzMDAwMTg1QGRzLnN0dWR5LmlpdG0uYWMuaW4ifQ.zjOoLtUcmCP0HZ62lm1c_xf8mCb3uBff9SxAXXRxdcU'

url = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"

headers = {
        "Content-type":"application/json",
        "Authorization": f"Bearer {AIPROXY_TOKEN}"
    }

@app.get ("/")
def home():
    print(AIPROXY_TOKEN)
    return {"We have just started our project"}

@app.get ("/read")
def read_file (path: str):
    try:
        with open(path,"r") as f:
            return f.read()
    except Exception as e :
        raise HTTPException(status_code=404, detail="file doesnt exist")
@app.post("/")
def home():
    return "Welcome to task runner"

@app.post ("/run")
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
    uv_script = f"""
# /// script
# requires-python = ">=3.8"  # Updated to a valid version
# dependencies = [
#    {dependency}
# ]
# ///
    """
    # script_url = arguments['script_url']
    # email = arguments['args'][0]
    # command = ["uv", "run", script_url, email]
    # subprocess.run(command)
    with open("llm_code.py","w") as f:
        f.write(uv_script)
        f.write(code)

output= run(["uv","run","llm_code.py"],capture_output=True,text=True,cwd=os.getcwd())
print(output)
if __name__ == '__main__':
    import uvicorn
    uvicorn.run (app, host="0.0.0.0", port=8000)
