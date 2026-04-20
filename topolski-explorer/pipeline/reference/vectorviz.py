import os
import json
from dotenv import load_dotenv
import chromadb
import numpy as np
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
import time # Import time for potential delays if needed

# Load environment variables from .env file
load_dotenv()

# --- Configuration from .env ---
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH")
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME")

# Construct the specific text and image collection names
TEXT_COLLECTION_NAME = f"{CHROMA_COLLECTION_NAME}_text"
IMAGE_COLLECTION_NAME = f"{CHROMA_COLLECTION_NAME}_images"

# --- ChromaDB Setup ---
print(f"Connecting to ChromaDB at: {CHROMA_DB_PATH}")
try:
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    print("Connected to ChromaDB.")
except Exception as e:
    print(f"Error connecting to ChromaDB: {e}")
    print("Please ensure ChromaDB is running or the path is correct.")
    exit()

# --- Retrieve Vectors ---
print(f"\nRetrieving vectors from collection: {TEXT_COLLECTION_NAME}")
try:
    text_collection = client.get_collection(name=TEXT_COLLECTION_NAME)
    # Get all data from the collection
    # For large collections, consider fetching in batches
    text_results = text_collection.get(include=['embeddings', 'metadatas'])
    text_embeddings = np.array(text_results['embeddings'])
    text_metadatas = text_results['metadatas']
    text_ids = text_results['ids']
    print(f"Retrieved {len(text_embeddings)} text vectors.")
except Exception as e:
    print(f"Error retrieving text vectors from {TEXT_COLLECTION_NAME}: {e}")
    text_embeddings = np.array([]) # Initialize as empty numpy array
    text_metadatas = []
    text_ids = []


print(f"\nRetrieving vectors from collection: {IMAGE_COLLECTION_NAME}")
try:
    image_collection = client.get_collection(name=IMAGE_COLLECTION_NAME)
    # Get all data from the collection
    # For large collections, consider fetching in batches
    image_results = image_collection.get(include=['embeddings', 'metadatas'])
    image_embeddings = np.array(image_results['embeddings'])
    image_metadatas = image_results['metadatas']
    image_ids = image_results['ids']
    print(f"Retrieved {len(image_embeddings)} image vectors.")
except Exception as e:
    print(f"Error retrieving image vectors from {IMAGE_COLLECTION_NAME}: {e}")
    image_embeddings = np.array([]) # Initialize as empty numpy array
    image_metadatas = []
    image_ids = []


# --- Dimensionality Reduction and Plotting ---

# Process Text Vectors
if text_embeddings.shape[0] > 1: # Need at least 2 samples for reduction
    print("\nPerforming dimensionality reduction on text vectors...")

    # PCA
    pca_text = PCA(n_components=2)
    text_pca_reduced = pca_text.fit_transform(text_embeddings)
    print("PCA reduction for text complete.")

    # t-SNE (can be computationally intensive for many points)
    # For a prototype of 10k items, t-SNE might take a while.
    # n_iter and perplexity can be tuned.
    print("Performing t-SNE reduction for text (this may take time)...")
    try:
        tsne_text = TSNE(n_components=2, random_state=42, perplexity=min(30, len(text_embeddings)-1), n_iter=300)
        text_tsne_reduced = tsne_text.fit_transform(text_embeddings)
        print("t-SNE reduction for text complete.")

        # Plot t-SNE text
        plt.figure(figsize=(10, 8))
        plt.scatter(text_tsne_reduced[:, 0], text_tsne_reduced[:, 1], s=10, alpha=0.6)
        plt.title('t-SNE Visualization of Text Embeddings')
        plt.xlabel('t-SNE Component 1')
        plt.ylabel('t-SNE Component 2')
        plt.grid(True)
        # Optional: Add annotations for a few points (e.g., first few items)
        # for i in range(min(10, len(text_ids))):
        #     plt.annotate(text_ids[i], (text_tsne_reduced[i, 0], text_tsne_reduced[i, 1]), fontsize=8)
        plt.show(block=False) # Use block=False to show plot without stopping script


    except Exception as e:
        print(f"Error performing t-SNE on text vectors: {e}")
        print("t-SNE requires at least 2 samples and perplexity must be less than the number of samples.")
        print("If you have very few items, t-SNE might not be possible or useful.")

    # Plot PCA text
    plt.figure(figsize=(10, 8))
    plt.scatter(text_pca_reduced[:, 0], text_pca_reduced[:, 1], s=10, alpha=0.6)
    plt.title('PCA Visualization of Text Embeddings')
    plt.xlabel('PCA Component 1')
    plt.ylabel('PCA Component 2')
    plt.grid(True)
     # Optional: Add annotations for a few points (e.g., first few items)
    # for i in range(min(10, len(text_ids))):
    #     plt.annotate(text_ids[i], (text_pca_reduced[i, 0], text_pca_reduced[i, 1]), fontsize=8)
    plt.show(block=False) # Use block=False to show plot without stopping script


else:
    print("\nNot enough text vectors (need at least 2) to perform dimensionality reduction.")


# Process Image Vectors
if image_embeddings.shape[0] > 1: # Need at least 2 samples for reduction
    print("\nPerforming dimensionality reduction on image vectors...")

    # PCA
    pca_image = PCA(n_components=2)
    image_pca_reduced = pca_image.fit_transform(image_embeddings)
    print("PCA reduction for image complete.")

    # t-SNE (can be computationally intensive for many points)
    print("Performing t-SNE reduction for image (this may take time)...")
    try:
        tsne_image = TSNE(n_components=2, random_state=42, perplexity=min(30, len(image_embeddings)-1), n_iter=300)
        image_tsne_reduced = tsne_image.fit_transform(image_embeddings)
        print("t-SNE reduction for image complete.")

        # Plot t-SNE image
        plt.figure(figsize=(10, 8))
        plt.scatter(image_tsne_reduced[:, 0], image_tsne_reduced[:, 1], s=10, alpha=0.6)
        plt.title('t-SNE Visualization of Image Embeddings')
        plt.xlabel('t-SNE Component 1')
        plt.ylabel('t-SNE Component 2')
        plt.grid(True)
         # Optional: Add annotations for a few points (e.g., first few items)
        # for i in range(min(10, len(image_ids))):
        #     plt.annotate(image_ids[i], (image_tsne_reduced[i, 0], image_tsne_reduced[i, 1]), fontsize=8)
        plt.show(block=False) # Use block=False to show plot without stopping script

    except Exception as e:
        print(f"Error performing t-SNE on image vectors: {e}")
        print("t-SNE requires at least 2 samples and perplexity must be less than the number of samples.")
        print("If you have very few images, t-SNE might not be possible or useful.")


    # Plot PCA image
    plt.figure(figsize=(10, 8))
    plt.scatter(image_pca_reduced[:, 0], image_pca_reduced[:, 1], s=10, alpha=0.6)
    plt.title('PCA Visualization of Image Embeddings')
    plt.xlabel('PCA Component 1')
    plt.ylabel('PCA Component 2')
    plt.grid(True)
     # Optional: Add annotations for a few points (e.g., first few items)
    # for i in range(min(10, len(image_ids))):
    #     plt.annotate(image_ids[i], (image_pca_reduced[i, 0], image_pca_reduced[i, 1]), fontsize=8)
    plt.show(block=False) # Use block=False to show plot without stopping script

else:
    print("\nNot enough image vectors (need at least 2) to perform dimensionality reduction.")


print("\nDisplaying plots. Close the plot windows to exit the script.")
plt.show() # This will block until all plot windows are closed

