"""
CPFB-MOH Healthcare Financing Media Workflow SOP RAG.

Loads data/media_workflow_sop.json, classifies the user's scenario,
retrieves only the relevant SOP pathway, and asks the LLM to produce a
grounded answer with source-slide references.
"""

from __future__ import annotations

import json
import os
import re
import streamlit as st
from pathlib import Path
from typing import Any, Dict, List, Optional

from openai import OpenAI

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


# ----------------------------- Loading -----------------------------

def resolve_sop_files() -> List[Path]:
    env_path = os.getenv("SOP_FILES")
    if env_path:
        candidates = [Path(p).expanduser() for p in env_path.split(os.pathsep) if p]
        found = [candidate for candidate in candidates if candidate.exists()]
        if found:
            return found

    candidates = [
        BASE_DIR / "Data" / "media_workflow_sop.json",
        BASE_DIR / "Data" / "workflow_sharing_hf_comms_2024.json",
    ]

    found = [candidate for candidate in candidates if candidate.exists()]
    if found:
        return found

    raise FileNotFoundError(
        "SOP files not found. Checked: "
        + ", ".join(str(c) for c in candidates)
        + ". Place the SOP JSON files inside the Data folder."
    )


SOP_FILES = resolve_sop_files()


def load_sop(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"SOP file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


SOP_DOCUMENTS = [load_sop(path) for path in SOP_FILES]
SOP_DATA = SOP_DOCUMENTS[0] if SOP_DOCUMENTS else {}


def sop_identifier(sop: Dict[str, Any]) -> str:
    title = (sop.get("document", {}).get("title") or "").lower()
    if "sharing" in title and "healthcare financing" in title:
        return "sharing_2024"
    if "preparation" in title and "issuance" in title:
        return "preparation_2025"
    return sop.get("document", {}).get("document_id", "unknown")


def build_sop_catalog() -> List[Dict[str, Any]]:
    catalog = []
    for sop in SOP_DOCUMENTS:
        catalog.append(
            {
                "id": sop_identifier(sop),
                "title": sop.get("document", {}).get("title", "SOP"),
                "sop": sop,
            }
        )
    return catalog


SOP_CATALOG = build_sop_catalog()


# ============================================================================
# OpenAI Client
# ============================================================================

def get_client() -> OpenAI:
    """Create the OpenAI client."""

    api_key = os.getenv("OPENAI_API_KEY")

    # Use Streamlit secrets when running on Streamlit Cloud
    if not api_key:
        api_key = st.secrets.get("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set."
        )

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
    "operation-related", "operations-related", "operational matter",
    "operational matters", "administration of healthcare schemes",
    "service staff", "member interaction", "cpf service", "cpf staff",
    "cpf-mpd", "cpfb operational",
]

POLICY_SIGNALS = [
    "policy-related", "policy related", "policy announcement",
    "policy announcements", "scheme change", "scheme changes",
    "medishield life review", "policy matter", "policy matters",
]

JOINT_SIGNALS = [
    "joint", "jointly developed", "co-developed", "co developed",
    "cpfb and moh jointly", "moh and cpfb jointly", "joint product",
    "joint products",
]

CPFB_INPUT_SIGNALS = [
    "cpfb input", "cpfb inputs", "cpfb hfg input", "cpfb hfg inputs",
    "hfg input", "hfg inputs", "needs cpfb", "need cpfb",
    "requires cpfb", "require cpfb", "seeks cpfb input",
    "seeking cpfb input", "cpf inputs",
]

MEDIA_SIGNALS = [
    "media query", "media queries", "press release", "press releases",
    "journalist", "journalists", "media outlet", "media outlets",
    "interview request", "interview requests", "podcast", "broadcast",
    "media factsheet", "media factsheets", "anticipated media query",
    "anticipated media queries",
]

DRUMS_SIGNALS = [
    "drums", "mistruth", "mistruths", "false information on social media",
    "member post on social media", "member posts on social media",
]

SLA_SIGNALS = [
    "sla", "timeline", "turnaround time", "how long", "deadline",
    "time needed", "time required",
]


def keyword_scores(query: str) -> Dict[str, int]:
    text = normalise(query)
    return {
        "operation_related": sum(normalise(x) in text for x in OPERATION_SIGNALS),
        "policy_related": sum(normalise(x) in text for x in POLICY_SIGNALS),
        "joint": sum(normalise(x) in text for x in JOINT_SIGNALS),
    }


def strong_keyword_category(query: str) -> Optional[str]:
    scores = keyword_scores(query)
    highest = max(scores.values())
    if highest == 0:
        return None

    winners = [k for k, v in scores.items() if v == highest]
    if len(winners) != 1:
        return None

    # Do not classify a question as policy-related merely because it says
    # "policy" once. A scheme name alone is also insufficient.
    if winners[0] == "policy_related" and highest == 1:
        text = normalise(query)
        strong_policy_terms = [
            "policy announcement", "policy-related", "policy related",
            "scheme change", "scheme changes", "medishield life review",
        ]
        if not any(x in text for x in strong_policy_terms):
            return None

    return winners[0]


# --------------------------- Classification ------------------------

def llm_classify(query: str) -> Dict[str, Any]:
    """Use the LLM only when deterministic classification is ambiguous."""
    client = get_client()

    prompt = f"""
Classify this question for the CPFB-MOH Healthcare Financing media workflow SOP.

Choose exactly one category:
- operation_related: operational matters concerning administration of healthcare
  schemes by CPFB, e.g. member interaction with CPFB service staff.
- policy_related: policy announcements on financing schemes concerning CPFB,
  e.g. scheme changes or MediShield Life review.
- joint: products/materials jointly developed by MOH and CPFB.
- general: general SOP question or insufficient information.

Also identify whether CPFB inputs are explicitly required, whether the case may
be covered by an existing SOP such as DRUMS, and whether the user asks about
SLA/timing.

A scheme name by itself is NOT enough to classify a case as policy-related.

Return ONLY valid JSON:
{{
  "category": "operation_related|policy_related|joint|general",
  "cpfb_inputs_required": true,
  "possible_existing_sop": false,
  "sla_question": false,
  "reason": "short reason"
}}

Question:
{query}
"""

    response = client.responses.create(
        model=MODEL,
        instructions="Return only valid JSON. No markdown fences.",
        input=prompt,
    )

    raw = response.output_text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {}

    category = result.get("category", "general")
    if category not in {"operation_related", "policy_related", "joint", "general"}:
        category = "general"

    return {
        "category": category,
        "cpfb_inputs_required": bool(
            result.get("cpfb_inputs_required", contains_any(query, CPFB_INPUT_SIGNALS))
        ),
        "possible_existing_sop": bool(
            result.get("possible_existing_sop", contains_any(query, DRUMS_SIGNALS))
        ),
        "sla_question": bool(
            result.get("sla_question", contains_any(query, SLA_SIGNALS))
        ),
        "reason": result.get("reason", ""),
    }


def classify_query(query: str) -> Dict[str, Any]:
    category = strong_keyword_category(query)
    if category:
        return {
            "category": category,
            "cpfb_inputs_required": contains_any(query, CPFB_INPUT_SIGNALS),
            "possible_existing_sop": contains_any(query, DRUMS_SIGNALS),
            "sla_question": contains_any(query, SLA_SIGNALS),
            "reason": "Clear pathway identified from SOP terminology.",
        }
    return llm_classify(query)


# ------------------------------ Retrieval ---------------------------

def summarise_sop(sop: Dict[str, Any], sop_id: str) -> Dict[str, Any]:
    doc = sop.get("document", {})
    if sop_id == "sharing_2024":
        return {
            "id": sop_id,
            "title": doc.get("title"),
            "status": doc.get("status"),
            "updated_as_at": doc.get("updated_as_at"),
            "scope": sop.get("scope"),
            "aim": sop.get("aim_and_background", {}).get("aim", []),
            "background": sop.get("aim_and_background", {}).get("background", []),
            "decision_framework": sop.get("decision_framework", {}),
            "materials": sop.get("materials", {}),
            "roles": sop.get("roles", {}),
            "workflows": sop.get("workflows", {}),
            "clearance_rules": sop.get("clearance_rules", {}),
            "document_relationship": sop.get("document_relationship", {}),
        }

    return {
        "id": sop_id,
        "title": doc.get("title"),
        "status": doc.get("status"),
        "date": doc.get("date"),
        "source": doc.get("source"),
        "notes": doc.get("notes", []),
        "media_material_definition": sop.get("slides", {}).get("3", {}),
        "decision_framework": sop.get("slides", {}).get("4", {}),
        "overarching_roles": sop.get("slides", {}).get("5", {}),
        "roles": sop.get("roles", []),
        "high_level_workflow": sop.get("slides", {}).get("7", {}),
        "detailed_workflow": sop.get("slides", {}).get("9", {}),
        "policy_workflow": sop.get("slides", {}).get("11", {}),
        "joint_workflow": sop.get("slides", {}).get("13", {}),
    }


def select_sop_candidates(query: str) -> List[Dict[str, Any]]:
    text = normalise(query)
    ranked = []

    for item in SOP_CATALOG:
        sop_id = item["id"]
        score = 0

        if sop_id == "sharing_2024":
            sharing_terms = [
                "share", "sharing", "disseminat", "frontliner", "cpfb comms",
                "cpfb channels", "cpfb channel", "website", "faq", "notification",
                "collateral", "update", "changes on cpfb", "channel change"
            ]
            if any(term in text for term in sharing_terms):
                score += 4
            if any(term in text for term in ["press release", "media query", "interview", "podcast", "broadcast", "issuance", "prepare"]):
                score -= 2
        else:
            prep_terms = [
                "prepare", "preparation", "issuance", "press release", "media query",
                "interview", "podcast", "broadcast", "media materials", "clearance", "issue"
            ]
            if any(term in text for term in prep_terms):
                score += 4
            if any(term in text for term in ["share", "sharing", "disseminat", "frontliner", "cpfb channel"]):
                score -= 2

        if score == 0 and any(term in text for term in ["sop", "workflow", "healthcare financing", "comms", "media"]):
            score = 1

        ranked.append({"id": sop_id, "title": item["title"], "score": score})

    ranked.sort(key=lambda item: item["score"], reverse=True)

    best_score = max(item["score"] for item in ranked)
    if best_score <= 0:
        return [{"id": item["id"], "title": item["title"]} for item in ranked]

    selected = [item for item in ranked if item["score"] == best_score]
    if len(selected) == 1:
        return [{"id": selected[0]["id"], "title": selected[0]["title"]}]

    return [{"id": item["id"], "title": item["title"]} for item in selected]


def retrieve_context(query: str, classification: Dict[str, Any]) -> Dict[str, Any]:
    selected_sops = select_sop_candidates(query)
    context: Dict[str, Any] = {
        "query": query,
        "classification": classification,
        "selected_sops": [
            summarise_sop(next(item["sop"] for item in SOP_CATALOG if item["id"] == sop["id"]), sop["id"])
            for sop in selected_sops
        ],
        "available_sops": [summarise_sop(item["sop"], item["id"]) for item in SOP_CATALOG],
        "chronology_note": (
            "The 2024 sharing SOP was endorsed first. After CPFB review, the 2025 preparation and issuance SOP was created to address gaps for media materials such as press releases, media queries and interview requests."
        ),
    }

    if classification.get("possible_existing_sop"):
        context["existing_sop_warning"] = (
            "The SOP context may overlap with other existing workflows such as DRUMS for social-media mistruths."
        )

    return context


# -------------------------- Source references -----------------------

def extract_source_slides(context: Dict[str, Any]) -> List[int]:
    slides: List[int] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if key == "source_slide" and isinstance(item, int):
                    slides.append(item)
                elif key == "source_slides" and isinstance(item, list):
                    slides.extend(x for x in item if isinstance(x, int))
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(context)
    return sorted(set(slides))


def format_context(context: Dict[str, Any]) -> str:
    return json.dumps(context, indent=2, ensure_ascii=False)


# ---------------------------- Generation ----------------------------

SYSTEM_PROMPT = """
You are the CPFB-MOH Healthcare Financing Comms Sharing and Media Workflow SOP Assistant.

Use ONLY the approved SOP context supplied to you. Do not use outside
knowledge to fill gaps unless provided to you.

Your role is to help a user understand when the relevant SOP applies, why it
matters, and how to follow it in practice. Write like a clear, friendly guide
rather than a rigid rulebook.

Your job is to:
1. Explain what situation or scenario triggers the use of the relevant SOP.
2. Clarify why the SOP is relevant in that situation.
3. Identify the most relevant pathway or SOP where possible.
4. Walk the user through the workflow in plain language.
5. Highlight the key stakeholders, decision points, and approvals involved.
6. Explain the SLA/timeline expectation in a practical way.
7. Flag any conditions, exceptions, or related SOPs that may also apply.
8. Cite the relevant source slide number(s) from the SOP.

GROUNDING RULES:
- Never invent responsibilities, stakeholders, approval levels or deadlines.
- The source SOPs do not provide a fixed numerical SLA.
- The responsible party preparing the media materials must establish the
  required SLA/timeline with relevant parties before the workflow begins.
- If asked for a number of days, explicitly say the source SOP does not give
  a fixed numerical duration.
- A scheme name alone does not determine the pathway.
- If the question is not clearly about the SOP, answer helpfully from the
  supplied context and say clearly when something is outside the SOP scope.
- Do not claim to have access to a PDF; the supplied JSON is the structured
  transcription of the source decks.

RESPONSE STYLE:
Write in a helpful and conversational way. Do not force a rigid template if a
more natural explanation would be better.

Use a structure similar to this when it helps:
- Start with a short answer to the user’s question.
- Then explain why the SOP applies and how to follow it.
- Use short bullet points or numbered steps where helpful.
- Mention the main people or teams involved.
- Explain any SLA or timing expectation clearly.
- End with the relevant source slide(s).

If the question is broad or general, answer in a natural way and keep the
response practical rather than overly formal.
**Source:** Slide X; Slide Y

For general questions, answer directly and clearly, while still explaining the
context and practical meaning of the SOP.

Do not force a rigid template if a more natural explanation would be better.
"""


def generate_answer(
    query: str,
    context: Dict[str, Any],
    source_slides: List[int],
    chat_history: Optional[List[Dict[str, str]]] = None,
) -> str:
    client = get_client()

    history = ""
    if chat_history:
        history = "\nRECENT CONVERSATION:\n"
        for message in chat_history[-6:]:
            history += f"{message.get('role', 'user').upper()}: {message.get('content', '')}\n"

    sources = ""
    if source_slides:
        sources = (
            "Relevant source slides retrieved: "
            + ", ".join(f"Slide {x}" for x in source_slides)
            + "."
        )

    prompt = f"""
USER QUESTION:
{query}
{history}

APPROVED SOP CONTEXT:
{format_context(context)}

{sources}

Answer the user's question strictly from the approved SOP context. If the
question is broader or more general than the SOP itself, answer helpfully from
what is available in the supplied context and clearly note when the question is
outside the SOP's direct scope.
"""

    response = client.responses.create(
        model=MODEL,
        instructions=SYSTEM_PROMPT,
        input=prompt,
    )
    answer = response.output_text.strip()
    return answer or "I could not find enough information in the SOP to answer that."


# ---------------------------- Public API ----------------------------

def answer_query(
    user_query: str,
    chat_history: Optional[List[Dict[str, str]]] = None,
) -> str:
    """Main function to call from Chatbot.py."""
    if not user_query or not user_query.strip():
        return "Please enter a question about the CPFB-MOH media workflow SOP."

    try:
        query = user_query.strip()
        classification = classify_query(query)
        context = retrieve_context(query, classification)
        source_slides = extract_source_slides(context)
        return generate_answer(query, context, source_slides, chat_history)

    except FileNotFoundError as exc:
        print(f"[SOP BOT] {exc}")
        return "I could not find the SOP data files in the Data folder."
    except RuntimeError as exc:
        print(f"[SOP BOT] {exc}")
        return "The chatbot is not configured correctly. Please check OPENAI_API_KEY."
    except Exception as exc:
        print(f"[SOP BOT] Unexpected error: {exc}")
        return "Sorry, I encountered an issue while processing your question. Please try again."


def classify_for_debug(user_query: str) -> Dict[str, Any]:
    """Useful during development to inspect retrieval without generating an answer."""
    classification = classify_query(user_query)
    context = retrieve_context(user_query, classification)
    return {
        "classification": classification,
        "source_slides": extract_source_slides(context),
        "context": context,
    }
