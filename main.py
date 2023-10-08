import streamlit as st
from langchain import PromptTemplate
from utils import load_data, get_src_dir, load_api_key_from_file, load_LLM, \
    load_file_to_list, load_yaml_settings, create_pdf
import random
import base64

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

# Modify the navigation menu
if st.session_state.module_completed: 
    possible_pages.append("Module 2: Brainstorm")
    
# Check if the Statement Starter Report is needed
if "generate_report" in st.session_state and st.session_state.generate_report:
    possible_pages.append("Module 3: Statement Starter Report")

# Main navigation menu
page = st.sidebar.selectbox(
    "Choose a page",
    possible_pages
)

if page == "Module 1: Mad Libs":
    # Initial state variable to check if user has started after filling required fields
    if "has_started" not in st.session_state:
        st.session_state.has_started = False

    if "essay_count" not in st.session_state:
        st.session_state.essay_count = 0

    if "generate" not in st.session_state:
        st.session_state.generate = False

    if "all_strong_essays" not in st.session_state:
        st.session_state.all_strong_essays = []
    
    if "ratings" not in st.session_state:
        st.session_state.ratings = []


    if not st.session_state.has_started:
        st.header("RapidFire: Crafting Authentic College Essays with AI & Human Mentorship")
        st.write("(*) Please fill in the required information:")

        # Organize inputs across columns for better visuals
        col1, col2 = st.columns(2)

        with col1:
            st.session_state.first_name = st.text_input("First Name*")
            st.session_state.last_name = st.text_input("Last Name*")
            st.session_state.email = st.text_input("Email*")
            st.session_state.zip_code = st.text_input("Zip Code*")  # New Zip Code field
            st.session_state.grade = st.text_input("Grade*")

        with col2:
            st.session_state.school = st.text_input("School*")  # Moved to the right column
            st.session_state.counselor_name = st.text_input("Counselor’s Name*")
            st.session_state.counselor_email = st.text_input("Counselor Email*")
            st.session_state.top_schools = st.text_area("Top three schools you are applying to (comma separated)")

        # Check if all required fields are filled
        if st.session_state.first_name and st.session_state.last_name and st.session_state.email and \
           st.session_state.school and st.session_state.grade and st.session_state.counselor_name and \
           st.session_state.counselor_email and st.session_state.zip_code:
               
            # To pseudo-center the Start button
            start_col1, start_btn_col, start_col2 = st.columns([1, 2, 1])

            if start_btn_col.button("Start the Process of Crafting Your Authentic College Essay"):
                st.session_state.has_started = True
                st.experimental_rerun()

    else:
        if st.session_state.essay_count >= SETTINGS['num_rounds']:
            st.session_state.module_completed = True
            st.header("Module 1 Completion!")
            st.progress(1.0)  # Show progress bar at 100%
            st.write(f"You've successfully rated {SETTINGS['num_rounds']} essays. Please proceed to Module 2 in the sidebar.")
        else:
            st.info(f"""
                    This module provides examples of both strong and weak essays written by a fictional student. 
                    To advance to the next module, you must review and rate the stronger essay in {SETTINGS['num_rounds']} separate comparisons. 
                    Please note that generating the essays may take some time. Be patient.
                    """)
            # Initialize the progress bar
            progress_bar = st.progress(0)

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

            # Create columns for the Generate and Shuffle buttons
            btn_generate_col, btn_shuffle_col = st.columns([1, 1])

            # Generate button in the left (btn_generate_col) column
            if btn_generate_col.button("Generate"):
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
            
            # Shuffle button in the right (btn_shuffle_col) column
            if btn_shuffle_col.button('Shuffle Options'):
                st.session_state.identity = random.sample(load_file_to_list(join(pathToPrompts, "identity.txt")), 4)
                st.session_state.wildcard = random.sample(load_file_to_list(join(pathToPrompts, "wildcard.txt")), 4)
                st.experimental_rerun()

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
                    rerun_flag = False
                    for i in range(1, 6):
                        if cols[i-1].button(str(i), key=f"rate_{i}"):
                            st.session_state.ratings.append(i)
                            st.session_state.essay_count += 1

                            # Refresh the identity and wildcard options
                            st.session_state.identity = random.sample(load_file_to_list(join(pathToPrompts, "identity.txt")), 4)
                            st.session_state.wildcard = random.sample(load_file_to_list(join(pathToPrompts, "wildcard.txt")), 4)

                            st.session_state.generate = False  # Reset generation state after rating
                            rerun_flag = True

                    if rerun_flag:
                        if st.session_state.essay_count >= SETTINGS['num_rounds']:
                            st.session_state.module_completed = True
                            st.experimental_rerun()
                        else:
                            st.experimental_rerun()

                if st.session_state.ratings:
                    st.write(f"You rated the last essay {st.session_state.ratings[-1]} out of 5.")

elif page == "Module 2: Brainstorm":
    st.header("Module 2: Brainstorm")

    if "context" not in st.session_state:
        st.session_state.context = ""

    if "messages" not in st.session_state:
        st.session_state.messages = []

        # Load initial prompts from module_two.txt and start the conversation
        initial_prompt = load_data(join(pathToPrompts, "module_two.txt"))
        st.session_state.context += "\n\n" + initial_prompt
        response = llm(st.session_state.context)
        st.session_state.messages.append({"role": "assistant", "content": response})  # Only add the LLM's response
        st.session_state.context += "\n\n" + response

    # Display the previous messages
    topic_identified = False
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
        if "[TOPIC IDENTIFIED]" in message["content"]:
            topic_identified = True

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

    # Check if topic was identified and display button
    if topic_identified:
        if st.button("Generate Report for Counselor"):
            # TODO: Place holder code. Your logic when the button is clicked
            st.write("Please proceed to Module 3 in the sidebar for your counselor report.")
            st.session_state.generate_report = True
            page = "Module 3: Statement Starter Report" # Redirect to Module 3
elif page == "Module 3: Statement Starter Report":
    st.header("Module 3: Statement Starter Report")
    
    # Load and append the initial prompts from module_three.txt
    if "context" not in st.session_state:
        st.session_state.context = ""
    
    # Add user info from Module 1
    user_info = f"""
                First Name: {st.session_state.first_name}
                Last Name: {st.session_state.last_name}
                Email: {st.session_state.email}
                School: {st.session_state.school}
                Grade: {st.session_state.grade}
                Counselor's Name: {st.session_state.counselor_name}
                Counselor Email: {st.session_state.counselor_email}
                Top Schools: {st.session_state.top_schools}
                Zip Code: {st.session_state.zip_code}
                """
    initial_prompt = load_data(join(pathToPrompts, "module_three.txt"))
    st.session_state.context += "\n\n" + user_info + "\n\n" + initial_prompt
    response = llm(st.session_state.context)

    # Generate PDF from the context
    pdf_buffer = create_pdf(response)

    # Encode the BytesIO stream to base64
    b64 = base64.b64encode(pdf_buffer.getvalue()).decode()

    # Embed the base64 encoded PDF in an HTML iframe
    pdf_display = f"""
    <iframe src="data:application/pdf;base64,{b64}" width="700" height="1000" type='application/pdf'>
    </iframe>
    """
    st.markdown(pdf_display, unsafe_allow_html=True)