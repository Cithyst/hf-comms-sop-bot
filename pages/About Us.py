import streamlit as st


# ============================================================
# Page configuration
# ============================================================

st.set_page_config(
    page_title="About the SOP Assistant",
    page_icon="📘",
    layout="wide",
)


# ============================================================
# Custom styling
# ============================================================

st.markdown(
    """
    <style>

    /* Main page */
    .main {
        padding-top: 2rem;
    }

    /* Hero section */
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

    .hero h1 {
        color: white;
        font-size: 2.4rem;
        margin-bottom: 0.5rem;
    }

    .hero p {
        color: #e8f5f1;
        font-size: 1.1rem;
        line-height: 1.6;
        margin-bottom: 0;
    }

    /* Section headings */
    .section-title {
        color: #006b54;
        font-size: 1.35rem;
        font-weight: 700;
        margin-top: 2rem;
        margin-bottom: 0.6rem;
    }

    /* SOP cards */
    .sop-card {
        border-radius: 14px;
        padding: 1.4rem;
        height: 100%;
        border: 1px solid #dfe8e4;
        background: white;
    }

    .sop-card h3 {
        color: #006b54;
        margin-top: 0;
        margin-bottom: 0.4rem;
        font-size: 1.1rem;
    }

    .sop-label {
        display: inline-block;
        background: #e5f3ee;
        color: #006b54;
        font-size: 0.8rem;
        font-weight: 700;
        padding: 0.25rem 0.65rem;
        border-radius: 20px;
        margin-bottom: 0.7rem;
    }

    .sop-card p,
    .sop-card li {
        font-size: 0.95rem;
        line-height: 1.55;
        color: #333333;
    }

    .sop-card ul {
        padding-left: 1.2rem;
    }

    /* Simple feature text */
    .feature-title {
        color: #006b54;
        font-weight: 700;
        font-size: 1rem;
        margin-bottom: 0.2rem;
    }

    .feature-description {
        font-size: 0.95rem;
        line-height: 1.55;
        color: #333333;
        margin-bottom: 1rem;
    }

    /* Footer */
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
        <h1>📘 About the SOP Assistant</h1>
        <p>
            A conversational AI assistant designed to help users understand
            and navigate Healthcare Financing communications workflows
            between CPFB and MOH.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# What is this chatbot?
# ============================================================

st.markdown(
    '<div class="section-title">What is this chatbot?</div>',
    unsafe_allow_html=True,
)

st.write(
    """
    The Healthcare Financing SOP Assistant turns approved workflow
    documents into a conversational knowledge tool. Instead of
    searching through lengthy SOP documents manually, users can
    describe their situation in plain language and receive guidance
    on the relevant workflow, stakeholders, approvals and timelines.
    """
)

st.write(
    """
    You do not need to know which SOP applies before asking a question.
    Simply describe what you are trying to prepare, update, share or
    issue, and the assistant will help identify the relevant SOP and
    pathway.
    """
)

st.divider()

# ============================================================
# Project Scope
# ============================================================

st.markdown(
    '<div class="section-title">Project Scope</div>',
    unsafe_allow_html=True,
)

st.write(
    """
    The assistant currently supports two related but distinct
    Healthcare Financing communications SOPs. The chatbot determines
    which SOP is relevant based on the user's situation before
    providing workflow guidance.
    """
)

col1, col2 = st.columns(2)


with col1:

    st.markdown(
        """
        <div class="sop-card">

        <div class="sop-label">2024 SOP</div>

        <h3>📢 Healthcare Financing Comms Sharing</h3>

        <p>
        <strong>
        Workflow for Sharing of Healthcare Financing Comms Materials
        btw CPFB & MOH
        </strong>
        </p>

        <p>
        Covers the sharing, preparation, updating and dissemination
        of Healthcare Financing communications materials involving
        CPFB and MOH.
        </p>

        <strong>Examples include:</strong>

        <ul>
            <li>CPF and CSHL website content</li>
            <li>FAQs and static contents</li>
            <li>Notifications</li>
            <li>Social media materials</li>
            <li>eDMs and videos</li>
            <li>Communications collaterals</li>
            <li>Dissemination to CPFB frontliners</li>
        </ul>

        </div>
        """,
        unsafe_allow_html=True,
    )


with col2:

    st.markdown(
        """
        <div class="sop-card">

        <div class="sop-label">2025 SOP</div>

        <h3>📰 Media Materials</h3>

        <p>
        <strong>
        Workflow for Preparation & Issuance of Media Materials
        for Healthcare Financing Schemes
        </strong>
        </p>

        <p>
        Covers the preparation and issuance of Healthcare Financing
        media materials and related media workflows.
        </p>

        <strong>Examples include:</strong>

        <ul>
            <li>Press releases</li>
            <li>Media queries</li>
            <li>Media responses</li>
            <li>Journalist or media requests</li>
            <li>Interview requests</li>
            <li>Media-material preparation</li>
            <li>Media clearance and issuance</li>
        </ul>

        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# Objectives
# ============================================================

st.markdown(
    '<div class="section-title">Objectives</div>',
    unsafe_allow_html=True,
)

st.write(
    """
    The assistant is designed to make approved SOP guidance easier
    to access and apply in day-to-day work. It aims to:
    """
)

st.markdown(
    """
    - **Identify the relevant SOP** based on the user's specific situation.
    - **Guide users through the workflow** and applicable pathway.
    - **Clarify roles and responsibilities** of relevant teams and stakeholders.
    - **Highlight clearance requirements and timelines** where specified in the SOP.
    - **Support scenario-based questions** by allowing users to describe their situation in plain language.
    - **Reduce manual searching** through lengthy SOP documents.
    """
)

st.divider()

# ============================================================
# Data Sources
# ============================================================

st.markdown(
    '<div class="section-title">Data Sources</div>',
    unsafe_allow_html=True,
)

st.write(
    """
    The chatbot is grounded in structured versions of the approved
    SOP source materials. The two SOPs are maintained as separate
    knowledge sources so that their workflows, roles and timelines
    are not inadvertently mixed.
    """
)

st.markdown(
    "**Approved SOP sources**"
)

st.write(
    """
    - **2024 —** Structured source based on the *Workflow for Sharing of Healthcare
    Financing Comms Materials btw CPFB & MOH*.
    """
)

st.write(
    """
    - **2025 —** Structured source based on the *Workflow for Preparation
    & Issuance of Media Materials for Healthcare Financing Schemes*.
    """
)

st.markdown(
    "**Information captured from the SOPs**"
)

st.write(
    """
    - The structured sources contain workflow steps, decision rules,
    roles and responsibilities, clearance requirements, SLA and
    timeline information, exceptions and source-slide references.
    """
)

st.divider()

# ============================================================
# Key Features
# ============================================================

st.markdown(
    '<div class="section-title">Key Features</div>',
    unsafe_allow_html=True,
)

st.write(
    """
    The assistant is designed to help users find, understand and
    apply the relevant SOP guidance quickly and intuitively.
    """
)

features = [
    (
        "🔍 SOP Identification & Scenario-Based Guidance",
        "Determines which of the two SOPs is relevant to the user's "
        "context and whether the SOP applies to their situation."
    ),
    (
        "👥 Roles & Clearances",
        "Highlights relevant stakeholders, responsibilities and "
        "clearance requirements."
    ),
    (
        "⏱️ SLA Guidance",
        "Provides applicable timelines when they are specified in "
        "the source SOP."
    ),
    (
        "📑 Source References",
        "Responses can point users back to relevant source-slide "
        "references."
    ),
    (
        "🎭 Response Personas",
        "Users can choose between SOP Navigator, Comms Advisor and "
        "SOP Checker, depending on the type of assistance they need."
    ),
    (
        "⬇️ Conversation Export",
        "Users can download their conversation for reference or "
        "follow-up."
    ),
]


for title, description in features:

    with st.container(border=True):

        st.markdown(
            f"**{title}**"
        )

        st.write(
            description
        )


st.divider()

# ============================================================
# What can I ask?
# ============================================================

st.markdown(
    '<div class="section-title">What can I ask?</div>',
    unsafe_allow_html=True,
)

st.write(
    """
    You don't need to know which SOP applies before asking a question.
    Simply describe what you are trying to do and let the assistant
    help identify the relevant workflow. Here are some examples:
    """
)

examples = [
    (
        "🌐 Website / FAQ",
        "We need to update a CareShield Life FAQ on the CPF website. "
        "What workflow should we follow?"
    ),
    (
        "📰 Media",
        "MOH is preparing a press release about CareShield Life. "
        "What does CPFB need to do?"
    ),
    (
        "⏱️ SLA",
        "Is there an SLA for communicating new policy changes to "
        "CPFB frontliners? How long do we have to prepare the materials?"
    ),
    (
        "📢 Frontliners",
        "MOH has provided comms materials that need to be shared "
        "with CPFB frontliners. What should I do?"
    ),
]


# ------------------------------------------------------------
# Display examples in a 2 x 2 card layout
# ------------------------------------------------------------

for row_start in range(0, len(examples), 2):

    row_examples = examples[row_start:row_start + 2]

    columns = st.columns(2)

    for column, (title, question) in zip(
        columns,
        row_examples,
    ):

        with column:

            with st.container(border=True):

                st.markdown(
                    f"**{title}**"
                )

                st.write(
                    f"“{question}”"
                )

    if row_start + 2 < len(examples):

        st.write("")


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