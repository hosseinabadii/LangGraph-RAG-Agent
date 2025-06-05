import logging
from pathlib import Path

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, TextLoader
from langchain_community.document_loaders.base import BaseLoader
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from app.config import BASE_DIR, settings

logger = logging.getLogger(__name__)

embeddings = OpenAIEmbeddings(
    model=settings.embedding_model_name,
    base_url=settings.embedding_base_url,
    api_key=settings.api_key,
)

vector_store = Chroma(
    collection_name="my_documents",
    embedding_function=embeddings,
    persist_directory=str(BASE_DIR / "chroma_db"),
)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
)


DOCUMENT_LOADER_MAPPING: dict[str, type[BaseLoader]] = {
    ".pdf": PyPDFLoader,
    ".docx": Docx2txtLoader,
    ".txt": TextLoader,
}

allowd_extensions = list(DOCUMENT_LOADER_MAPPING.keys())


def _load_and_split_documents(file_path: Path) -> list[Document]:
    """
    Load and split documents based on file extension.
    Raises:
        UnsupportedFileTypeError: If the file extension is not supported.
        Exception: For other loading or splitting errors.
    """

    file_extension = file_path.suffix.lower()
    if file_extension not in DOCUMENT_LOADER_MAPPING:
        raise ValueError(f"Unsupported file type: {file_extension}, Allowed types: {', '.join(allowd_extensions)}")
    loader = DOCUMENT_LOADER_MAPPING[file_extension](file_path)  # type: ignore
    documents = loader.load()
    splits = text_splitter.split_documents(documents)
    logger.info(f"Successfully loaded and split {file_path} into {len(splits)} chunks.")

    return splits


def index_document_to_chroma(file_path: Path, file_id: int) -> None:
    """Index a document to Chroma."""

    logger.info(f"Starting indexing for document: {file_path} with file_id: {file_id}")
    splits = _load_and_split_documents(file_path)
    for split in splits:
        split.metadata["file_id"] = file_id
    vector_store.add_documents(splits)
    logger.info(f"Successfully indexed {len(splits)} chunks for document {file_path} (file_id: {file_id}) to Chroma.")


def delete_document_from_chroma(file_id: int) -> None:
    """Delete documents from Chroma based on file ID."""

    logger.info(f"Attempting to delete documents with file_id: {file_id} from Chroma.")
    result = vector_store.get(where={"file_id": file_id})
    if not result or not result.get("ids"):
        logger.info(f"No documents found to delete for file_id: {file_id} in Chroma.")
        return
    doc_ids_to_delete = result["ids"]
    if doc_ids_to_delete:
        vector_store.delete(ids=doc_ids_to_delete)
        logger.info(
            f"Successfully deleted {len(doc_ids_to_delete)} document chunks for file_id: {file_id} from Chroma."
        )
    else:
        logger.info(f"No document chunks to delete for file_id {file_id} after get call.")
