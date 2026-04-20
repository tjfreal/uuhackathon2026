import os
import json
from dotenv import load_dotenv
import time
import chromadb
from chromadb.utils import embedding_functions
import tensorflow as tf # Using TensorFlow for EfficientNetB2
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications import EfficientNetB2
from tensorflow.keras.models import Model
import numpy as np
from PIL import Image # Pillow for image loading
import requests
import re

# Load environment variables from .env file
load_dotenv()

# --- Configuration from .env ---
STAGING_DATA_DIR = os.getenv("STAGING_DATA_DIR")
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH")
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME")
RESET_CHROMA_COLLECTION = os.getenv("RESET_CHROMA_COLLECTION", "false").lower() == "true"

# --- Ensure Staging Directory Exists ---
if not os.path.exists(STAGING_DATA_DIR):
    print(f"Error: Staging directory '{STAGING_DATA_DIR}' not found. Run data_extraction_script.py and pre_process.py first.")
    exit()

# --- ChromaDB Setup ---
print(f"Connecting to ChromaDB at: {CHROMA_DB_PATH}")
client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

# Handle collection reset
if RESET_CHROMA_COLLECTION:
    print(f"Resetting collection: {CHROMA_COLLECTION_NAME}")
    try:
        client.delete_collection(name=CHROMA_COLLECTION_NAME)
        print(f"Collection '{CHROMA_COLLECTION_NAME}' deleted.")
    except:
        print(f"Collection '{CHROMA_COLLECTION_NAME}' not found, no need to delete.")

# Get or create the collection
# ChromaDB requires an embedding function, but we will provide embeddings manually
# So we use a dummy embedding function here.
# The dimension should match the output dimension of your models (EfficientNetB2 + Sentence Transformer)
# EfficientNetB2 output (after removing top) is 1408. all-MiniLM-L6-v2 output is 384.
# If we combine, the dimension would be 1408 + 384 = 1792.
# For now, we are storing separately, so we need to ensure the collection can handle
# different embedding dimensions or use separate collections.
# Let's use separate collections for clarity in this prototype.

# Collection for text vectors
TEXT_COLLECTION_NAME = f"{CHROMA_COLLECTION_NAME}_text"
try:
    text_collection = client.get_collection(name=TEXT_COLLECTION_NAME)
    print(f"Using existing text collection: {TEXT_COLLECTION_NAME}")
except:
    # Dimension for all-MiniLM-L6-v2 is 384
    text_collection = client.create_collection(name=TEXT_COLLECTION_NAME,
                                               embedding_function=embedding_functions.DefaultEmbeddingFunction()) # Dummy EF
    print(f"Created new text collection: {TEXT_COLLECTION_NAME}")

# Collection for image vectors
IMAGE_COLLECTION_NAME = f"{CHROMA_COLLECTION_NAME}_images"
try:
    image_collection = client.get_collection(name=IMAGE_COLLECTION_NAME)
    print(f"Using existing image collection: {IMAGE_COLLECTION_NAME}")
except:
    # Dimension for EfficientNetB2 (without top) is 1408
    image_collection = client.create_collection(name=IMAGE_COLLECTION_NAME,
                                                embedding_function=embedding_functions.DefaultEmbeddingFunction()) # Dummy EF
    print(f"Created new image collection: {IMAGE_COLLECTION_NAME}")


# --- Load Models ---
print("Loading models...")

# Load Sentence Transformer model for text vectorization
# Using a standard Hugging Face model
try:
    from sentence_transformers import SentenceTransformer
    text_model = SentenceTransformer('all-MiniLM-L6-v2')
    print("Loaded text embedding model: all-MiniLM-L6-v2")
    TEXT_EMBEDDING_DIM = text_model.get_sentence_embedding_dimension()
    print(f"Text embedding dimension: {TEXT_EMBEDDING_DIM}")
except ImportError:
    print("Error: sentence-transformers library not found. Please install it (`pip install sentence-transformers`).")
    exit()
except Exception as e:
    print(f"Error loading text embedding model: {e}")
    exit()


# Load EfficientNetB2 model for image vectorization
# Using TensorFlow/Keras pre-trained model
try:
    # Load the model without the top (classification) layer
    base_image_model = EfficientNetB2(weights='imagenet', include_top=False, pooling='avg')
    # Create a model that outputs the features from the pooling layer
    image_model = Model(inputs=base_image_model.input, outputs=base_image_model.output)
    print("Loaded image embedding model: EfficientNetB2 (with pooling)")
    IMAGE_EMBEDDING_DIM = image_model.output_shape[1]
    print(f"Image embedding dimension: {IMAGE_EMBEDDING_DIM}")
except Exception as e:
    print(f"Error loading image embedding model (EfficientNetB2): {e}")
    print("Please ensure TensorFlow is installed (`pip install tensorflow`).")
    exit()


# --- Vectorization Functions ---
def vectorize_text(text):
    """Generates a vector embedding for the given text."""
    if not text:
        return None
    # The SentenceTransformer model expects a list of strings
    embeddings = text_model.encode([text])
    return embeddings[0].tolist() # Return as a list of floats

def vectorize_image(image_path):
    """Generates a vector embedding for the image file."""
    try:
        # Load the image, resizing to the expected input size for EfficientNetB2 (260x260)
        img = image.load_img(image_path, target_size=(260, 260))
        # Convert the image to a numpy array
        img_array = image.img_to_array(img)
        # Expand dimensions to match the model's expected input shape (add batch dimension)
        img_array = np.expand_dims(img_array, axis=0)
        # Preprocess the image for the model (scaling pixel values)
        # EfficientNet models expect input scaled to [-1, 1] or [0, 1] depending on preprocessing function
        # Use the preprocess_input function from the application module
        from tensorflow.keras.applications.efficientnet import preprocess_input
        img_array = preprocess_input(img_array)

        # Get the embeddings
        embeddings = image_model.predict(img_array)
        return embeddings[0].tolist() # Return as a list of floats

    except FileNotFoundError:
        print(f"Error: Image file not found at {image_path}")
        return None
    except Exception as e:
        print(f"Error vectorizing image {image_path}: {e}")
        return None


# --- Main Vectorization Logic ---
print("\nStarting vectorization and ChromaDB ingestion...")

# Find all item directories in the staging directory
item_dirs = [d for d in os.listdir(STAGING_DATA_DIR) if os.path.isdir(os.path.join(STAGING_DATA_DIR, d))]

total_items_to_process = len(item_dirs)
processed_items_count = 0
successfully_vectorized_items = 0
failed_vectorized_items = 0

# Batching for ChromaDB ingestion (can improve performance)
BATCH_SIZE = 100 # Number of vectors to add in one ChromaDB call

text_embeddings_to_add = []
text_metadatas_to_add = []
text_ids_to_add = []

image_embeddings_to_add = []
image_metadatas_to_add = []
image_ids_to_add = []


# Add a small delay between processing items
PROCESSING_DELAY = 0.1 # seconds

print(f"Found {total_items_to_process} item directories in the staging directory.")

for item_id in sorted(item_dirs): # Process in sorted order for consistency
    item_dir_path = os.path.join(STAGING_DATA_DIR, item_id)
    json_filename = f"{item_id}.json"
    json_path = os.path.join(STAGING_DATA_DIR, json_filename) # JSON is noT inside item dir

    # Check if the JSON file exists (should exist if pre-processing was successful)
    if not os.path.exists(json_path):
        print(f"Skipping item ID {item_id}: JSON file not found at {json_path}.")
        failed_vectorized_items += 1
        continue

    print(f"\nProcessing item ID: {item_id}")

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            item_data = json.load(f)

        # --- Text Vectorization ---
        # Concatenate relevant metadata fields into a single string
        # Adjust the fields list based on which metadata you want to include
        metadata_fields_to_vectorize = ["Title", "Alternative Title", "Description", "Subject", "Keywords", "Creator", "Collection Number and Name", "Holding Institution", "Type", "Genre", "Format", "Rights", "Source", "ARK", "Setname", "ID", "Reference URL"] # Include all extracted fields for now
        text_to_vectorize = " ".join([
            str(item_data["metadata"].get(field, "")) for field in metadata_fields_to_vectorize
            if item_data["metadata"].get(field) is not None # Only include fields that exist and are not None
        ]).strip()

        if not text_to_vectorize:
            print(f"Warning: No text found to vectorize for item ID {item_id}. Skipping text vectorization.")
            text_vector = None
        else:
            print(f"Vectorizing text for item ID {item_id}...")
            text_vector = vectorize_text(text_to_vectorize)

        if text_vector:
            # Prepare data for text collection ingestion
            text_embeddings_to_add.append(text_vector)
            text_metadatas_to_add.append({
                "item_id": item_id,
                "content_type": "text",
                "source_field": "concatenated_metadata",
                "original_text": text_to_vectorize # Store original text for context
            })
            text_ids_to_add.append(f"{item_id}_text") # Unique ID for this text vector

        # --- Image Vectorization ---
        # Find all JPG files in the item's subdirectory
        image_files = [f for f in os.listdir(item_dir_path) if f.endswith('.jpg')]
        image_files.sort() # Process images in order (e.g., page 1, page 2)

        if not image_files:
            print(f"Warning: No image files found for item ID {item_id}. Skipping image vectorization.")

        for image_filename in image_files:
            image_path = os.path.join(item_dir_path, image_filename)
            page_number_match = re.search(r'_(\d{4})\.jpg$', image_filename)
            page_number = int(page_number_match.group(1)) if page_number_match else None


            print(f"Vectorizing image {image_filename} for item ID {item_id}...")
            image_vector = vectorize_image(image_path)

            if image_vector:
                # Prepare data for image collection ingestion
                image_embeddings_to_add.append(image_vector)
                image_metadatas_to_add.append({
                    "item_id": item_id,
                    "content_type": "image",
                    "image_filename": image_filename,
                    "page_number": page_number # Store page number
                })
                image_ids_to_add.append(f"{item_id}_{page_number}") # Unique ID for this image vector

            # --- Batch Ingestion Check ---
            # Ingest into ChromaDB in batches to improve efficiency
            if len(text_embeddings_to_add) >= BATCH_SIZE:
                print(f"Ingesting batch of {len(text_embeddings_to_add)} text vectors...")
                try:
                    text_collection.add(
                        embeddings=text_embeddings_to_add,
                        metadatas=text_metadatas_to_add,
                        ids=text_ids_to_add
                    )
                    print("Text batch ingested successfully.")
                    text_embeddings_to_add = []
                    text_metadatas_to_add = []
                    text_ids_to_add = []
                except Exception as e:
                    print(f"Error ingesting text batch: {e}")
                    # Decide how to handle batch failure - for a prototype,
                    # just print error and clear batch is acceptable.

            if len(image_embeddings_to_add) >= BATCH_SIZE:
                 print(f"Ingesting batch of {len(image_embeddings_to_add)} image vectors...")
                 try:
                     image_collection.add(
                         embeddings=image_embeddings_to_add,
                         metadatas=image_metadatas_to_add,
                         ids=image_ids_to_add
                     )
                     print("Image batch ingested successfully.")
                     image_embeddings_to_add = []
                     image_metadatas_to_add = []
                     image_ids_to_add = []
                 except Exception as e:
                     print(f"Error ingesting image batch: {e}")
                     # Decide how to handle batch failure

    except (IOError, json.JSONDecodeError) as e:
        print(f"Error loading or parsing JSON file {json_path}: {e}")
        failed_vectorized_items += 1
        continue # Move to the next item if JSON loading fails
    except Exception as e:
        print(f"An unexpected error occurred while processing item ID {item_id}: {e}")
        failed_vectorized_items += 1
        continue


    # If we reached here, the item was processed (even if some vectors failed)
    successfully_vectorized_items += 1
    processed_items_count += 1
    print(f"Finished processing item ID: {item_id}. Processed {processed_items_count}/{total_items_to_process} items.")
    time.sleep(PROCESSING_DELAY) # Wait between processing items


# --- Ingest any remaining vectors in the batch ---
if text_embeddings_to_add:
    print(f"Ingesting final batch of {len(text_embeddings_to_add)} text vectors...")
    try:
        text_collection.add(
            embeddings=text_embeddings_to_add,
            metadatas=text_metadatas_to_add,
            ids=text_ids_to_add
        )
        print("Final text batch ingested successfully.")
    except Exception as e:
        print(f"Error ingesting final text batch: {e}")

if image_embeddings_to_add:
     print(f"Ingesting final batch of {len(image_embeddings_to_add)} image vectors...")
     try:
         image_collection.add(
             embeddings=image_embeddings_to_add,
             metadatas=image_metadatas_to_add,
             ids=image_ids_to_add
         )
         print("Final image batch ingested successfully.")
     except Exception as e:
         print(f"Error ingesting final image batch: {e}")


print(f"\nVectorization and ChromaDB ingestion complete.")
print(f"Successfully processed {successfully_vectorized_items} items.")
print(f"Failed to process {failed_vectorized_items} items.")
print(f"Vectors stored in ChromaDB collections '{TEXT_COLLECTION_NAME}' and '{IMAGE_COLLECTION_NAME}'.")

