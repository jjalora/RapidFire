import os
import inspect

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
    with open(filename, 'r') as file:
        for line in file:
            key, value = line.strip().split('=')
            if key == "API_KEY":
                return value
    return None

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