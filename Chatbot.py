import os
import tempfile
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from openai import OpenAI

from helper_functions.document_loader import load_and_split
from logics.rag import answer_query as rag_answer_query


if load_dotenv('.env'):
    # for local development
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
else:
    OPENAI_API_KEY = st.secrets['OPENAI_API_KEY']


# Pass the API Key to the OpenAI Client
client = OpenAI(api_key=OPENAI_API_KEY)

# Some other code here are omitted for brevity


# ============================================================
# Page configuration
# ============================================================

st.set_page_config(
    page_title="Healthcare Financing SOP Assistant",
    page_icon="🤖",
)


# ============================================================
# Simple UI styling
# ============================================================

st.markdown(
    """
    <style>

    .main {
        padding-top: 1.5rem;
    }

    .hero {
        background: linear-gradient(
            135deg,
            #006b54 0%,
            #005744 100%
        );
        padding: 1.5rem 1.8rem;
        border-radius: 14px;
        color: white;
        margin-bottom: 1.5rem;
    }

    .hero h1 {
        color: white;
        font-size: 2rem;
        margin-bottom: 0.4rem;
    }

    .hero p {
        color: #e8f5f1;
        font-size: 1rem;
        margin-bottom: 0;
        line-height: 1.5;
    }

    .section-title {
        color: #006b54;
        font-size: 1.3rem;
        font-weight: 700;
        margin-top: 1.5rem;
        margin-bottom: 0.5rem;
    }

    .notice {
        background: #fff8e8;
        border-left: 4px solid #d99a00;
        border-radius: 6px;
        padding: 0.8rem 1rem;
        color: #555555;
        font-size: 0.85rem;
        line-height: 1.5;
        margin-bottom: 1.2rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Password protection
# ============================================================

from helper_functions.utility import check_credentials


# Check if the username and password is correct.
if not check_credentials():

    st.markdown(
        """
        <br><br><br><br>
        <div style="background-color:#fff3cd; border:1px solid #ffeeba; padding:16px; border-radius:8px; color:#856404;">
        <div style="font-size:1.2em; font-weight:bold;">⚠️ IMPORTANT NOTICE</div>
        This web application is developed as a proof-of-concept prototype. The information provided here is <strong>NOT intended for actual usage</strong> and should not be relied upon for making any decisions, especially those related to financial, legal, or healthcare matters.
        <br><br>
        <strong>Furthermore, please be aware that the LLM may generate inaccurate or incorrect information. You assume full responsibility for how you use any generated output.</strong>
        <br><br>
        Always consult with qualified professionals for accurate and personalised advice.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.stop()


# ============================================================
# Page header
# ============================================================

st.title("Healthcare Financing Media/Comms SOP Assistant")

st.write(
    """
    Ask questions about the Healthcare Financing communications
    workflows, or describe a specific situation to find out which
    SOP and pathway may apply.
    """
)


# ============================================================
# Session state
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []


if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = "You are a helpful assistant."


if "starter_prompt" not in st.session_state:
    st.session_state.starter_prompt = ""


# ============================================================
# Capture pending starter prompt
# ============================================================

# Store the selected starter prompt in a local variable.
# This allows us to process it as a normal user message while
# ensuring the starter cards do not reappear during the rerun.

pending_starter_prompt = st.session_state.starter_prompt


# ============================================================
# Starter prompts
# ============================================================

# Starter prompts are only shown at the beginning of a
# completely new conversation.
#
# Once the user selects either starter prompt, the cards
# disappear and the selected prompt is processed as the
# first user message.

if (
    not st.session_state.messages
    and not pending_starter_prompt
):

    st.markdown(
        '<div class="section-title">How can I help?</div>',
        unsafe_allow_html=True,
    )

    starter_col1, starter_col2 = st.columns(2)


    # --------------------------------------------------------
    # Starter prompt 1
    # --------------------------------------------------------

    with starter_col1:

        with st.container(border=True):

            st.markdown(
                "### 📖 Learn about the SOP"
            )

            st.caption(
                "For users who want to understand the workflow."
            )

            st.write(
                "Get an overview of when the SOPs apply, "
                "the different pathways, key roles and main steps."
            )

            if st.button(
                "Start here →",
                key="learn_sop",
                use_container_width=True,
            ):

                st.session_state.starter_prompt = (
                    "I'm new to this SOP. Can you give me an overview "
                    "of when it applies, the different pathways, the "
                    "key roles, and the main steps involved?"
                )

                st.rerun()


    # --------------------------------------------------------
    # Starter prompt 2
    # --------------------------------------------------------

    with starter_col2:

        with st.container(border=True):

            st.markdown(
                "### 💡 Apply to my scenario"
            )

            st.caption(
                "For users who already have a situation in mind."
            )

            st.write(
                "Describe your context to get advice on whether "
                "the SOP applies and what you should do next."
            )

            if st.button(
                "Describe my scenario →",
                key="scenario_sop",
                use_container_width=True,
            ):

                st.session_state.starter_prompt = (
                    "I have a media-related situation. Can I describe "
                    "what happened and get advice on whether this SOP "
                    "applies, which pathway I should follow, and what "
                    "I should do next?"
                )

                st.rerun()


# ============================================================
# Clear the processed starter prompt
# ============================================================

# If a starter prompt was selected, clear it from session state
# now that we have captured it in pending_starter_prompt.
#
# This prevents the same starter prompt from being processed
# again on a subsequent rerun.

if pending_starter_prompt:

    st.session_state.starter_prompt = ""


# ============================================================
# Sidebar
# ============================================================

st.sidebar.header("⚙️ Settings")


# ------------------------------------------------------------
# Uploaded documents
# ------------------------------------------------------------

uploaded_files = st.sidebar.file_uploader(
    "📄 Upload Documents",
    type=["pdf", "txt"],
    accept_multiple_files=True,
)


if uploaded_files:

    chunks = load_and_split(
        uploaded_files
    )

    if chunks:

        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=OPENAI_API_KEY,
        )

        vectorstore = Chroma.from_documents(
            chunks,
            embeddings,
        )

        st.session_state.vectorstore = vectorstore

        filenames = [
            getattr(
                uploaded_file,
                "name",
                "unknown"
            )
            for uploaded_file in uploaded_files
        ]

        st.session_state.uploaded_filenames = filenames
        st.session_state.chunk_count = len(chunks)

        st.sidebar.success(
            f"Ready! Indexed {len(chunks)} chunks "
            f"from {len(filenames)} file(s)."
        )

    else:

        st.session_state.vectorstore = None
        st.session_state.uploaded_filenames = []
        st.session_state.chunk_count = 0

        st.sidebar.warning(
            "No readable text was found in the uploaded files."
        )


if "uploaded_filenames" not in st.session_state:
    st.session_state.uploaded_filenames = []


if "chunk_count" not in st.session_state:
    st.session_state.chunk_count = 0


if st.session_state.uploaded_filenames:

    st.sidebar.caption(
        "Uploaded files:"
    )

    for filename in st.session_state.uploaded_filenames:

        st.sidebar.caption(
            f"- {filename}"
        )

    st.sidebar.caption(
        f"Total chunks: {st.session_state.chunk_count}"
    )


# ------------------------------------------------------------
# Retrieval settings
# ------------------------------------------------------------

k_value = 4


# ------------------------------------------------------------
# Persona
# ------------------------------------------------------------

st.sidebar.markdown(
    "### 🎭 Response Style"
)


persona_options = {

    "SOP Navigator": (
        "You are an SOP Navigator. Help the user understand "
        "which pathway applies, explain the workflow step by "
        "step, and guide them through the SOP clearly and practically."
    ),

    "Comms Advisor": (
        "You are a Comms Advisor. Help the user apply the SOP "
        "to their specific situation, explain what actions they "
        "should take, and tailor the guidance to their scenario."
    ),

    "SOP Checker": (
        "You are an SOP Checker. Review the user's proposed "
        "approach against the SOP, identify any gaps or missing "
        "steps, and flag what should be adjusted to align with "
        "the SOP."
    ),
}


selected_persona = st.sidebar.selectbox(
    "Select Persona",
    options=list(persona_options.keys()),
    index=0,
)


st.session_state.system_prompt = (
    persona_options[selected_persona]
)


# ------------------------------------------------------------
# Model
# ------------------------------------------------------------

st.sidebar.markdown(
    "### 🤖 Model"
)


model = st.sidebar.selectbox(
    "Select Model",
    ["gpt-4o-mini", "gpt-4o"],
    index=0,
)


temperature = 0.4


# ------------------------------------------------------------
# Conversation information
# ------------------------------------------------------------

conversation_text = "\n".join(
    message["content"]
    for message in st.session_state.messages
)


character_count = len(
    conversation_text
)


st.sidebar.caption(
    f"Conversation characters: {character_count}"
)


# ============================================================
# Existing conversation
# ============================================================

for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        st.write(
            message["content"]
        )


# ============================================================
# Determine prompt
# ============================================================

# If a starter prompt was selected, use it as the prompt.
# Otherwise, wait for normal chat input.

prompt = pending_starter_prompt


# ============================================================
# Chat input
# ============================================================

chat_prompt = st.chat_input(
    "Describe your situation or ask a question..."
)


if chat_prompt:

    prompt = chat_prompt


# ============================================================
# Process user prompt
# ============================================================

if prompt:

    # --------------------------------------------------------
    # Add user message
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )


    with st.chat_message("user"):

        st.write(
            prompt
        )


    # --------------------------------------------------------
    # Check API key
    # --------------------------------------------------------

    api_key = os.getenv(
        "OPENAI_API_KEY"
    )


    if not api_key:

        st.warning(
            "Please set OPENAI_API_KEY in your environment "
            "or .env file."
        )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": (
                    "Please configure your OpenAI API key."
                ),
            }
        )

        st.stop()


    # --------------------------------------------------------
    # Send prompt to RAG
    # --------------------------------------------------------

    assistant_response_text = (
        rag_answer_query(
            prompt,
            chat_history=st.session_state.messages,
        )
    )


    # --------------------------------------------------------
    # Display assistant response
    # --------------------------------------------------------

    with st.chat_message(
        "assistant"
    ):

        st.write(
            assistant_response_text
        )


    # --------------------------------------------------------
    # Save assistant response
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": assistant_response_text,
        }
    )


# ============================================================
# Sidebar conversation controls
# ============================================================

if st.sidebar.button(
    "Clear Conversation",
    use_container_width=True,
):

    st.session_state.messages = []

    st.session_state.starter_prompt = ""

    st.rerun()


# ============================================================
# Download conversation
# ============================================================

chat_export = ""


for message in st.session_state.messages:

    role = message["role"].upper()

    content = message["content"]

    chat_export += (
        f"{role}: {content}\n\n"
    )


st.sidebar.download_button(
    label="Download Chat",
    data=chat_export,
    file_name="chat_conversation.txt",
    mime="text/plain",
    use_container_width=True,
)