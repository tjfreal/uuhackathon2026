#search_app.py
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
from flask import Flask, render_template, request, redirect, url_for # Import Flask components
from sentence_transformers import SentenceTransformer # Import SentenceTransformer
import re # Import re for page number extraction (from image filenames)
import requests # Import requests (for potential future use, or if needed by models)

# Load environment variables from .env file
load_dotenv()

# --- Configuration from .env ---
STAGING_DATA_DIR = os.getenv("STAGING_DATA_DIR") # Needed to potentially retrieve full metadata or images
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH")
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME")

# Construct the specific text and image collection names
TEXT_COLLECTION_NAME = f"{CHROMA_COLLECTION_NAME}_text"
IMAGE_COLLECTION_NAME = f"{CHROMA_COLLECTION_NAME}_images"

# Base URL for the original item details page (from extraction phase .env)
# This is needed to create links in the search results.
ITEM_DETAILS_BASE_URL = os.getenv("ITEM_DETAILS_BASE_URL")
if not ITEM_DETAILS_BASE_URL:
     print("Warning: ITEM_DETAILS_BASE_URL not set in .env. Cannot create links to original items.")


# --- Flask App Setup ---
app = Flask(__name__)
# Configure upload folder for images (optional, can use temporary files)
# app.config['UPLOAD_FOLDER'] = 'uploads/' # Example upload folder

# --- ChromaDB Setup ---
print(f"Connecting to ChromaDB at: {CHROMA_DB_PATH}")
try:
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    print("Connected to ChromaDB.")
    text_collection = client.get_collection(name=TEXT_COLLECTION_NAME)
    image_collection = client.get_collection(name=IMAGE_COLLECTION_NAME)
    print(f"Connected to collections: {TEXT_COLLECTION_NAME}, {IMAGE_COLLECTION_NAME}")
except Exception as e:
    print(f"Error connecting to ChromaDB or collections: {e}")
    print("Please ensure ChromaDB is running and collections exist.")
    # In a production app, you might handle this more gracefully than exiting
    text_collection = None
    image_collection = None


# --- Load Models ---
# Load models only once when the application starts
text_model = None
image_model = None

print("Loading models...")

# Load Sentence Transformer model for text vectorization
try:
    text_model = SentenceTransformer('all-MiniLM-L6-v2')
    print("Loaded text embedding model: all-MiniLM-L6-v2")
except Exception as e:
    print(f"Error loading text embedding model: {e}")
    print("Text search will not be available.")

# Load EfficientNetB2 model for image vectorization
try:
    # Load the model without the top (classification) layer
    base_image_model = EfficientNetB2(weights='imagenet', include_top=False, pooling='avg')
    # Create a model that outputs the features from the pooling layer
    image_model = Model(inputs=base_image_model.input, outputs=base_image_model.output)
    print("Loaded image embedding model: EfficientNetB2 (with pooling)")
except Exception as e:
    print(f"Error loading image embedding model (EfficientNetB2): {e}")
    print("Image search will not be available.")


# --- Vectorization Functions (Same as in vectorize_data.py) ---
def vectorize_text(text):
    """Generates a vector embedding for the given text."""
    if not text or text_model is None:
        return None
    try:
        # The SentenceTransformer model expects a list of strings
        embeddings = text_model.encode([text], convert_to_numpy=True)
        return embeddings[0].tolist() # Return as a list of floats
    except Exception as e:
        print(f"Error during text vectorization: {e}")
        return None

def vectorize_image(image_file_or_path):
    """Generates a vector embedding for the image file or path."""
    if image_model is None:
        return None
    try:
        # Load the image, resizing to the expected input size for EfficientNetB2 (260x260)
        # Use PIL Image.open which can handle file-like objects from Flask requests
        img = Image.open(image_file_or_path).resize((260, 260))
        # Convert the image to a numpy array
        img_array = image.img_to_array(img)
        # Expand dimensions to match the model's expected input shape (add batch dimension)
        img_array = np.expand_dims(img_array, axis=0)
        # Preprocess the image for the model (scaling pixel values)
        from tensorflow.keras.applications.efficientnet import preprocess_input
        img_array = preprocess_input(img_array)

        # Get the embeddings
        embeddings = image_model.predict(img_array)
        return embeddings[0].tolist() # Return as a list of floats

    except FileNotFoundError:
        print(f"Error: Image file not found.")
        return None
    except Exception as e:
        print(f"Error vectorizing image: {e}")
        return None


# --- Search Function ---
def search_chroma(query_text=None, query_image_file=None, n_results=10):
    """Performs a search against the ChromaDB collections."""
    text_results = []
    image_results = []

    # Perform text search if query_text is provided and model is loaded
    if query_text and text_model and text_collection:
        print(f"Performing text search for: '{query_text}'")
        query_vector = vectorize_text(query_text)
        if query_vector:
            try:
                # Query the text collection
                text_results = text_collection.query(
                    query_embeddings=[query_vector],
                    n_results=n_results,
                    include=['metadatas', 'distances']
                )
                print(f"Text search returned {len(text_results.get('ids', []))} results.")
            except Exception as e:
                print(f"Error querying text collection: {e}")


    # Perform image search if query_image_file is provided and model is loaded
    if query_image_file and image_model and image_collection:
        print("Performing image search...")
        query_vector = vectorize_image(query_image_file)
        if query_vector:
            try:
                # Query the image collection
                image_results = image_collection.query(
                    query_embeddings=[query_vector],
                    n_results=n_results,
                    include=['metadatas', 'distances']
                )
                print(f"Image search returned {len(image_results.get('ids', []))} results.")
            except Exception as e:
                print(f"Error querying image collection: {e}")

    # Combine and format results (simple combination for now)
    # In a real app, you might want to combine and re-rank results based on distance/score
    combined_results = []

    # Add text results
    if text_results and text_results.get('ids'):
        for i in range(len(text_results['ids'][0])):
            item_id = text_results['metadatas'][0][i].get('item_id')
            # Retrieve full metadata from JSON file for richer display
            metadata = {}
            if item_id:
                json_path = os.path.join(STAGING_DATA_DIR, f"{item_id}.json")
                if os.path.exists(json_path):
                    try:
                        with open(json_path, 'r', encoding='utf-8') as f:
                            full_item_data = json.load(f)
                            metadata = full_item_data.get('metadata', {})
                    except Exception as e:
                        print(f"Error loading full metadata for item {item_id}: {e}")


            combined_results.append({
                "type": "text",
                "id": text_results['ids'][0][i],
                "item_id": item_id,
                "distance": text_results['distances'][0][i],
                "metadata": metadata, # Use retrieved metadata
                "original_link": f"{ITEM_DETAILS_BASE_URL}{item_id}" if item_id and ITEM_DETAILS_BASE_URL else "#" # Construct original link
            })

    # Add image results
    if image_results and image_results.get('ids'):
        for i in range(len(image_results['ids'][0])):
            item_id = image_results['metadatas'][0][i].get('item_id')
            page_number = image_results['metadatas'][0][i].get('page_number')
            image_filename = image_results['metadatas'][0][i].get('image_filename')

            # Retrieve full metadata from JSON file for richer display
            metadata = {}
            if item_id:
                json_path = os.path.join(STAGING_DATA_DIR, f"{item_id}.json")
                if os.path.exists(json_path):
                    try:
                        with open(json_path, 'r', encoding='utf-8') as f:
                            full_item_data = json.load(f)
                            metadata = full_item_data.get('metadata', {})
                    except Exception as e:
                        print(f"Error loading full metadata for item {item_id}: {e}")

            # Construct path to the local image thumbnail/preview
            local_image_path = os.path.join(STAGING_DATA_DIR, str(item_id), image_filename) if item_id and image_filename else None


            combined_results.append({
                "type": "image",
                "id": image_results['ids'][0][i],
                "item_id": item_id,
                "distance": image_results['distances'][0][i],
                "metadata": metadata, # Use retrieved metadata
                "page_number": page_number,
                "image_filename": image_filename,
                "local_image_path": local_image_path, # Path to local image file
                "original_link": f"{ITEM_DETAILS_BASE_URL}{item_id}" if item_id and ITEM_DETAILS_BASE_URL else "#" # Construct original link
            })

    # Sort results by distance (lower distance is more similar)
    combined_results.sort(key=lambda x: x['distance'])

    return combined_results


# --- Flask Routes ---
@app.route('/')
def index():
    """Renders the main search page."""
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    """Handles search queries."""
    query_text = request.form.get('query_text')
    query_image_file = request.files.get('query_image')
    n_results = int(request.form.get('n_results', 10)) # Get number of results, default to 10

    search_results = []
    if query_text or query_image_file:
        search_results = search_chroma(query_text=query_text, query_image_file=query_image_file, n_results=n_results)

    # Pass the results to the template
    return render_template('index.html', search_results=search_results, query_text=query_text, n_results=n_results)

# --- Helper to serve local images (for prototype only) ---
# In a production app, you'd serve these images via a web server (like Nginx or Apache)
# or a dedicated static file server. This is a simple way for the prototype.
from flask import send_from_directory

@app.route('/staged_data/<path:filename>')
def serve_staged_data(filename):
    """Serve files from the staged_data directory."""
    # Security consideration: Ensure filename doesn't allow directory traversal
    # send_from_directory handles this basic security.
    return send_from_directory(STAGING_DATA_DIR, filename)


if __name__ == '__main__':
    # Run the Flask app
    # Debug=True is useful during development for auto-reloading and error messages
    # For production, set debug=False
    app.run(debug=True)
