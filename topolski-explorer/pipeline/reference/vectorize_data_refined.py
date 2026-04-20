
import os
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from chromadb import Client
from chromadb.config import Settings
from dotenv import load_dotenv

load_dotenv()

CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_data")
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "semantic_text_blocks")

IGNORED_FIELDS = {
    "Title", "Alternative Title", "Date", "Creator",
    "Subject", "Collection Number and Name", "Holding Institution"
}

model = SentenceTransformer("all-MiniLM-L6-v2")
chroma_client = Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory=CHROMA_DB_PATH))
collection = chroma_client.get_or_create_collection(name=CHROMA_COLLECTION_NAME)

def vectorize_text_blocks(text_blocks):
    vectors = model.encode(text_blocks).tolist()
    return vectors

staged_data_dir = "staged_data"
batch_texts = []
batch_ids = []
batch_metadata = []
BATCH_SIZE = 32

for item_folder in os.listdir(staged_data_dir):
    item_path = os.path.join(staged_data_dir, item_folder)
    if not os.path.isdir(item_path):
        continue

    json_path = os.path.join(item_path, f"{item_folder}.json")
    if not os.path.exists(json_path):
        continue

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Vectorize individual metadata fields except ignored ones
    for key, value in data.items():
        if key in IGNORED_FIELDS or not isinstance(value, str):
            continue
        uid = f"{item_folder}_{key}"
        batch_texts.append(value)
        batch_ids.append(uid)
        batch_metadata.append({"item_id": item_folder, "field": key, "source_type": "metadata"})

    # Vectorize OCR blocks per page
    ocr_data = data.get("existing_ocr", {})
    for page_number, page_texts in ocr_data.items():
        for idx, text in enumerate(page_texts):
            if not text.strip():
                continue
            uid = f"{item_folder}_p{page_number}_ocr_{idx}"
            batch_texts.append(text)
            batch_ids.append(uid)
            batch_metadata.append({"item_id": item_folder, "page_number": page_number, "source_type": "ocr", "ocr_index": idx})

    # Add to Chroma in batches
    if len(batch_texts) >= BATCH_SIZE:
        vectors = vectorize_text_blocks(batch_texts)
        collection.add(documents=batch_texts, embeddings=vectors, ids=batch_ids, metadatas=batch_metadata)
        batch_texts, batch_ids, batch_metadata = [], [], []

# Final batch flush
if batch_texts:
    vectors = vectorize_text_blocks(batch_texts)
    collection.add(documents=batch_texts, embeddings=vectors, ids=batch_ids, metadatas=batch_metadata)
