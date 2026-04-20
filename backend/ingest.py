import os
from pathlib import Path
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

BACKEND_DIR = Path(__file__).resolve().parent
DATA_FILE = BACKEND_DIR / "data" / "fau.txt"
CHROMA_DIR = BACKEND_DIR / "chroma"

# -----------------------
# LOAD DATA
# -----------------------
with open(DATA_FILE, "r", encoding="utf-8") as f:
    text = f.read()

# -----------------------
# SIMPLE CHUNKING (NO LANGCHAIN SPLITTER)
# -----------------------
chunks = text.split("====================================================")

# clean empty chunks
chunks = [c.strip() for c in chunks if c.strip()]

# -----------------------
# EMBEDDINGS (FREE)
# -----------------------
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# -----------------------
# STORE IN CHROMA DB
# -----------------------
db = Chroma.from_texts(
    chunks,
    embedding=embeddings,
    persist_directory=str(CHROMA_DIR)
)

db.persist()

print("FAU knowledge base created and loaded (no splitter).")