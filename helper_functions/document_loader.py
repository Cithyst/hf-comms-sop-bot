import os
import tempfile
from pathlib import Path
from typing import Any, List, Union

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader


def load_and_split(uploaded_files: Union[Any, List[Any]]) -> List[Document]:
    if uploaded_files is None:
        return []

    if not isinstance(uploaded_files, list):
        uploaded_files = [uploaded_files]

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    all_chunks: List[Document] = []

    for uploaded_file in uploaded_files:
        if not getattr(uploaded_file, "name", None):
            continue

        suffix = Path(uploaded_file.name).suffix.lower()
        with tempfile.NamedTemporaryFile(suffix=suffix or ".txt", delete=False) as temp_file:
            temp_file.write(uploaded_file.getvalue())
            temp_path = temp_file.name

        try:
            if suffix == ".txt":
                with open(temp_path, "r", encoding="utf-8") as handle:
                    text = handle.read()
                if text.strip():
                    docs = [Document(page_content=text, metadata={"source": uploaded_file.name})]
                    all_chunks.extend(
                        chunk for chunk in splitter.split_documents(docs) if getattr(chunk, "page_content", "").strip()
                    )
                continue

            loader = PyPDFLoader(temp_path)
            documents = loader.load()
            if documents and any(getattr(doc, "page_content", "").strip() for doc in documents):
                all_chunks.extend(
                    chunk for chunk in splitter.split_documents(documents) if getattr(chunk, "page_content", "").strip()
                )
                continue

            reader = PdfReader(temp_path)
            page_texts = []
            for page in reader.pages:
                text = page.extract_text() or ""
                if text.strip():
                    page_texts.append(text)

            if page_texts:
                docs = [Document(page_content=text, metadata={"source": uploaded_file.name}) for text in page_texts]
                all_chunks.extend(
                    chunk for chunk in splitter.split_documents(docs) if getattr(chunk, "page_content", "").strip()
                )
        finally:
            os.remove(temp_path)

    return all_chunks
