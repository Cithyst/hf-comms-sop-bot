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

The bot uses ONLY the approved SOP JSON files in the Data folder.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from openai import OpenAI


# ============================================================================
# Configuration
# ============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


# ============================================================================
# Loading
# ============================================================================

def resolve_sop_files() -> List[Path]:
    """
    Resolve the SOP JSON files to load.

    If SOP_FILES environment variable is provided, use those files.

    Otherwise, look for the two approved SOP files in the Data folder.
    """

    env_path = os.getenv("SOP_FILES")

    if env_path:
        candidates = [
            Path(p).expanduser()
            for p in env_path.split(os.pathsep)
            if p
        ]

        found = [
            candidate
            for candidate in candidates
            if candidate.exists()
        ]

        if found:
            return found

    candidates = [
        BASE_DIR / "Data" / "media_workflow_sop.json",
        BASE_DIR / "Data" / "workflow_sharing_hf_comms_2024.json",
    ]

    found = [
        candidate
        for candidate in candidates
        if candidate.exists()
    ]

    if found:
        return found

    raise FileNotFoundError(
        "SOP files not found. Checked: "
        + ", ".join(str(c) for c in candidates)
        + ". Place the SOP JSON files inside the Data folder."
    )


SOP_FILES = resolve_sop_files()


def load_sop(path: Path) -> Dict[str, Any]:
    """Load one SOP JSON file."""

    if not path.exists():
        raise FileNotFoundError(
            f"SOP file not found: {path}"
        )

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


SOP_DOCUMENTS = [
    load_sop(path)
    for path in SOP_FILES
]


# ============================================================================
# SOP Identification
# ============================================================================

def sop_identifier(sop: Dict[str, Any]) -> str:
    """
    Identify which SOP the JSON represents.

    Supports both JSON structures:

    2024 Sharing SOP:
        Metadata is at the top level.

    2025 Media Materials SOP:
        Metadata may be nested under "document".
    """

    document = sop.get("document", {})

    title = (
        sop.get("title")
        or document.get("title")
        or ""
    ).lower()

    document_id = (
        sop.get("document_id")
        or document.get("document_id")
        or ""
    ).lower()

    # ------------------------------------------------------------------
    # Explicit document ID
    # ------------------------------------------------------------------

    if "hf_comms_sharing_cpfb_moh_2024" in document_id:
        return "sharing_2024"

    # ------------------------------------------------------------------
    # 2024 Sharing SOP
    # ------------------------------------------------------------------

    if (
        "sharing" in title
        and "healthcare financing" in title
    ):
        return "sharing_2024"

    # ------------------------------------------------------------------
    # 2025 Media Materials SOP
    # ------------------------------------------------------------------

    if (
        "preparation" in title
        and "issuance" in title
    ):
        return "preparation_2025"

    if "media materials" in title:
        return "preparation_2025"

    # ------------------------------------------------------------------
    # Fallback
    # ------------------------------------------------------------------

    return document_id or "unknown"


def build_sop_catalog() -> List[Dict[str, Any]]:
    """
    Build a common catalogue for all loaded SOPs.
    """

    catalog = []

    for sop in SOP_DOCUMENTS:
        document = sop.get("document", {})

        title = (
            sop.get("title")
            or document.get("title")
            or "SOP"
        )

        sop_id = sop_identifier(sop)

        catalog.append(
            {
                "id": sop_id,
                "title": title,
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

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set."
        )

    return OpenAI(api_key=api_key)


# ============================================================================
# General Helpers
# ============================================================================

def normalise(text: str) -> str:
    """
    Normalise text for keyword matching.
    """

    text = text.lower().replace("&", " and ")

    text = re.sub(
        r"[^a-z0-9\s/-]",
        " ",
        text,
    )

    return re.sub(
        r"\s+",
        " ",
        text,
    ).strip()


def contains_any(
    text: str,
    phrases: List[str],
) -> bool:
    """
    Return True if any phrase is present in the normalised text.
    """

    text = normalise(text)

    return any(
        normalise(p) in text
        for p in phrases
    )


# ============================================================================
# Existing 2025 SOP Classification Signals
# ============================================================================

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


# ============================================================================
# Existing 2025 Pathway Classification
# ============================================================================

def keyword_scores(query: str) -> Dict[str, int]:
    """
    Score the existing 2025 SOP pathways.
    """

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
    """
    Determine whether the 2025 pathway can be identified
    confidently using deterministic keywords.
    """

    scores = keyword_scores(query)

    highest = max(
        scores.values()
    )

    if highest == 0:
        return None

    winners = [
        key
        for key, value in scores.items()
        if value == highest
    ]

    if len(winners) != 1:
        return None

    # Do not classify a question as policy-related merely because
    # it says "policy" once.
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


# ============================================================================
# LLM Classification Within the 2025 SOP
# ============================================================================

def llm_classify(
    query: str,
) -> Dict[str, Any]:
    """
    Use the LLM when the 2025 pathway is ambiguous.
    """

    client = get_client()

    prompt = f"""
Classify this question for the CPFB-MOH Healthcare Financing media workflow SOP.

Choose exactly ONE category:

- operation_related:
  Operational matters concerning administration of healthcare schemes by CPFB,
  e.g. member interaction with CPFB service staff.

- policy_related:
  Policy announcements on financing schemes concerning CPFB,
  e.g. scheme changes or MediShield Life review.

- joint:
  Products/materials jointly developed by MOH and CPFB.

- general:
  General SOP question or insufficient information.

Also identify:

1. Whether CPFB inputs are explicitly required.
2. Whether the case may be covered by an existing SOP such as DRUMS.
3. Whether the user asks about SLA/timing.

IMPORTANT:
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

    category = result.get(
        "category",
        "general",
    )

    if category not in {
        "operation_related",
        "policy_related",
        "joint",
        "general",
    }:
        category = "general"

    return {
        "category": category,

        "cpfb_inputs_required": bool(
            result.get(
                "cpfb_inputs_required",
                contains_any(
                    query,
                    CPFB_INPUT_SIGNALS,
                ),
            )
        ),

        "possible_existing_sop": bool(
            result.get(
                "possible_existing_sop",
                contains_any(
                    query,
                    DRUMS_SIGNALS,
                ),
            )
        ),

        "sla_question": bool(
            result.get(
                "sla_question",
                contains_any(
                    query,
                    SLA_SIGNALS,
                ),
            )
        ),

        "reason": result.get(
            "reason",
            "",
        ),
    }


# ============================================================================
# SOP Selection
# ============================================================================

def classify_sop(
    query: str,
) -> Dict[str, Any]:
    """
    Determine which of the two Healthcare Financing SOPs is most relevant.

    This is the FIRST classification step.

    The distinction is based on what the user is trying to do,
    rather than merely matching words such as "policy", "media",
    "healthcare financing" or a scheme name.
    """

    text = normalise(query)

    # ------------------------------------------------------------------
    # Strong indicators for the 2025 Media Materials SOP
    # ------------------------------------------------------------------

    media_material_signals = [
        "press release",
        "press releases",
        "media query",
        "media queries",
        "media response",
        "media responses",
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
        "media material",
        "media materials",
        "media statement",
        "press statement",
        "anticipated media query",
        "anticipated media queries",
        "issue a press release",
        "issuing a press release",
        "respond to media",
        "respond to a media query",
    ]

    # ------------------------------------------------------------------
    # Strong indicators for the 2024 Sharing SOP
    # ------------------------------------------------------------------

    sharing_signals = [
        "cpfb website",
        "cshl website",
        "cpf website",
        "website static content",
        "website static contents",
        "static content",
        "static contents",
        "faq",
        "faqs",
        "frontliner",
        "frontliners",
        "notification",
        "notifications",
        "collateral",
        "collaterals",
        "aem",
        "nice 2.0",
        "acs",
        "eservice",
        "e-service",
        "calculator",
        "healthcare dashboard",
        "dashboard",
        "update the website",
        "update website",
        "website update",
        "website updates",
        "website changes",
        "changes on cpfb",
        "changes on cpfb channels",
        "cpfb comms channel",
        "cpfb comms channels",
        "cpfb channel",
        "cpfb channels",
        "sharing of comms materials",
        "sharing comms materials",
        "share comms materials",
        "disseminate",
        "dissemination",
        "new social media comms",
        "new social media material",
        "new social media materials",
        "social media post",
        "social media posts",
        "social media content",
        "edm",
        "edms",
        "electronic direct mailer",
        "electronic direct mailers",
        "video",
        "videos",
        "hardcopy",
        "hardcopy materials",
        "leaflet",
        "leaflets",
        "handbook",
        "handbooks",
    ]

    media_score = sum(
        1
        for signal in media_material_signals
        if normalise(signal) in text
    )

    sharing_score = sum(
        1
        for signal in sharing_signals
        if normalise(signal) in text
    )

    # ------------------------------------------------------------------
    # Strong deterministic result
    # ------------------------------------------------------------------

    if (
        media_score > 0
        and sharing_score == 0
    ):
        return {
            "selected_sop": "preparation_2025",
            "confidence": "high",
            "reason": (
                "The question explicitly concerns "
                "media-material preparation or issuance."
            ),
        }

    if (
        sharing_score > 0
        and media_score == 0
    ):
        return {
            "selected_sop": "sharing_2024",
            "confidence": "high",
            "reason": (
                "The question concerns CPFB communications "
                "channels, website updates, FAQs, frontliners "
                "or sharing/updating comms materials."
            ),
        }

    # ------------------------------------------------------------------
    # If both are possible, ask the LLM
    # ------------------------------------------------------------------

    client = get_client()

    prompt = f"""
You are selecting between TWO related but distinct CPFB-MOH
Healthcare Financing SOPs.

===============================================================
SOP 1 — 2024 Healthcare Financing Comms Sharing SOP
===============================================================

Title:
"Workflow for Sharing of Healthcare Financing Comms Materials btw CPFB & MOH"

This SOP primarily covers:

- sharing and dissemination of Healthcare Financing comms materials
- materials requiring changes on CPFB communications channels
- CPF website content
- CSHL website content
- FAQs
- static contents
- notifications
- collaterals
- social media materials
- eDMs
- videos
- CPFB frontliner dissemination
- CPF-COM development of new CPFB communications assets
- editorial changes to existing CPFB communications materials
- MOH-generated materials that do not require changes on CPFB channels


===============================================================
SOP 2 — 2025 Healthcare Financing Media Materials SOP
===============================================================

Title:
"Workflow for Preparation & Issuance of Media Materials for Healthcare Financing Schemes"

This SOP primarily covers media-material preparation and issuance,
including matters such as:

- press releases
- media queries
- interview requests
- journalists / media outlets
- media responses
- media-material preparation
- media-material clearance
- related media workflows


===============================================================
IMPORTANT DISTINCTION
===============================================================

Do NOT select an SOP merely because the question contains:

- "policy"
- "healthcare financing"
- "communications"
- "media"
- a healthcare scheme name

Instead, determine WHAT THE USER IS ACTUALLY TRYING TO DO.

Examples:

Example 1:
"We need to update the CareShield Life FAQ on the CPF website."

→ 2024 Sharing SOP

Example 2:
"MOH is preparing a press release about CareShield Life."

→ 2025 Media Materials SOP

Example 3:
"We need to prepare a new social media post about a healthcare
financing policy."

→ Consider the purpose and workflow carefully. Do not automatically
assume the 2025 Media Materials SOP just because it involves
communications.

If the scenario genuinely involves both workflows, return "both".

If the scenario is too ambiguous, return "unclear".


Return ONLY valid JSON:

{{
  "selected_sop": "sharing_2024|preparation_2025|both|unclear",
  "confidence": "high|medium|low",
  "reason": "short explanation"
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
        return {
            "selected_sop": "unclear",
            "confidence": "low",
            "reason": (
                "Unable to reliably determine the applicable SOP."
            ),
        }

    selected = result.get(
        "selected_sop",
        "unclear",
    )

    if selected not in {
        "sharing_2024",
        "preparation_2025",
        "both",
        "unclear",
    }:
        selected = "unclear"

    return {
        "selected_sop": selected,
        "confidence": result.get(
            "confidence",
            "medium",
        ),
        "reason": result.get(
            "reason",
            "",
        ),
    }


# ============================================================================
# Overall Classification
# ============================================================================

def classify_query(
    query: str,
) -> Dict[str, Any]:
    """
    Perform two-level classification:

    Level 1:
        Which SOP applies?

    Level 2:
        If the 2025 SOP applies, which pathway applies?
    """

    # --------------------------------------------------------------
    # First determine the applicable SOP
    # --------------------------------------------------------------

    sop_selection = classify_sop(query)

    # --------------------------------------------------------------
    # Then determine the existing 2025 pathway where relevant
    # --------------------------------------------------------------

    category = strong_keyword_category(query)

    if category:
        pathway_classification = {
            "category": category,

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
                "Clear pathway identified from "
                "SOP terminology."
            ),
        }

    else:
        pathway_classification = llm_classify(query)

    # --------------------------------------------------------------
    # Combine
    # --------------------------------------------------------------

    pathway_classification["sop_selection"] = sop_selection

    return pathway_classification


# ============================================================================
# SOP Summarisation
# ============================================================================

def summarise_sop(
    sop: Dict[str, Any],
    sop_id: str,
) -> Dict[str, Any]:
    """
    Convert either SOP JSON structure into a common retrieval structure.
    """

    document = sop.get(
        "document",
        {},
    )

    title = (
        sop.get("title")
        or document.get("title")
        or "SOP"
    )

    status = (
        sop.get("status")
        or document.get("status")
    )

    updated_as_at = (
        sop.get("updated_as_at")
        or document.get("updated_as_at")
        or document.get("date")
    )

    # ==================================================================
    # 2024 Sharing SOP
    # ==================================================================

    if sop_id == "sharing_2024":

        return {
            "id": sop_id,

            "sop_name": (
                "2024 Healthcare Financing "
                "Comms Sharing SOP"
            ),

            "title": title,

            "status": status,

            "updated_as_at": updated_as_at,

            "scope": sop.get(
                "scope",
            ),

            "aim_and_background": sop.get(
                "aim_and_background",
                {},
            ),

            "decision_framework": sop.get(
                "decision_framework",
                {},
            ),

            "materials": sop.get(
                "materials",
                {},
            ),

            "roles": sop.get(
                "roles",
                {},
            ),

            "workflows": sop.get(
                "workflows",
                {},
            ),

            "clearance_rules": sop.get(
                "clearance_rules",
                {},
            ),

            "sla_summary": sop.get(
                "sla_summary",
                {},
            ),

            "checklists": sop.get(
                "checklists",
                {},
            ),

            "content_ownership": sop.get(
                "content_ownership",
                {},
            ),

            "document_relationship": sop.get(
                "document_relationship",
                {},
            ),

            "bot_instructions": sop.get(
                "bot_instructions",
                {},
            ),

            "source_slides": sop.get(
                "source_slides",
                [],
            ),
        }

    # ==================================================================
    # 2025 Media Materials SOP
    # ==================================================================

    return {
        "id": sop_id,

        "sop_name": (
            "2025 Healthcare Financing "
            "Media Materials SOP"
        ),

        "title": title,

        "status": status,

        "date": document.get(
            "date",
        ),

        "source": document.get(
            "source",
        ),

        "notes": document.get(
            "notes",
            [],
        ),

        "media_material_definition": (
            sop.get(
                "slides",
                {},
            ).get(
                "3",
                {},
            )
        ),

        "decision_framework": (
            sop.get(
                "slides",
                {},
            ).get(
                "4",
                {},
            )
        ),

        "overarching_roles": (
            sop.get(
                "slides",
                {},
            ).get(
                "5",
                {},
            )
        ),

        "roles": sop.get(
            "roles",
            [],
        ),

        "high_level_workflow": (
            sop.get(
                "slides",
                {},
            ).get(
                "7",
                {},
            )
        ),

        "detailed_workflow": (
            sop.get(
                "slides",
                {},
            ).get(
                "9",
                {},
            )
        ),

        "policy_workflow": (
            sop.get(
                "slides",
                {},
            ).get(
                "11",
                {},
            )
        ),

        "joint_workflow": (
            sop.get(
                "slides",
                {},
            ).get(
                "13",
                {},
            )
        ),
    }


# ============================================================================
# SOP Candidate Selection
# ============================================================================

def select_sop_candidates(
    query: str,
    classification: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Select the SOP(s) identified by the SOP classifier.

    If the classifier is uncertain, return both SOPs so that the
    generation model can explain the distinction instead of guessing.
    """

    sop_selection = classification.get(
        "sop_selection",
        {},
    )

    selected = sop_selection.get(
        "selected_sop",
        "unclear",
    )

    available = {
        item["id"]: item
        for item in SOP_CATALOG
    }

    # --------------------------------------------------------------
    # One specific SOP
    # --------------------------------------------------------------

    if selected in {
        "sharing_2024",
        "preparation_2025",
    }:

        item = available.get(
            selected,
        )

        if item:
            return [
                {
                    "id": item["id"],
                    "title": item["title"],
                }
            ]

    # --------------------------------------------------------------
    # Both SOPs
    # --------------------------------------------------------------

    if selected == "both":

        return [
            {
                "id": item["id"],
                "title": item["title"],
            }
            for item in SOP_CATALOG
        ]

    # --------------------------------------------------------------
    # Unclear
    #
    # Do not guess.
    # Give the generation model both SOPs.
    # --------------------------------------------------------------

    return [
        {
            "id": item["id"],
            "title": item["title"],
        }
        for item in SOP_CATALOG
    ]


# ============================================================================
# Retrieval
# ============================================================================

def retrieve_context(
    query: str,
    classification: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Retrieve the relevant SOP context.

    Only the selected SOP(s) receive full structured content.
    The available SOP catalogue only contains names/titles.
    """

    selected_sops = select_sop_candidates(
        query,
        classification,
    )

    selected_context = []

    for selected in selected_sops:

        matching = next(
            (
                item
                for item in SOP_CATALOG
                if item["id"] == selected["id"]
            ),
            None,
        )

        if matching:

            selected_context.append(
                summarise_sop(
                    matching["sop"],
                    matching["id"],
                )
            )

    context: Dict[str, Any] = {

        "query": query,

        "classification": classification,

        # ----------------------------------------------------------
        # Full context for the SOP(s) considered relevant
        # ----------------------------------------------------------

        "selected_sops": selected_context,

        # ----------------------------------------------------------
        # Catalogue of all SOPs
        # ----------------------------------------------------------

        "available_sops": [
            {
                "id": item["id"],
                "title": item["title"],
            }
            for item in SOP_CATALOG
        ],

        # ----------------------------------------------------------
        # Explicit distinction between the two SOPs
        # ----------------------------------------------------------

        "sop_distinction": {

            "sharing_2024": (
                "Use primarily for sharing, updating, preparing and "
                "disseminating Healthcare Financing comms materials "
                "involving CPFB communications channels, including "
                "websites, FAQs, static contents, notifications, "
                "collaterals, social media, eDMs, videos and "
                "CPFB frontliner dissemination."
            ),

            "preparation_2025": (
                "Use primarily for preparation and issuance of "
                "Healthcare Financing media materials, including "
                "press releases, media queries, interview requests "
                "and related media workflows."
            ),
        },

        # ----------------------------------------------------------
        # Chronological/document relationship
        # ----------------------------------------------------------

        "chronology_note": (
            "The 2024 Sharing SOP was endorsed first. "
            "The later 2025 Preparation & Issuance of Media Materials "
            "SOP addresses a different media-material workflow. "
            "Do not treat the two SOPs as interchangeable."
        ),
    }

    # --------------------------------------------------------------
    # Existing SOP warning
    # --------------------------------------------------------------

    if classification.get(
        "possible_existing_sop",
    ):

        context["existing_sop_warning"] = (
            "The scenario may also overlap with another existing "
            "workflow such as DRUMS for social-media mistruths."
        )

    return context


# ============================================================================
# Source References
# ============================================================================

def extract_source_slides(
    context: Dict[str, Any],
) -> List[int]:
    """
    Extract source slide numbers from either SOP structure.

    Supports:

        "source_slide": 21

    and:

        "source_slides": [21, 22]

    and:

        "source_slides": [
            {"slide": 21, "title": "..."}
        ]

    and nested:

        {"slide": 21}
    """

    slides: List[int] = []

    def walk(value: Any) -> None:

        if isinstance(value, dict):

            for key, item in value.items():

                # --------------------------------------------------
                # Single source slide
                # --------------------------------------------------

                if (
                    key == "source_slide"
                    and isinstance(item, int)
                ):
                    slides.append(item)

                # --------------------------------------------------
                # Source slides
                # --------------------------------------------------

                elif (
                    key == "source_slides"
                    and isinstance(item, list)
                ):

                    for x in item:

                        if isinstance(
                            x,
                            int,
                        ):
                            slides.append(x)

                        elif (
                            isinstance(x, dict)
                            and isinstance(
                                x.get("slide"),
                                int,
                            )
                        ):
                            slides.append(
                                x["slide"]
                            )

                # --------------------------------------------------
                # Generic slide field
                # --------------------------------------------------

                elif (
                    key == "slide"
                    and isinstance(item, int)
                ):
                    slides.append(item)

                # --------------------------------------------------
                # Continue recursively
                # --------------------------------------------------

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
    """Format context for the generation model."""

    return json.dumps(
        context,
        indent=2,
        ensure_ascii=False,
    )


# ============================================================================
# Generation System Prompt
# ============================================================================

SYSTEM_PROMPT = """
You are the CPFB-MOH Healthcare Financing Comms Sharing and Media Workflow
SOP Assistant.

You have access to TWO approved SOPs:

1. 2024 Healthcare Financing Comms Sharing SOP
   "Workflow for Sharing of Healthcare Financing Comms Materials btw CPFB & MOH"

2. 2025 Healthcare Financing Media Materials SOP
   "Workflow for Preparation & Issuance of Media Materials for Healthcare
   Financing Schemes"


====================================================================
CORE ROLE
====================================================================

Use ONLY the approved SOP context supplied to you.

Do not use outside knowledge to fill gaps.

Your role is to help the user understand:

- which SOP applies
- why that SOP applies
- what workflow/pathway should be followed
- who is involved
- what decisions or clearances are required
- what SLA/timing applies
- what exceptions or related SOPs may be relevant
- where the information comes from in the source slides


====================================================================
TWO-SOP DISTINCTION
====================================================================

There are TWO related but distinct SOPs in the knowledge base.

--------------------------------------------------------------------
2024 Healthcare Financing Comms Sharing SOP
--------------------------------------------------------------------

Title:

"Workflow for Sharing of Healthcare Financing Comms Materials btw CPFB & MOH"

This generally applies to:

- sharing and dissemination of Healthcare Financing comms materials
- changes to CPFB communications channels
- CPF website
- CSHL website
- FAQs
- static contents
- notifications
- collaterals
- social media materials
- eDMs
- videos
- CPFB frontliner dissemination
- CPF-COM development of new CPFB communications assets
- editorial changes to existing CPFB communications materials
- MOH-generated materials that do not require changes on CPFB channels


--------------------------------------------------------------------
2025 Healthcare Financing Media Materials SOP
--------------------------------------------------------------------

Title:

"Workflow for Preparation & Issuance of Media Materials for Healthcare
Financing Schemes"

This generally applies to:

- press releases
- media queries
- interview requests
- journalists
- media outlets
- media responses
- media-material preparation
- media-material clearance
- related media-material issuance workflows


====================================================================
IMPORTANT SOP BOUNDARY
====================================================================

Determine the user's actual situation before selecting an SOP.

Do NOT select an SOP merely because the question contains:

- "policy"
- "communications"
- "media"
- "healthcare financing"
- a healthcare scheme name
- "CPFB"
- "MOH"

A scheme name alone does NOT determine the SOP.

Examples:

"We need to update a CareShield Life FAQ on the CPF website."

→ 2024 Sharing SOP.

"MOH is preparing a press release about CareShield Life."

→ 2025 Media Materials SOP.

If the scenario genuinely involves both workflows, explain which part is
covered by each SOP.

If the scenario is ambiguous, do not invent an answer. Explain what is
unclear and ask the minimum clarification needed.


====================================================================
TWO-LEVEL CLASSIFICATION
====================================================================

The chatbot should think about the workflow in this order:

1. Determine WHICH SOP applies.

2. Once the SOP is selected, determine the relevant pathway within
   that SOP.

For the 2025 Media Materials SOP, the relevant pathways may include:

- operation-related
- policy-related
- joint
- general

Do NOT use the 2025 pathway categories to decide which SOP applies.


====================================================================
YOUR JOB
====================================================================

1. Identify the applicable SOP.

2. Explain why the SOP applies.

3. Identify the relevant pathway within that SOP where possible.

4. If another SOP may also be relevant, explain the boundary between
   the two SOPs instead of mixing their workflows.

5. Walk the user through the workflow in plain language.

6. Highlight key stakeholders, decision points and approvals.

7. Explain the applicable SLA/timeline.

8. Flag conditions, exceptions or related SOPs.

9. Cite the relevant source slide number(s).


====================================================================
SLA RULES
====================================================================

The 2024 Sharing SOP contains specific indicative SLAs for different
types of communications materials.

Examples may include different timelines for:

- FAQ updates
- website static content
- digital notifications
- hardcopy notifications
- infographics
- eDMs
- social media posts
- videos
- MOH-generated materials

Do NOT automatically apply a 2024 SLA to the 2025 SOP.

Likewise, do NOT automatically apply a 2025 timing expectation to
the 2024 SOP.

When giving an SLA:

- identify which SOP it comes from
- identify which material/workflow it applies to
- do not transfer SLAs between SOPs
- do not invent a numerical SLA

The 2024 SOP also recognises that greater complexity and/or larger
volume may require a longer SLA and that some assets may be subject
to resource prioritisation.

If the source does not provide a numerical SLA for the specific
scenario, explicitly say so.


====================================================================
GROUNDING RULES
====================================================================

- Never invent responsibilities.
- Never invent stakeholders.
- Never invent approval levels.
- Never invent deadlines.
- Never invent SLAs.
- Never mix requirements between the two SOPs.
- Never treat the two SOPs as interchangeable.
- A healthcare scheme name alone does not determine the workflow.
- If information is not contained in the approved SOP context, say so.
- Do not claim to have access to a PDF.
- The supplied JSON files are structured transcriptions of the approved
  source decks.
- Use the source slides supplied in the context.
- Do not cite a slide merely because it exists; cite slides that support
  the answer.


====================================================================
SOP IDENTIFICATION IN THE RESPONSE
====================================================================

When the applicable SOP can be determined, explicitly state it near
the beginning of the answer.

Use:

"Applicable SOP: 2024 Healthcare Financing Comms Sharing SOP"

OR:

"Applicable SOP: 2025 Healthcare Financing Media Materials SOP"

If both apply:

"Applicable SOPs: 2024 Healthcare Financing Comms Sharing SOP + 2025
Healthcare Financing Media Materials SOP"

If the SOP cannot be determined:

"Applicable SOP: Unable to determine from the information provided."


Then briefly explain why that SOP applies.


====================================================================
RESPONSE STYLE
====================================================================

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


====================================================================
SOURCE CITATION
====================================================================

Always provide the relevant source slide(s) when the answer is based
on specific workflow content.

Use:

**Source:** Slide X; Slide Y

If different parts of the answer come from different SOPs, identify
the SOP alongside the slide where helpful.

Example:

**Source:** 2024 Sharing SOP, Slides 21–24.


====================================================================
OUTSIDE-SCOPE QUESTIONS
====================================================================

If the question is not clearly about the approved SOPs:

- answer only from the supplied context if possible
- clearly say when the question is outside the SOP's direct scope
- do not use outside knowledge to fill the gap
"""


# ============================================================================
# Answer Generation
# ============================================================================

def generate_answer(
    query: str,
    context: Dict[str, Any],
    source_slides: List[int],
    chat_history: Optional[
        List[Dict[str, str]]
    ] = None,
) -> str:

    client = get_client()

    # ------------------------------------------------------------------
    # Conversation history
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Retrieved source slides
    # ------------------------------------------------------------------

    sources = ""

    if source_slides:

        sources = (
            "Relevant source slides retrieved: "
            + ", ".join(
                f"Slide {x}"
                for x in source_slides
            )
            + "."
        )

    # ------------------------------------------------------------------
    # Generation prompt
    # ------------------------------------------------------------------

    prompt = f"""
USER QUESTION:
{query}

{history}

APPROVED SOP CONTEXT:
{format_context(context)}

{sources}

IMPORTANT:

The classification section in the approved context identifies which SOP
the system believes is applicable.

Use that classification as an important retrieval signal, but verify the
answer against the actual SOP content supplied in the context.

If the selected SOP is:

"sharing_2024"

→ Answer primarily from the 2024 Healthcare Financing Comms Sharing SOP.

If the selected SOP is:

"preparation_2025"

→ Answer primarily from the 2025 Healthcare Financing Media Materials SOP.

If the selected SOP is:

"both"

→ Explain the role of each SOP separately.

If the selected SOP is:

"unclear"

→ Do not guess. Explain the distinction between the two SOPs and ask
the minimum clarification needed if the question cannot be answered
reliably.

Never combine workflow steps from the two SOPs simply because they
appear relevant.

Answer the user's question strictly from the approved SOP context.

If the question is broader or more general than the SOP itself, answer
helpfully from what is available in the supplied context and clearly
note when the question is outside the SOP's direct scope.
"""

    response = client.responses.create(
        model=MODEL,
        instructions=SYSTEM_PROMPT,
        input=prompt,
    )

    answer = response.output_text.strip()

    if not answer:
        return (
            "I could not find enough information in the SOP "
            "to answer that."
        )

    return answer


# ============================================================================
# Public API
# ============================================================================

def answer_query(
    user_query: str,
    chat_history: Optional[
        List[Dict[str, str]]
    ] = None,
) -> str:
    """
    Main function called from Chatbot.py.
    """

    if not user_query or not user_query.strip():

        return (
            "Please enter a question about the CPFB-MOH "
            "Healthcare Financing comms workflow SOP."
        )

    try:

        query = user_query.strip()

        # ----------------------------------------------------------
        # Step 1: Classify the situation
        # ----------------------------------------------------------

        classification = classify_query(
            query,
        )

        # ----------------------------------------------------------
        # Step 2: Retrieve the relevant SOP context
        # ----------------------------------------------------------

        context = retrieve_context(
            query,
            classification,
        )

        # ----------------------------------------------------------
        # Step 3: Extract source slides
        # ----------------------------------------------------------

        source_slides = extract_source_slides(
            context,
        )

        # ----------------------------------------------------------
        # Step 4: Generate grounded answer
        # ----------------------------------------------------------

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
            "I could not find the SOP data files in "
            "the Data folder."
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


# ============================================================================
# Debugging / Development API
# ============================================================================

def classify_for_debug(
    user_query: str,
) -> Dict[str, Any]:
    """
    Useful during development.

    This allows you to inspect:

    - which SOP was selected
    - which 2025 pathway was identified
    - source slides retrieved
    - full retrieval context

    without generating a final chatbot response.
    """

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
            context,
        ),

        "context": context,
    }