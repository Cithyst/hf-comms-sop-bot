from helper_functions.document_loader import load_and_split


class FakeUploadedFile:
    def __init__(self, name, content):
        self.name = name
        self._content = content

    def getvalue(self):
        return self._content


def test_load_and_split_handles_multiple_text_files():
    files = [
        FakeUploadedFile("a.txt", b"Alpha beta gamma"),
        FakeUploadedFile("b.txt", b"Delta epsilon zeta"),
    ]

    chunks = load_and_split(files)

    assert len(chunks) >= 2
    assert all(getattr(chunk, "page_content", "") for chunk in chunks)
