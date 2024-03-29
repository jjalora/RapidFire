import os
import inspect
from langchain.llms.openai import OpenAIChat
import yaml
from fpdf import FPDF
import io
import yagmail

def load_data(filename):
    with open(filename, 'r') as file:
        return file.read().strip()

def get_src_dir():
    """
    Returns the directory of the script that called this function.
    """
    # Get the caller's stack frame
    frame = inspect.stack()[1]
    
    # Extract the path from the frame
    path = frame[0].f_globals['__file__']
    
    return os.path.dirname(os.path.abspath(path))

def load_api_key_from_file(filename):
    config_data = {}
    
    with open(filename, 'r') as file:
        for line in file:
            key, value = line.strip().split('=')
            if key == "API_KEY":
                config_data['API_KEY'] = value
            elif key == "EMAIL_PASSWORD":
                config_data['EMAIL_PASSWORD'] = value

    return config_data

def save_string_to_file(content, filename):
    """
    Save a given string to a specified text file.

    Parameters:
    - content (str): The string you want to save.
    - filename (str): The name (or path) of the file where the string should be saved.

    Returns:
    - None
    """
    with open(filename, 'w') as file:
        file.write(content)

def load_LLM(key):
    """Logic for loading the chain you want to use should go here."""
    # Make sure your openai_api_key is set as an environment variable
    llm = OpenAIChat(temperature=.2, openai_api_key=key, model="gpt-4")
    return llm

def load_file_to_list(filename):
    """
    Load contents of a text file into a list, where each line in the file becomes an item in the list.
    
    Parameters:
    - filename (str): Path to the text file.
    
    Returns:
    - list: List containing each line from the file as an item.
    """
    with open(filename, 'r') as file:
        # Read lines and strip trailing and leading whitespace from each line
        return [line.strip() for line in file]

def load_yaml_settings(filename):
    """
    Load a YAML file and return the contents as a dictionary.
    
    Parameters:
    - filename (str): Path to the YAML file.
    
    Returns:
    - dict: Dictionary containing the contents of the YAML file.
    """
    with open(filename, 'r') as file:
        return yaml.load(file, Loader=yaml.FullLoader)

def create_pdf(text):
    """
    Create a PDF document from a given string.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=text)

    # Save to a BytesIO object and return that
    pdf_buffer = io.BytesIO()
    pdf.output(pdf_buffer, "F")
    pdf_buffer.seek(0)
    return pdf_buffer

import yagmail
import tempfile

def send_email_with_pdf(student_name, sender_email, recipient_email, subject, content, pdf_buffer, email_password):
    temp_filename = f"{student_name}_counseling_report.pdf"
    with open(temp_filename, "wb") as f:
        f.write(pdf_buffer.getvalue())

    # Create yagmail client using the sender email and the provided email password
    yag = yagmail.SMTP(sender_email, email_password)
    yag.send(
        to=recipient_email,
        subject=subject,
        contents=content,
        attachments=[temp_filename]  # Pass the temp file path as the attachment
    )
    
    # Optionally delete the temp file if you don't want to keep it
    # os.remove(temp_filename)
