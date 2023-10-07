import streamlit as st
from langchain import PromptTemplate
from utils import load_data, get_src_dir, load_api_key_from_file, load_LLM, \
    load_file_to_list, load_yaml_settings
import random

from os.path import join, exists

PATH = get_src_dir()
pathToPrompts = join(PATH, "prompts")

# Load the settings from settings.yaml
SETTINGS = load_yaml_settings(join(PATH, "settings.yaml"))

module_one_template = load_data(join(pathToPrompts, "module_one.txt"))
module_one_prompt = PromptTemplate(
    input_variables=["strong_attribute", "weak_attribute", "identity", "wildcard", "common_essay_prompt"],
    template=module_one_template,
)

# Load API key either from local machine or from streamlit secrets
key_path = join(PATH, "config.txt")
if exists(key_path):
    API_KEY = load_api_key_from_file(key_path)
    if not API_KEY:
        st.error("Failed to load API key from config file.")
        raise SystemExit
else:
    API_KEY = st.secrets["openai_secret_key"]

# Load LLM
llm = load_LLM(API_KEY)

@st.cache_data(show_spinner=False)  # Disable the spinner for a cleaner UI
def get_module_one_output(prompt_with_attributes):
    return llm(prompt_with_attributes)

# Load attributes for Module 1
if 'strong_attr' not in st.session_state:
    st.session_state.strong_attr = random.sample(load_file_to_list(join(pathToPrompts, "strong_attributes.txt")), 1)[0]
strong_attr = st.session_state.strong_attr

if 'weak_attr' not in st.session_state:
    st.session_state.weak_attr = random.sample(load_file_to_list(join(pathToPrompts, "weak_attributes.txt")), 1)[0]
weak_attr = st.session_state.weak_attr

if 'wildcard' not in st.session_state:
    st.session_state.wildcard = random.sample(load_file_to_list(join(pathToPrompts, "wildcard.txt")), 4)
wildcard = st.session_state.wildcard

if 'identity' not in st.session_state:
    st.session_state.identity = random.sample(load_file_to_list(join(pathToPrompts, "identity.txt")), 4)
identity = st.session_state.identity

if 'common_prompt' not in st.session_state:
    st.session_state.common_prompt = load_file_to_list(join(pathToPrompts, "common_questions.txt"))
common_prompt = st.session_state.common_prompt

####### Streamlit UI #######
# Initialize the state variable for module completion
if "module_completed" not in st.session_state:
    st.session_state.module_completed = False

# Define the possible pages, start with only "Module 1: Mad Libs"
possible_pages = ["Module 1: Mad Libs"]

if st.session_state.module_completed:
    possible_pages.append("Module 2: Brainstorm")

# Main navigation menu
page = st.sidebar.selectbox(
    "Choose a page",
    possible_pages
)

if page == "Module 1: Mad Libs":
    # Initialize the progress bar
    progress_bar = st.progress(0)

    # Initialize state variables
    if "ratings" not in st.session_state:
        st.session_state.ratings = []
    if "essay_count" not in st.session_state:
        st.session_state.essay_count = 0
    if "context" not in st.session_state:
        st.session_state.context = ""
    if "all_strong_essays" not in st.session_state:
        st.session_state.all_strong_essays = []
    if "generate" not in st.session_state:
        st.session_state.generate = False

    # Update the progress bar based on the number of essays rated
    if st.session_state.essay_count:
        progress_percentage = st.session_state.essay_count / SETTINGS['num_rounds']
        progress_bar.progress(progress_percentage)

    # Dropdown for common_prompt
    selected_common_prompt = st.selectbox("Select a Common Prompt:", common_prompt)

    # Display identity and wildcard options in columns
    col1, col2 = st.columns(2)

    # Using radio buttons for identity on the left column
    selected_identity = col1.radio("Choose an Identity:", identity)

    # Using radio buttons for wildcard on the right column
    selected_wildcard = col2.radio("Choose a Wildcard:", wildcard)

    # Generate button
    if st.button("Generate"):
        st.session_state.generate = True

        prompt_with_attributes = module_one_prompt.format(
            strong_attribute=strong_attr,
            weak_attribute=weak_attr,
            identity=selected_identity,
            wildcard=selected_wildcard,
            common_essay_prompt=selected_common_prompt
        )

        module_one_output = get_module_one_output(prompt_with_attributes)

        # Parsing the output to get strong and weak essays
        start_strong = module_one_output.find('Strong Essay') + len('Strong Essay') + 1
        start_weak = module_one_output.find('Weak Essay')
        end_strong = start_weak - 1

        st.session_state.strong_essay = module_one_output[start_strong:end_strong].strip()
        st.session_state.weak_essay = module_one_output[start_weak + len('Weak Essay') + 1:].strip()

        # Append the new strong essay to the list
        st.session_state.all_strong_essays.append(st.session_state.strong_essay)

    # If essays are generated, display them
    if st.session_state.generate:
        col_strong, col_weak = st.columns(2)

        with col_strong:
            st.subheader("Strong Essay")
            st.text_area("", value=st.session_state.strong_essay, height=400)

        with col_weak:
            st.subheader("Weak Essay")
            st.text_area("", value=st.session_state.weak_essay, height=400)

        with col_strong:
            st.subheader("Rate the Strong Essay:")

            # Creating a row of buttons
            cols = st.columns(5)
            for i in range(1, 6):
                if cols[i-1].button(str(i), key=f"rate_{i}"):
                    st.session_state.ratings.append(i)
                    st.session_state.essay_count += 1
                    
                    # Refresh the identity and wildcard options
                    st.session_state.identity = random.sample(load_file_to_list(join(pathToPrompts, "identity.txt")), 4)
                    st.session_state.wildcard = random.sample(load_file_to_list(join(pathToPrompts, "wildcard.txt")), 4)
                    
                    st.session_state.generate = False  # Reset generation state after rating

                    # Refresh the page to show new selections and hide the essays
                    st.experimental_rerun()

        if st.session_state.ratings:
            st.write(f"You rated the last essay {st.session_state.ratings[-1]} out of 5.")
elif page == "Module 2: Brainstorm":
    st.header("Module 2: Brainstorm")

    if "messages" not in st.session_state:
        st.session_state.messages = []

        # Load initial prompts from module_two.txt and start the conversation
        initial_prompt = load_data(join(pathToPrompts, "module_two.txt"))
        st.session_state.context += "\n\n" + initial_prompt
        response = llm(st.session_state.context)
        st.session_state.messages.append({"role": "assistant", "content": response})  # Only add the LLM's response
        st.session_state.context += "\n\n" + response

    # Display the previous messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Get user's input
    prompt = st.chat_input("You: ")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.context += "\n\n" + prompt

        # Obtain the LLM's response using the accumulated context and user's message
        response = llm(st.session_state.context)

        st.session_state.messages.append({"role": "assistant", "content": response})
        st.session_state.context += "\n\n" + response

        # Force rerun to update the chat immediately
        st.experimental_rerun()