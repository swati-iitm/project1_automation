# /// script
# requires-python = ">=3.8"  # Updated to a valid version
# dependencies = [
#    "pillow",
#    "faker"
# ]
# ///

import os
import subprocess
import urllib.request

# Ensure `USER_EMAIL` is set
user_email = os.getenv("USER_EMAIL")
if not user_email:
    print("USER_EMAIL environment variable is not set. Please set it or provide an email.")
    user_email = input("Enter your email: ").strip()

# Download the `datagen.py` script
script_url = "https://raw.githubusercontent.com/sanand0/tools-in-data-science-public/tds-2025-01/project-1/datagen.py"
script_name = "datagen.py"
try:
    print(f"Downloading script from {script_url}...")
    urllib.request.urlretrieve(script_url, script_name)
    print(f"Script downloaded as {script_name}.")
except Exception as e:
    print(f"Failed to download the script: {e}")
    exit(1)

# Run the script with the provided email
try:
    print(f"Running {script_name} with email: {user_email}...")
    subprocess.run(["python", script_name, user_email], check=True)
    print("Script executed successfully. Check the generated files in the current directory.")
except subprocess.CalledProcessError as e:
    print(f"Error executing {script_name}: {e}")
    exit(1)
