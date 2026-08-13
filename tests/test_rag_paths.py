from logics import rag


def test_load_sop_finds_json_in_workspace():
    data = rag.load_sop()
    assert data["document"]["title"].startswith("CPFB-MOH")
