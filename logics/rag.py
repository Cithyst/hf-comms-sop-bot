"""
CPFB-MOH Healthcare Financing Comms Workflow SOP RAG.

Supports two related but distinct SOPs:

1. 2024 Healthcare Financing Comms Sharing SOP
   "Workflow for Sharing of Healthcare Financing Comms Materials btw CPFB & MOH"

2. 2025 Healthcare Financing Media Materials SOP
   "Workflow for Preparation & Issuance of Media Materials for Healthcare
   Financing Schemes"

The chatbot first determines which SOP applies to the user's situation,
then identifies the relevant pathway within that SOP.

The bot uses ONLY the approved combined SOP JSON in the Data folder.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from openai import OpenAI


BASE_DIR = Path(__file__).resolve().parent.parent
SOP_FILE = BASE_DIR / "data" / "healthcare_comms_sops.json"
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


# ----------------------------- Loading -----------------------------

def load_sop() -> Dict[str, Any]:
    if not SOP_FILE.exists():
        raise FileNotFoundError(
            f"SOP file not found: {SOP_FILE}. "
            "Place healthcare_comms_sops.json inside the data folder."
        )

    with SOP_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


SOP_DATA = load_sop()


def get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")

    return OpenAI(api_key=api_key)


# ----------------------------- Helpers -----------------------------

def normalise(text: str) -> str:
    text = text.lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9\s/-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def contains_any(text: str, phrases: List[str]) -> bool:
    text = normalise(text)
    return any(normalise(p) in text for p in phrases)


OPERATION_SIGNALS = [
    "operation-related",
    "operations-related",
    "operational matter",
    "operational matters",
    "administration of healthcare schemes",
    "service staff",
    "member interaction",
    "cpf service",
    "cpf staff",
    "cpf-mpd",
    "cpfb operational",
]

POLICY_SIGNALS = [
    "policy-related",
    "policy related",
    "policy announcement",
    "policy announcements",
    "scheme change",
    "scheme changes",
    "medishield life review",
    "policy matter",
    "policy matters",
]

JOINT_SIGNALS = [
    "joint",
    "jointly developed",
    "co-developed",
    "co developed",
    "cpfb and moh jointly",
    "moh and cpfb jointly",
    "joint product",
    "joint products",
]

CPFB_INPUT_SIGNALS = [
    "cpfb input",
    "cpfb inputs",
    "cpfb hfg input",
    "cpfb hfg inputs",
    "hfg input",
    "hfg inputs",
    "needs cpfb",
    "need cpfb",
    "requires cpfb",
    "require cpfb",
    "seeks cpfb input",
    "seeking cpfb input",
    "cpf inputs",
]

MEDIA_SIGNALS = [
    "media query",
    "media queries",
    "press release",
    "press releases",
    "journalist",
    "journalists",
    "media outlet",
    "media outlets",
    "interview request",
    "interview requests",
    "podcast",
    "broadcast",
    "media factsheet",
    "media factsheets",
    "anticipated media query",
    "anticipated media queries",
]

DRUMS_SIGNALS = [
    "drums",
    "mistruth",
    "mistruths",
    "false information on social media",
    "member post on social media",
    "member posts on social media",
]

SLA_SIGNALS = [
    "sla",
    "timeline",
    "turnaround time",
    "how long",
    "deadline",
    "time needed",
    "time required",
]


# Signals that strongly point to the 2024 Healthcare Financing Comms
# Sharing SOP rather than the 2025 Media Materials Preparation & Issuance SOP.
COMMS_SHARING_2024_SIGNALS = [
    "cpf website",
    "cpf website update",
    "cpf website changes",
    "cshl website",
    "website contents",
    "static contents",
    "static content",
    "faqs",
    "faq",
    "eDM",
    "edm",
    "digital notification",
    "digital notifications",
    "hardcopy notification",
    "hardcopy notifications",
    "hardcopy collateral",
    "hardcopy collaterals",
    "digital collateral",
    "digital collaterals",
    "social media post",
    "social media posts",
    "website hosting",
    "cpfb comms channels",
    "cpf comms channels",
    "comms materials requiring changes",
    "moh-generated comms materials",
    "comms material sharing",
    "comms materials sharing",
    "comms sharing",
    "sharing of healthcare financing comms materials",
]

MEDIA_2025_SIGNALS = MEDIA_SIGNALS + [
    "preparation and issuance",
    "preparation of media materials",
    "issuance of media materials",
    "media materials",
    "media material",
    "press release",
    "journalist",
    "interview request",
    "podcast",
    "broadcast",
    "media factsheet",
]


# --------------------------- Classification ------------------------

def keyword_scores(query: str) -> Dict[str, int]:
    text = normalise(query)

    return {
        "operation_related": sum(
            normalise(x) in text
            for x in OPERATION_SIGNALS
        ),
        "policy_related": sum(
            normalise(x) in text
            for x in POLICY_SIGNALS
        ),
        "joint": sum(
            normalise(x) in text
            for x in JOINT_SIGNALS
        ),
    }


def strong_keyword_category(
    query: str,
) -> Optional[str]:

    scores = keyword_scores(query)

    highest = max(scores.values())

    if highest == 0:
        return None

    winners = [
        key
        for key, value in scores.items()
        if value == highest
    ]

    if len(winners) != 1:
        return None

    if (
        winners[0] == "policy_related"
        and highest == 1
    ):
        text = normalise(query)

        strong_policy_terms = [
            "policy announcement",
            "policy-related",
            "policy related",
            "scheme change",
            "scheme changes",
            "medishield life review",
        ]

        if not any(
            x in text
            for x in strong_policy_terms
        ):
            return None

    return winners[0]


def llm_classify(
    query: str,
) -> Dict[str, Any]:
    """Use the LLM when deterministic classification is ambiguous.

    The first decision is which of the two approved SOPs applies. The
    second decision identifies the pathway within that SOP.
    """

    client = get_client()

    prompt = f"""
Classify this question using ONLY the two approved CPFB-MOH Healthcare
Financing SOPs supplied to the chatbot.

There are TWO DISTINCT SOPs:

SOP A - 2024 Healthcare Financing Comms Sharing SOP:
"Workflow for Sharing of Healthcare Financing Comms Materials btw CPFB & MOH"
Use this when the question is about sharing, updating, clearing, creating
or disseminating healthcare financing communications materials on CPFB
channels, including CPF/CSHL websites, FAQs, static contents, notifications,
collaterals, infographics, social posts, eDMs and videos. It also covers
MOH-generated communications materials that do not require changes on CPFB
channels.

SOP B - 2025 Healthcare Financing Media Materials SOP:
"Workflow for Preparation & Issuance of Media Materials for Healthcare
Financing Schemes"
Use this when the question concerns preparation/issuance of MEDIA MATERIALS,
including media queries, press releases, journalists, interviews, podcasts,
broadcasts and media factsheets, and the operation-related, policy-related
and joint pathways.

IMPORTANT:
- Do NOT choose the 2025 SOP merely because a healthcare scheme is mentioned.
- A question about a CPF/CSHL website, FAQ, static content, eDM, social post,
  notification or CPFB comms-channel update normally belongs to the 2024 SOP.
- A media query, journalist, press release, interview, podcast, broadcast or
  media factsheet normally belongs to the 2025 SOP.
- If the question is ambiguous, choose "ambiguous" and explain what needs
  clarification rather than guessing.
- If the user asks about a general concept common to both SOPs, choose the SOP
  that best matches the concrete scenario; if there is no scenario, choose
  "ambiguous".

For SOP A, choose one pathway:
- "2024_general_cpf_channel_change"
- "2024_one_hfg_department"
- "2024_multiple_hfg_departments"
- "2024_cpfb_triggered_social_media"
- "2024_moh_generated_no_cpf_channel_change"
- "2024_general"

For SOP B, choose one pathway:
- "operation_related"
- "policy_related"
- "joint"
- "general"

Also identify:
1. Whether CPFB inputs are explicitly required.
2. Whether the case may be covered by DRUMS or another existing SOP.
3. Whether the user asks about SLA/timing.

Return ONLY valid JSON:
{{
  "sop": "2024_hf_comms_sharing|2025_media_materials_preparation_issuance|ambiguous",
  "pathway": "2024_general_cpf_channel_change|2024_one_hfg_department|2024_multiple_hfg_departments|2024_cpfb_triggered_social_media|2024_moh_generated_no_cpf_channel_change|2024_general|operation_related|policy_related|joint|general",
  "cpfb_inputs_required": true,
  "possible_existing_sop": false,
  "sla_question": false,
  "reason": "short reason",
  "clarification_needed": ""
}}

Question:
{query}
"""

    response = client.responses.create(
        model=MODEL,
        instructions=(
            "Return only valid JSON. "
            "No markdown fences."
        ),
        input=prompt,
    )

    raw = response.output_text.strip()

    raw = re.sub(
        r"^```(?:json)?\s*",
        "",
        raw,
    )

    raw = re.sub(
        r"\s*```$",
        "",
        raw,
    )

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {}

    sop = result.get("sop", "ambiguous")
    if sop not in {
        "2024_hf_comms_sharing",
        "2025_media_materials_preparation_issuance",
        "ambiguous",
    }:
        sop = "ambiguous"

    valid_pathways = {
        "2024_general_cpf_channel_change",
        "2024_one_hfg_department",
        "2024_multiple_hfg_departments",
        "2024_cpfb_triggered_social_media",
        "2024_moh_generated_no_cpf_channel_change",
        "2024_general",
        "operation_related",
        "policy_related",
        "joint",
        "general",
    }

    pathway = result.get("pathway", "general")
    if pathway not in valid_pathways:
        pathway = "general"

    if sop == "ambiguous":
        pathway = "general"

    return {
        "sop": sop,
        "category": pathway,
        "pathway": pathway,
        "cpfb_inputs_required": bool(
            result.get(
                "cpfb_inputs_required",
                contains_any(query, CPFB_INPUT_SIGNALS),
            )
        ),
        "possible_existing_sop": bool(
            result.get(
                "possible_existing_sop",
                contains_any(query, DRUMS_SIGNALS),
            )
        ),
        "sla_question": bool(
            result.get(
                "sla_question",
                contains_any(query, SLA_SIGNALS),
            )
        ),
        "reason": result.get("reason", ""),
        "clarification_needed": result.get(
            "clarification_needed",
            "",
        ),
    }


def _score_sop_keywords(query: str) -> Dict[str, int]:
    text = normalise(query)

    return {
        "2024_hf_comms_sharing": sum(
            normalise(x) in text
            for x in COMMS_SHARING_2024_SIGNALS
        ),
        "2025_media_materials_preparation_issuance": sum(
            normalise(x) in text
            for x in MEDIA_2025_SIGNALS
        ),
    }


def _deterministic_sop(query: str) -> Optional[str]:
    scores = _score_sop_keywords(query)
    highest = max(scores.values())

    if highest == 0:
        return None

    winners = [
        key for key, value in scores.items()
        if value == highest
    ]

    if len(winners) != 1:
        return None

    # Require a reasonably strong signal before making the SOP decision
    # without the LLM.
    if highest < 1:
        return None

    return winners[0]


def classify_query(
    query: str,
) -> Dict[str, Any]:

    sop = _deterministic_sop(query)

    # If the wording clearly points to one SOP, retain the fast deterministic
    # behaviour. For the 2025 SOP we can also retain the existing pathway
    # keyword classifier.
    if sop == "2025_media_materials_preparation_issuance":
        category = strong_keyword_category(query)

        if category:
            return {
                "sop": sop,
                "category": category,
                "pathway": category,
                "cpfb_inputs_required": contains_any(
                    query,
                    CPFB_INPUT_SIGNALS,
                ),
                "possible_existing_sop": contains_any(
                    query,
                    DRUMS_SIGNALS,
                ),
                "sla_question": contains_any(
                    query,
                    SLA_SIGNALS,
                ),
                "reason": (
                    "2025 Media Materials SOP identified from "
                    "clear media-workflow terminology."
                ),
            }

    # For 2024, ask the LLM for the exact workflow because the SOP contains
    # several different CPFB-channel pathways.
    # For ambiguous cases, the LLM decides which SOP applies.
    result = llm_classify(query)

    return result


# ------------------------------ Retrieval ---------------------------

def get_selected_sop(
    sop_id: str,
) -> Dict[str, Any]:
    return (
        SOP_DATA
        .get("sops", {})
        .get(sop_id, {})
    )


def category_definition(
    category: str,
) -> Optional[Dict[str, Any]]:

    sop = get_selected_sop(
        "2025_media_materials_preparation_issuance"
    )

    categories = (
        sop
        .get("slides", {})
        .get("4", {})
        .get("categories", [])
    )

    return next(
        (
            x
            for x in categories
            if x.get("id") == category
        ),
        None,
    )


def high_level_workflow(
    category: str,
) -> Optional[Dict[str, Any]]:

    sop = get_selected_sop(
        "2025_media_materials_preparation_issuance"
    )

    workflows = (
        sop
        .get("slides", {})
        .get("7", {})
        .get("workflows", [])
    )

    return next(
        (
            x
            for x in workflows
            if x.get("id") == category
        ),
        None,
    )


def detailed_workflow(
    category: str,
) -> Optional[Dict[str, Any]]:

    sop = get_selected_sop(
        "2025_media_materials_preparation_issuance"
    )

    slide_map = {
        "operation_related": "9",
        "policy_related": "11",
        "joint": "13",
    }

    slide = slide_map.get(category)

    return (
        sop
        .get("slides", {})
        .get(slide)
        if slide
        else None
    )


def relevant_roles(
    category: str,
) -> List[Dict[str, Any]]:

    sop = get_selected_sop(
        "2025_media_materials_preparation_issuance"
    )

    roles = sop.get(
        "roles",
        [],
    )

    if category == "operation_related":
        wanted = [
            "CPF-MPD",
            "CPF-SSE",
            "CPF-HID / CPF-HCP",
        ]
    else:
        wanted = [
            "MOH-CommsD",
            "MOH-HF",
            "CPF-MPD",
            "CPF-SSE",
            "CPF-HID / CPF-HCP",
        ]

    result = []

    for role in roles:
        party = normalise(
            role.get(
                "party",
                "",
            )
        )

        if any(
            normalise(w) in party
            or party in normalise(w)
            for w in wanted
        ):
            result.append(role)

    return result


def retrieve_2024_context(
    query: str,
    classification: Dict[str, Any],
) -> Dict[str, Any]:
    """Retrieve the relevant parts of the 2024 comms-sharing SOP."""

    sop = get_selected_sop(
        "2024_hf_comms_sharing"
    )

    pathway = classification.get(
        "pathway",
        "2024_general",
    )

    context = {
        "sop": {
            "id": sop.get("document_id"),
            "title": sop.get("title"),
            "short_title": sop.get("short_title"),
            "status": sop.get("status"),
            "updated_as_at": sop.get("updated_as_at"),
            "scope": sop.get("scope"),
        },
        "query": query,
        "classification": classification,
        "decision_framework": sop.get(
            "decision_framework",
            {},
        ),
        "materials": sop.get(
            "materials",
            {},
        ),
        "clearance_rules": sop.get(
            "clearance_rules",
            {},
        ),
        "content_ownership": sop.get(
            "content_ownership",
            {},
        ),
        "sla_summary": sop.get(
            "sla_summary",
            {},
        ),
        "bot_instructions": sop.get(
            "bot_instructions",
            {},
        ),
    }

    workflows = sop.get(
        "workflows",
        {},
    )

    workflow_key = {
        "2024_general_cpf_channel_change":
            "general_cpf_channel_change",
        "2024_one_hfg_department":
            "one_hfg_department",
        "2024_multiple_hfg_departments":
            "multiple_hfg_departments",
        "2024_cpfb_triggered_social_media":
            "cpfb_triggered_social_media",
        "2024_moh_generated_no_cpf_channel_change":
            "moh_generated_no_cpf_channel_change",
    }.get(pathway)

    if workflow_key:
        context["selected_workflow"] = workflows.get(
            workflow_key
        )

    # If the exact pathway is uncertain, provide all pathway names and their
    # decision logic, rather than inventing a workflow.
    if pathway == "2024_general":
        context["workflow_options"] = workflows

    # The 2024 JSON stores the source references separately from individual
    # workflow objects, so retain them for answer citation.
    context["source_slides"] = sop.get(
        "source_slides",
        [],
    )

    return context


def retrieve_2025_context(
    query: str,
    classification: Dict[str, Any],
) -> Dict[str, Any]:
    """Retrieve the relevant parts of the 2025 media-materials SOP."""

    sop = get_selected_sop(
        "2025_media_materials_preparation_issuance"
    )

    category = classification.get(
        "category",
        "general",
    )

    context: Dict[str, Any] = {
        "sop": sop.get(
            "document",
            {},
        ),
        "query": query,
        "classification": classification,
        "media_material_definition": (
            sop
            .get("slides", {})
            .get("3", {})
        ),
        "sla": sop.get(
            "sla",
            {},
        ),
        "decision_rules": sop.get(
            "decision_rules",
            [],
        ),
        "exceptions_and_notes": sop.get(
            "exceptions_and_notes",
            [],
        ),
        "bot_answering_guidance": sop.get(
            "bot_answering_guidance",
            {},
        ),
    }

    if category in {
        "operation_related",
        "policy_related",
        "joint",
    }:

        context["decision_rule"] = (
            category_definition(category)
        )

        context["high_level_workflow"] = (
            high_level_workflow(category)
        )

        context["detailed_workflow"] = (
            detailed_workflow(category)
        )

        context["relevant_roles"] = (
            relevant_roles(category)
        )

    else:

        context["decision_framework"] = (
            sop
            .get("slides", {})
            .get("4", {})
        )

        context["overarching_roles"] = (
            sop
            .get("slides", {})
            .get("5", {})
        )

        context["roles"] = sop.get(
            "roles",
            [],
        )

    return context


# ------------------------------ Retrieval ---------------------------

def category_definition(
    category: str,
) -> Optional[Dict[str, Any]]:

    categories = (
        SOP_DATA
        .get("slides", {})
        .get("4", {})
        .get("categories", [])
    )

    return next(
        (
            x
            for x in categories
            if x.get("id") == category
        ),
        None,
    )


def high_level_workflow(
    category: str,
) -> Optional[Dict[str, Any]]:

    workflows = (
        SOP_DATA
        .get("slides", {})
        .get("7", {})
        .get("workflows", [])
    )

    return next(
        (
            x
            for x in workflows
            if x.get("id") == category
        ),
        None,
    )


def detailed_workflow(
    category: str,
) -> Optional[Dict[str, Any]]:

    slide_map = {
        "operation_related": "9",
        "policy_related": "11",
        "joint": "13",
    }

    slide = slide_map.get(category)

    return (
        SOP_DATA
        .get("slides", {})
        .get(slide)
        if slide
        else None
    )


def relevant_roles(
    category: str,
) -> List[Dict[str, Any]]:

    roles = SOP_DATA.get(
        "roles",
        [],
    )

    if category == "operation_related":
        wanted = [
            "CPF-MPD",
            "CPF-SSE",
            "CPF-HID / CPF-HCP",
        ]
    else:
        wanted = [
            "MOH-CommsD",
            "MOH-HF",
            "CPF-MPD",
            "CPF-SSE",
            "CPF-HID / CPF-HCP",
        ]

    result = []

    for role in roles:
        party = normalise(
            role.get(
                "party",
                "",
            )
        )

        if any(
            normalise(w) in party
            or party in normalise(w)
            for w in wanted
        ):
            result.append(role)

    return result


# ============================================================================
# Uploaded Document Retrieval
# ============================================================================

def retrieve_uploaded_document_context(
    query: str,
    uploaded_vectorstore: Any = None,
    uploaded_filenames: Optional[List[str]] = None,
    k: int = 4,
) -> Dict[str, Any]:
    """
    Retrieve relevant chunks from the uploaded PDF vectorstore.

    The vectorstore is created by Chatbot.py. It is optional and does
    not replace the approved SOP knowledge base.
    """

    if uploaded_vectorstore is None:
        return {
            "active": False,
            "filenames": uploaded_filenames or [],
            "chunks": [],
        }

    try:
        documents = uploaded_vectorstore.similarity_search(
            query,
            k=k,
        )

    except Exception as exc:
        print(
            f"[SOP BOT] Uploaded document retrieval error: {exc}"
        )

        return {
            "active": True,
            "filenames": uploaded_filenames or [],
            "chunks": [],
            "error": (
                "The uploaded document could not be searched."
            ),
        }

    chunks = []

    for index, document in enumerate(
        documents,
        start=1,
    ):

        metadata = getattr(
            document,
            "metadata",
            {},
        ) or {}

        page = metadata.get(
            "page",
        )

        if page is None:
            page = metadata.get(
                "page_number",
            )

        chunks.append(
            {
                "chunk": index,
                "content": getattr(
                    document,
                    "page_content",
                    "",
                ),
                "source_file": (
                    metadata.get("source")
                    or metadata.get("file_name")
                    or metadata.get("filename")
                    or "Uploaded document"
                ),
                "page": page,
            }
        )

    return {
        "active": True,
        "filenames": uploaded_filenames or [],
        "chunks": chunks,
    }


def retrieve_context(
    query: str,
    classification: Dict[str, Any],
    uploaded_vectorstore: Any = None,
    uploaded_filenames: Optional[List[str]] = None,
) -> Dict[str, Any]:

    sop_id = classification.get(
        "sop",
        "ambiguous",
    )

    if sop_id == "2024_hf_comms_sharing":
        context = retrieve_2024_context(
            query,
            classification,
        )

    elif sop_id == "2025_media_materials_preparation_issuance":
        context = retrieve_2025_context(
            query,
            classification,
        )

    else:
        # Ambiguous questions receive a compact comparison of both SOPs so
        # the LLM can explain the distinction or ask a targeted clarification.
        sop_2024 = get_selected_sop(
            "2024_hf_comms_sharing"
        )
        sop_2025 = get_selected_sop(
            "2025_media_materials_preparation_issuance"
        )

        context = {
            "query": query,
            "classification": classification,
            "sop_selection_status": "ambiguous",
            "two_sop_distinction": {
                "2024": {
                    "title": sop_2024.get("title"),
                    "scope": sop_2024.get("scope"),
                    "decision_framework": sop_2024.get(
                        "decision_framework",
                        {},
                    ),
                    "materials": sop_2024.get(
                        "materials",
                        {},
                    ),
                },
                "2025": {
                    "title": sop_2025
                    .get("document", {})
                    .get("title"),
                    "scope": sop_2025
                    .get("document", {})
                    .get("scope"),
                    "decision_rules": sop_2025.get(
                        "decision_rules",
                        [],
                    ),
                },
            },
        }

    if classification.get(
        "possible_existing_sop"
    ):

        context["existing_sop_warning"] = (
            "The 2025 Media Materials SOP states that other SOPs already "
            "exist, including DRUMS for mistruths involving members who "
            "post on social media. The 2024 Comms Sharing SOP should also "
            "not be assumed to replace other applicable approved SOPs."
        )

    # Uploaded document is optional additional context.
    context["uploaded_document"] = (
        retrieve_uploaded_document_context(
            query=query,
            uploaded_vectorstore=uploaded_vectorstore,
            uploaded_filenames=uploaded_filenames,
            k=4,
        )
    )

    return context


# -------------------------- Source references -----------------------

def extract_source_slides(
    context: Dict[str, Any],
) -> List[int]:

    slides: List[int] = []

    def walk(value: Any) -> None:

        if isinstance(value, dict):

            for key, item in value.items():

                if (
                    key == "source_slide"
                    and isinstance(item, int)
                ):
                    slides.append(item)

                elif (
                    key == "source_slides"
                    and isinstance(item, list)
                ):
                    slides.extend(
                        x
                        for x in item
                        if isinstance(x, int)
                    )

                walk(item)

        elif isinstance(value, list):

            for item in value:
                walk(item)

    walk(context)

    return sorted(
        set(slides)
    )


def format_context(
    context: Dict[str, Any],
) -> str:

    return json.dumps(
        context,
        indent=2,
        ensure_ascii=False,
    )


# ---------------------------- Generation ----------------------------

SYSTEM_PROMPT = """
You are the CPFB-MOH Healthcare Financing Comms and Media Workflow SOP Assistant.

There are TWO DISTINCT approved SOPs in the supplied knowledge base:

1. 2024 Healthcare Financing Comms Sharing SOP:
   "Workflow for Sharing of Healthcare Financing Comms Materials btw CPFB & MOH"

2. 2025 Healthcare Financing Media Materials SOP:
   "Workflow for Preparation & Issuance of Media Materials for Healthcare
   Financing Schemes"

The 2024 SOP covers healthcare financing communications materials and
workflows involving CPFB communications channels, including website contents,
FAQs, static contents, notifications, collaterals, infographics, social media,
eDMs and videos. It also covers MOH-generated comms materials that do not
require changes on CPFB comms channels.

The 2025 SOP covers preparation and issuance of media materials, including
operation-related, policy-related and joint pathways, as well as media
queries, press releases, interviews, podcasts, broadcasts and media
factsheets.

Your first responsibility is to apply the CORRECT SOP. Do not mix the
workflows of the two SOPs.

If the context says the SOP selection is ambiguous:
- explain the distinction between the two SOPs;
- ask a targeted clarification question if one is needed;
- do not invent a pathway.

For the 2024 SOP:
- Determine whether the material requires changes on CPFB comms channels.
- Where relevant, distinguish one-HFG-department, multiple-HFG-department,
  CPFB-triggered social media, and MOH-generated materials without CPFB
  channel changes.
- Use the 2024 SOP's actual clearance rules, content ownership, workflows
  and material-specific SLA.
- The 2024 SOP contains numerical SLA values for specified material types.
  Do not replace those with a generic "no fixed SLA" statement.

For the 2025 SOP:
- Operation-related: operational matters related to administration of
  healthcare schemes by CPFB. CPFB is the rightful owner/preparer and issuer.
- Policy-related: policy announcements on financing schemes concerning CPFB.
  MOH is the rightful owner/preparer and issuer.
- Joint: products/materials jointly developed by MOH and CPFB.
- If CPFB inputs are required for a policy-related item, use the detailed
  policy workflow.
- The 2025 SOP does NOT provide a fixed numerical SLA. The responsible party
  preparing the media materials establishes the required SLA/timeline with
  relevant parties before the workflow begins.
- A scheme name alone does not determine the 2025 pathway.
- If the case may be covered by an existing SOP such as DRUMS, flag this.

GROUNDING RULES:
- Use the selected approved SOP as the authoritative source for workflow,
  responsibilities, approvals, timelines and exceptions.
- Never invent responsibilities, stakeholders, approval levels, deadlines or
  exceptions.
- Do not silently reconcile differences between the two SOPs.
- If the two SOPs contain different rules, keep them attributed to the
  correct SOP.
- Do not use outside knowledge to fill gaps in the approved SOP.
- Cite the relevant original source slide number(s) where available.
- If the source does not support an answer, say so.

UPLOADED DOCUMENT RULES:
- If an uploaded document is active, use its retrieved chunks when relevant.
- Treat it as additional user-provided context.
- Do not assume it overrides either approved SOP.
- If it conflicts with an approved SOP, explicitly flag the conflict.
- Do not claim information is in the uploaded document unless it appears in
  the retrieved chunks.

RESPONSE STYLE:
Write in a helpful and conversational way.

Do not sound like a rigid rulebook.

A useful structure is:

- Short answer
- Applicable SOP
- Why it applies
- Relevant workflow/pathway
- Key stakeholders/approvals
- SLA/timing
- Exceptions or related SOPs
- Source slides

Use short bullets or numbered steps where useful.

For broad questions, answer naturally and practically.

Do not force a rigid template when a more natural explanation is better.

For simple questions, answer directly. Do not force a template.
"""



def generate_answer(
    query: str,
    context: Dict[str, Any],
    source_slides: List[int],
    chat_history: Optional[
        List[Dict[str, str]]
    ] = None,
) -> str:

    client = get_client()

    history = ""

    if chat_history:

        history = (
            "\nRECENT CONVERSATION:\n"
        )

        for message in chat_history[-6:]:

            history += (
                f"{message.get('role', 'user').upper()}: "
                f"{message.get('content', '')}\n"
            )

    sources = ""

    if source_slides:

        sources = (
            "Relevant approved SOP source slides retrieved: "
            + ", ".join(
                f"Slide {x}"
                for x in source_slides
            )
            + "."
        )

    uploaded = context.get(
        "uploaded_document",
        {},
    )

    if uploaded.get("active"):

        uploaded_files = uploaded.get(
            "filenames",
            [],
        )

        uploaded_note = (
            "An uploaded document is active. "
            "Relevant retrieved chunks are included "
            "in the context below."
        )

        if uploaded_files:

            uploaded_note += (
                " Active uploaded file(s): "
                + ", ".join(uploaded_files)
                + "."
            )

    else:

        uploaded_note = (
            "No uploaded document is active."
        )

    prompt = f"""
USER QUESTION:
{query}

{history}

APPROVED SOP CONTEXT:
{format_context(context)}

{sources}

UPLOADED DOCUMENT STATUS:
{uploaded_note}

Answer the user's question using the approved SOP context and, where
relevant, the retrieved uploaded-document context.

Do not invent information that is absent from the supplied context.
"""

    response = client.responses.create(
        model=MODEL,
        instructions=SYSTEM_PROMPT,
        input=prompt,
    )

    answer = response.output_text.strip()

    return (
        answer
        or "I could not find enough information in the supplied context "
        "to answer that."
    )


# ---------------------------- Public API ----------------------------

def answer_query(
    user_query: str,
    chat_history: Optional[
        List[Dict[str, str]]
    ] = None,
    uploaded_vectorstore: Any = None,
    uploaded_filenames: Optional[
        List[str]
    ] = None,
) -> str:
    """
    Main function called from Chatbot.py.

    uploaded_vectorstore:
        Optional Chroma vectorstore created from the user's uploaded PDF.

    uploaded_filenames:
        Optional list containing the uploaded file name(s).
    """

    if not user_query or not user_query.strip():

        return (
            "Please enter a question about the CPFB-MOH "
            "Healthcare Financing media workflow SOP."
        )

    try:

        query = user_query.strip()

        classification = classify_query(
            query,
        )

        context = retrieve_context(
            query,
            classification,
            uploaded_vectorstore=uploaded_vectorstore,
            uploaded_filenames=uploaded_filenames,
        )

        source_slides = extract_source_slides(
            context,
        )

        return generate_answer(
            query,
            context,
            source_slides,
            chat_history,
        )

    except FileNotFoundError as exc:

        print(
            f"[SOP BOT] {exc}"
        )

        return (
            "I could not find data/healthcare_comms_sops.json."
        )

    except RuntimeError as exc:

        print(
            f"[SOP BOT] {exc}"
        )

        return (
            "The chatbot is not configured correctly. "
            "Please check OPENAI_API_KEY."
        )

    except Exception as exc:

        print(
            f"[SOP BOT] Unexpected error: {exc}"
        )

        return (
            "Sorry, I encountered an issue while processing "
            "your question. Please try again."
        )


def classify_for_debug(
    user_query: str,
) -> Dict[str, Any]:

    classification = classify_query(
        user_query,
    )

    context = retrieve_context(
        user_query,
        classification,
    )

    return {
        "classification": classification,
        "source_slides": extract_source_slides(
            context
        ),
        "context": context,
    }