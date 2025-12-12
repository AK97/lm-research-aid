import streamlit as st
from src.rag import RAG_Handler

st.set_page_config(layout = "wide")
st.title("StudyLM Research Aid")

left, right = st.columns([4,1])

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hello, begin by uploading document(s) and asking questions"
        }
    ]

# Initialize RAG handling object
ragger = RAG_Handler()

# Tracking uploaded docs
st.session_state.uploaded_files = []

with left:
    st.subheader("Chat")
    messages = st.container()
    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

with right:
    st.subheader("Documents")
    st.session_state.uploaded_files = st.file_uploader(label = "Uploaded pdfs", type = "pdf", accept_multiple_files = True)

# User input
if prompt := st.chat_input("Ask for summaries, ideas, and more"):

    with messages:
        st.chat_message("user").markdown(prompt)

    st.session_state.messages.append({"role": "user", "content": prompt})

    response = ragger.get_ai_response(prompt, st.session_state.uploaded_files)

    with messages:
        st.chat_message("assistant").markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})