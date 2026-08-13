import streamlit as st


# ============================================================
# Page configuration
# ============================================================

st.set_page_config(
    page_title="Methodology",
    page_icon="⚙️",
    layout="wide",
)


# ============================================================
# Custom styling
# ============================================================

st.markdown(
    """
    <style>

    /* ========================================================
       General page
       ======================================================== */

    .main {
        padding-top: 2rem;
    }


    /* ========================================================
       Hero
       ======================================================== */

    .hero {
        background: linear-gradient(
            135deg,
            #006b54 0%,
            #005744 100%
        );
        padding: 2.2rem 2.5rem;
        border-radius: 18px;
        color: white;
        margin-bottom: 2rem;
    }

    .hero-title {
        color: white;
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0 0 0.5rem 0;
    }

    .hero-description {
        color: #e8f5f1;
        font-size: 1.05rem;
        line-height: 1.6;
        margin: 0;
    }


    /* ========================================================
       Major section headings
       ======================================================== */

    .section-title {
        color: #006b54;
        font-size: 1.35rem;
        font-weight: 700;
        line-height: 1.4;
        margin-top: 2rem;
        margin-bottom: 0.7rem;
    }


    /* ========================================================
       Subsection headings
       ======================================================== */

    .subsection-title {
        color: #333333;
        font-size: 1.05rem;
        font-weight: 700;
        line-height: 1.4;
        margin-top: 1.3rem;
        margin-bottom: 0.5rem;
    }


    /* ========================================================
       Body text
       ======================================================== */

    .body-text {
        color: #333333;
        font-size: 0.95rem;
        line-height: 1.6;
    }


    /* ========================================================
       SOP cards
       ======================================================== */

    .sop-card {
        background: white;
        border: 1px solid #dfe8e4;
        border-radius: 14px;
        padding: 1.4rem;
        height: 100%;
    }

    .sop-card-title {
        color: #006b54;
        font-size: 1rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        line-height: 1.4;
    }

    .sop-label {
        display: inline-block;
        background: #e5f3ee;
        color: #006b54;
        font-size: 0.78rem;
        font-weight: 700;
        padding: 0.25rem 0.65rem;
        border-radius: 20px;
        margin-bottom: 0.7rem;
    }

    .sop-card p,
    .sop-card li {
        color: #333333;
        font-size: 0.92rem;
        line-height: 1.55;
    }

    .sop-card ul {
        padding-left: 1.2rem;
    }


    /* ========================================================
       Simple callouts
       ======================================================== */

    .callout {
        background: #eef7f4;
        border-left: 5px solid #006b54;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin: 1rem 0;
        color: #333333;
        font-size: 0.95rem;
        line-height: 1.55;
    }


    /* ========================================================
       Footer
       ======================================================== */

    .footer {
        text-align: center;
        color: #777777;
        font-size: 0.8rem;
        padding: 2rem 0 1rem 0;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# To password protect the app
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
# Hero
# ============================================================


st.markdown(
    """
    <div class="hero">
        <h1>⚙️ Methodology</h1>
        <p>
            How the SOP Assistant identifies the relevant workflow,
            retrieves supporting information, and generates
            grounded guidance for users.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# How the SOP Assistant works
# ============================================================

st.markdown(
    '<div class="section-title">How the SOP Assistant works</div>',
    unsafe_allow_html=True,
)

st.write(
    """
    The SOP Assistant uses a situation-first approach. Instead of
    requiring users to know which SOP or section to search, users
    can describe what they are trying to do and the chatbot determines
    which approved workflow is most relevant.
    """
)


st.divider()

# ============================================================
# 1. How information flows through the chatbot
# ============================================================

st.markdown(
    '<div class="section-title">How information flows through the chatbot</div>',
    unsafe_allow_html=True,
)

st.write(
    """
    The chatbot's methodology can be understood through three stages:
    <strong>Inputs → Processing → Outputs</strong>. Multiple sources
    of information are brought together before the chatbot generates
    its response.
    """,
    unsafe_allow_html=True,
)


# ------------------------------------------------------------
# Inputs
# ------------------------------------------------------------

st.markdown(
    '<div class="subsection-title">1. Inputs</div>',
    unsafe_allow_html=True,
)

st.write(
    "The chatbot receives information from several sources:"
)

input_col1, input_col2 = st.columns(2)

with input_col1:

    with st.container(border=True):

        st.markdown("**📚 SOP Knowledge Base**")

        st.write(
            """
            Approved Healthcare Financing SOPs stored as structured
            JSON sources.
            """
        )

    with st.container(border=True):

        st.markdown("**💬 User Question / Scenario**")

        st.write(
            """
            The user's question or description of what they are
            trying to prepare, update, share or issue.
            """
        )


with input_col2:

    with st.container(border=True):

        st.markdown("**📄 Uploaded Documents**")

        st.write(
            """
            Optional PDF documents provided by the user to
            give the chatbot additional context.
            """
        )

    with st.container(border=True):

        st.markdown("**🎭 Selected Persona**")

        st.write(
            """
            The user's preferred response style: SOP Navigator,
            Comms Advisor or SOP Checker.
            """
        )


# ------------------------------------------------------------
# Processing
# ------------------------------------------------------------

st.markdown(
    '<div class="subsection-title">2. Processing</div>',
    unsafe_allow_html=True,
)

st.write(
    """
    The chatbot processes these inputs through a series of reasoning
    and retrieval steps:
    """
)

processing = [
    (
        "1. Understand",
        "Understand the user's intent, situation and information need."
    ),
    (
        "2. Identify",
        "Identify the relevant SOP and workflow or pathway."
    ),
    (
        "3. Retrieve",
        "Retrieve relevant information from the SOP knowledge base and, where applicable, uploaded documents."
    ),
    (
        "4. Contextualise",
        "Consider the retrieved information together with the user's scenario and supporting documents."
    ),
    (
        "5. Apply",
        "Apply the relevant SOP requirements to the user's specific situation."
    ),
    (
        "6. Generate",
        "Generate a response using the selected persona."
    ),
]

for title, description in processing:

    with st.container(border=True):

        st.markdown(f"**{title}**")

        st.write(description)


# ------------------------------------------------------------
# Outputs
# ------------------------------------------------------------

st.markdown(
    '<div class="subsection-title">3. Outputs</div>',
    unsafe_allow_html=True,
)

st.write(
    """
    The chatbot generates a response tailored to the user's question
    and available context. Depending on the query, this may include:
    """
)

st.markdown(
    """
    - Applicable SOP and pathway
    - Recommended next steps
    - Roles and responsibilities
    - Clearance requirements
    - SLA / timelines
    - Exceptions or considerations
    - Relevant source-slide references
    """
)


# ============================================================
# 2. SOP Knowledge Sources
# ============================================================

st.markdown(
    '<div class="section-title">SOP Knowledge Sources</div>',
    unsafe_allow_html=True,
)

st.write(
    """
    The chatbot uses two approved Healthcare Financing communications
    SOPs as its primary knowledge source. Both SOPs are maintained
    within a structured JSON knowledge source so that the chatbot can
    distinguish between their different workflows, decision rules, roles,
    clearances and timelines.
    """
)


st.divider()

# ============================================================
# 3. Use Case 1
# ============================================================

st.markdown(
    '<div class="section-title">Use Case 1 — SOP Guidance & Scenario Assessment</div>',
    unsafe_allow_html=True,
)

st.write(
    """
    This use case is designed for users who have a specific situation
    in mind but may not know whether an SOP applies, which SOP is
    relevant, which pathway to follow, or what they should do next.
    """
)

st.markdown(
    '<div class="subsection-title">Example</div>',
    unsafe_allow_html=True,
)

st.info(
    """
    **"We have a new website page that needs to be published for a
    Healthcare Financing scheme. Does the SOP apply, which pathway
    should we follow, and what do we need to do?"**
    """
)

st.markdown(
    '<div class="subsection-title">Process Flow</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
```mermaid
flowchart TD
    A[User describes a scenario] --> B[Understand intent and context]
    B --> C[Identify relevant SOP]
    C --> D[Identify relevant workflow or pathway]
    D --> E[Retrieve relevant SOP information]
    E --> F[Apply SOP to user's scenario]
    F --> G[Apply selected persona]
    G --> H[Generate grounded guidance]
    H --> I[Return response with source references]
"""
)

st.markdown(
'<div class="subsection-title">What this use case provides</div>',
unsafe_allow_html=True,
)

st.write(
"""
The chatbot moves beyond simply answering what the SOP says.
It applies the relevant workflow to the user's specific situation
and provides practical guidance on what to do next.
"""
)

st.markdown(
    """
    **Typical response components:**

    - Applicable SOP
    - Relevant pathway
    - Recommended next steps
    - Roles and clearances
    - Applicable SLA / timeline
    - Relevant source references
    """
)


# ============================================================
# 4. Use Case 2
# ============================================================

st.markdown(
    '<div class="section-title">Use Case 2 — Contextualised Search with Uploaded Documents</div>',
    unsafe_allow_html=True,
)

st.write(
    """
    This use case allows users to provide their own documents when
    additional context is needed. The chatbot can consider the
    uploaded material alongside the relevant SOP information when
    generating its response.
    """
)

st.markdown(
    '<div class="subsection-title">Examples</div>',
    unsafe_allow_html=True,
)

st.info(
    """
    **"Here is the draft website page. Does it need to follow the
    SOP and what clearance is required?"**
    """
)

st.markdown(
    '<div class="subsection-title">Process Flow</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
```mermaid
flowchart TD
    A[User asks a question] --> B[Upload PDF document]
    B --> C[Process and split document]
    C --> D[Retrieve relevant document information]
    D --> E[Retrieve relevant SOP information, where applicable]
    E --> F[Combine document and SOP context]
    F --> G[Apply selected persona]
    G --> H[Generate contextualised response]
    H --> I[Display answer with relevant references]
    """
)

st.markdown(
'<div class="subsection-title">How uploaded documents enhance the response</div>',
unsafe_allow_html=True,
)

st.write(
    """
    Uploaded documents provide additional context that may not be
    available from the user's question alone. For example, a user
    could upload a draft webpage, media material, email or briefing
    document and ask how the relevant SOP applies to it.
    """
)

st.divider()

# ============================================================
# 5. Response Personas
# ============================================================

st.markdown(
    '<div class="section-title">Response Personas</div>',
    unsafe_allow_html=True,
)

st.write(
    """
    Users can select a persona depending on the type of assistance
    they need. The persona influences how the guidance is presented,
    while the underlying SOP requirements remain unchanged.
    """
)

persona_col1, persona_col2, persona_col3 = st.columns(3)

with persona_col1:

    with st.container(border=True):

        st.markdown("### 🧭 SOP Navigator")

        st.write(
            """
            Helps users understand the applicable pathway and
            workflow.
            """
        )


with persona_col2:

    with st.container(border=True):

        st.markdown("### 💬 Comms Advisor")

        st.write(
            """
            Helps users apply the SOP to their specific situation
            and provides practical guidance.
            """
        )


with persona_col3:

    with st.container(border=True):

        st.markdown("### ✅ SOP Checker")

        st.write(
            """
            Reviews a proposed approach against the SOP and
            highlights potential gaps.
            """
        )


# ============================================================
# 6. Implementation
# ============================================================

st.markdown(
    '<div class="section-title">Implementation</div>',
    unsafe_allow_html=True,
)

st.write(
    """
    The chatbot was developed in **Visual Studio Code** using Python
    and **Streamlit** as the application framework. The SOP knowledge
    is maintained as a structured JSON file, while the RAG logic in
    `rag.py` retrieves and processes relevant SOP information alongside
    user-provided context. The application is deployed through
    Streamlit to provide an interactive web-based chatbot interface.
    """
)


# ============================================================
# 7. Grounding & Response Reliability
# ============================================================

st.markdown(
    '<div class="section-title">Grounding & Response Reliability</div>',
    unsafe_allow_html=True,
)

st.write(
    """
    The chatbot is designed to ground its responses in the approved
    SOP knowledge sources and any relevant user-provided documents.
    Where the available information is insufficient to determine a
    workflow, requirement or timeline, the chatbot should indicate
    the limitation rather than inventing an answer.
    """
)

# ============================================================
# Important Note
# ============================================================

st.markdown(
    '<div class="section-title">Important Note</div>',
    unsafe_allow_html=True,
)

st.info(
    """
    The SOP Assistant is an AI-assisted tool and should be used as
    a guide rather than a replacement for the approved SOPs or
    relevant stakeholder clearance.

    If a situation is ambiguous or the available SOPs do not provide
    enough information, users should verify the matter with CPF-HPD-SSE.
    """
)

# ============================================================
# Footer
# ============================================================

st.markdown(
    """
    <div class="footer">
        <strong>Healthcare Financing SOP Assistant</strong><br>
        CPFB-MOH Healthcare Financing Communications Workflows
    </div>
    """,
    unsafe_allow_html=True,
)