from logics import rag


def test_prefers_sharing_sop_for_channel_update_queries():
    result = rag.select_sop_candidates(
        "How do we share updates to CPFB comms channels for a healthcare financing policy change?"
    )
    assert result[0]["id"] == "sharing_2024"


def test_prefers_preparation_sop_for_press_release_queries():
    result = rag.select_sop_candidates(
        "How do we prepare and issue a press release for a healthcare financing scheme?"
    )
    assert result[0]["id"] == "preparation_2025"


def test_includes_both_sops_for_general_queries():
    result = rag.select_sop_candidates(
        "Can you explain the overall workflow for healthcare financing comms?"
    )
    assert {item["id"] for item in result} == {"sharing_2024", "preparation_2025"}
