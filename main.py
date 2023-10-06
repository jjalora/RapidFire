import streamlit as st
from langchain import PromptTemplate
from langchain.llms.openai import OpenAIChat
from utils import load_data, get_src_dir, load_api_key_from_file, save_string_to_file

from os.path import join

PATH = get_src_dir()
pathToPrompts = join(PATH, "prompts")

module_one_template = load_data(join(pathToPrompts, "module_one.txt"))

module_one_prompt = PromptTemplate(
    input_variables=["strong_attribute", "weak_attribute", "identity", "wildcard", "common_essay_prompt"],
    template=module_one_template,
)

def load_LLM(openai_api_key):
    """Logic for loading the chain you want to use should go here."""
    # Make sure your openai_api_key is set as an environment variable
    llm = OpenAIChat(temperature=.2, openai_api_key=openai_api_key, model="gpt-4")
    return llm

API_KEY = load_api_key_from_file("config.txt")

if not API_KEY:
    st.error("Failed to load API key from config file.")
    raise SystemExit

llm = load_LLM(API_KEY)

# TODO: Hardcoded for now
STRONG_ATTR = "Unique Voice"
WEAK_ATTR = "Passive Voice"
IDENTITY = "runner"
WILDCARD = "spent time in juvenile detention"
COMMON_PROMPT = "The lessons we take from obstacles we encounter can be fundamental to later success. \
                Recount a time when you faced a challenge, setback, or failure. \
                How did it affect you, and what did you learn from the experience?"

prompt_with_attributes = module_one_prompt.format(strong_attribute=STRONG_ATTR,
                                                 weak_attribute=WEAK_ATTR,
                                                 identity=IDENTITY,
                                                 wildcard=WILDCARD,
                                                 common_essay_prompt=COMMON_PROMPT)

module_one_output = llm(prompt_with_attributes)

outputFile = join(PATH, "module_one_output.txt")
save_string_to_file(module_one_output, outputFile)

# st.header("Test")