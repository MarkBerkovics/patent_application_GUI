import streamlit as st
import requests
import time
import os
from docx import Document
from PyPDF2 import PdfReader

st.title("Patent Application Writer 📑")
st.image("images/patent_lawyer.jpg", width=300)

st.markdown("#### Hi Ariel, I'm here to assist you with crafting a patent application. \
    Please provide a complete description of the patent idea")
st.markdown("")

# Base url and all the endpoints
base_url = "https://patent-application-image-2dkcwif5ra-ew.a.run.app"
response_url = base_url + "/response"
compile_url = base_url + "/compile"
reset_url = base_url + "/reset"


# Function to extract text from DOCX
def extract_text_from_docx(file):
    doc = Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

# Function to extract text from PDF
def extract_text_from_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


if "prompt_template" not in st.session_state:
    prompt_template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', 'prompt', 'system_prompt.txt')
    with open(prompt_template_path, 'r') as f:
        st.session_state.prompt_template = f.read()

# Set a default model
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4o"

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": st.session_state.prompt_template}]

# Display chat messages from history on app rerun
for i, message in enumerate(st.session_state.messages):
    if i != 0:
        if message["role"] == "user":
            #with st:
            with st.chat_message(message["role"], avatar="images/Ariel_Averbuch_avatar.jpg"):
                st.markdown(message["content"])
        else:
            #with st:
            with st.chat_message(message["role"], avatar="images/patent_lawyer_avatar.jpg"):
                st.markdown(message["content"])

# Accept text input or file
query_input = st.chat_input("Please provide a complete description of the patent idea", accept_file=True)

if query_input:

    query = query_input.text

    # Upload file and determine type
    if query_input.files:

        filename = query_input.files[0].name.lower()
        if filename.endswith(".pdf"):
            query += '\n\n' + extract_text_from_pdf(query_input.files[0])
        elif filename.endswith(".docx"):
            query += '\n\n' + extract_text_from_docx(query_input.files[0])
        elif filename.endswith(".txt"):
            query += '\n\n' + query_input.files[0].read().decode("utf-8")
        else:
            st.error("Unsupported file type. Please upload a PDF, DOCX, or TXT file.")


    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": query})
    # Display user message in chat message container
    with st.chat_message("user", avatar="images/Ariel_Averbuch_avatar.jpg"):
        st.markdown(query)

    # Display assistant response in chat message container
    with st.chat_message("assistant", avatar="images/patent_lawyer_avatar.jpg"):

        def fetch_response(response_url, query, messages):
            payload = {
                "query": query,
                "messages": messages  # Send entire chat history
            }

            response = requests.post(response_url, json=payload, stream=True)

            def stream():
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        yield chunk.decode("utf-8")  # Decode and stream response

            return stream

        ai_response = st.write_stream(fetch_response(response_url, query, st.session_state.messages))

    st.session_state.messages.append({"role": "assistant", "content": ai_response})

with st.sidebar:

    if st.button("Reset chat"):

        st.session_state.messages = [{"role": "system", "content": st.session_state.prompt_template}]

        response = requests.get(reset_url)
        st.write((response.json()['message']))
        time.sleep(0.5)
        st.rerun()

    if st.button("Compile a google doc with the data"):
        with st.spinner("Generating Google Doc ...", show_time=True):

            payload = {
                "query": query,
                "messages": st.session_state.messages
            }

            response = requests.post(compile_url, json=payload)
            if response.status_code == 200:
                draft = response.json()["draft"]
                st.text_area("Draft", draft, height=400)

                st.success("✅ Google Doc generated successfully")
            else:
                st.error("❌ Error generating Google Doc")
