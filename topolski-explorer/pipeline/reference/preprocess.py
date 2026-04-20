import os
import json
from dotenv import load_dotenv
import fitz # PyMuPDF
from PIL import Image # Pillow
import time # Import time for adding delays
# hashlib is no longer strictly needed as we rely on item_id for filenames/dirs

# Load environment variables from .env file
load_dotenv()

# --- Configuration from .env ---
STAGING_DATA_DIR = os.getenv("STAGING_DATA_DIR")

# --- Ensure Staging Directory Exists (should already exist from extraction) ---
if not os.path.exists(STAGING_DATA_DIR):
    print(f"Error: Staging directory '{STAGING_DATA_DIR}' not found. Run data_extraction_script.py first.")
    exit() # Exit if staging directory doesn't exist

# --- Function to Extract Images from a PDF ---
def extract_images_from_pdf(pdf_path, item_id, base_output_dir):
    """Extracts each page of a PDF as a JPG image into an item-specific subdirectory."""
    images_info = []
    item_image_dir = os.path.join(base_output_dir, str(item_id)) # Item-specific subdirectory

    # Create item-specific subdirectory if it doesn't exist
    if not os.path.exists(item_image_dir):
        os.makedirs(item_image_dir)
        print(f"Created image directory: {item_image_dir}")
    else:
        print(f"Image directory already exists for {item_id}: {item_image_dir}")
        # Optional: Add logic here to clear the directory if you want to force re-extraction
        # import shutil
        # shutil.rmtree(item_image_dir)
        # os.makedirs(item_image_dir)
        # print(f"Cleared and recreated image directory: {item_image_dir}")


    try:
        doc = fitz.open(pdf_path)
        print(f"Opened PDF: {pdf_path} with {doc.page_count} pages.")

        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            # Render page to a pixmap (an image representation)
            # dpi can be adjusted for image quality vs file size
            pix = page.get_pixmap(dpi=300)

            # Define output filename within the item's subdirectory
            image_filename = f"{item_id}_{page_num + 1:04d}.jpg" # e.g., 2548454_0001.jpg
            image_save_path = os.path.join(item_image_dir, image_filename)

            try:
                # Save the pixmap as a JPG file
                pix.save(image_save_path)
                # print(f"Saved page {page_num + 1} as {image_filename}") # Reduced verbosity

                # Get image size (dimensions) using Pillow for robustness
                try:
                    with Image.open(image_save_path) as img:
                        width, height = img.size
                        image_size = f"{width}x{height}"
                except IOError:
                    image_size = "unknown"
                    print(f"Warning: Could not get dimensions for {image_filename}")


                images_info.append({
                    "page_number": page_num + 1,
                    "filename": image_filename,
                    "filepath": image_save_path, # Store local path for later use
                    "size": image_size
                })

            except Exception as e:
                print(f"Error saving image for page {page_num + 1} of {pdf_path}: {e}")
                # Continue processing other pages even if one fails

        doc.close()
        return images_info # Return list of successfully extracted images info

    except fitz.FileDataError as e:
        print(f"Error opening or reading PDF file {pdf_path}: {e}")
        return None # Indicate failure to process PDF
    except Exception as e:
        print(f"An unexpected error occurred while processing {pdf_path}: {e}")
        return None # Indicate failure to process PDF


# --- Main Pre-processing Logic ---
print("\nStarting PDF image extraction and metadata update...")

# Find all potential item IDs by looking for .json and .pdf files
item_ids_to_process = set()
for filename in os.listdir(STAGING_DATA_DIR):
    if filename.endswith('.json'):
        item_id = os.path.splitext(filename)[0]
        # Check if the corresponding PDF file exists
        pdf_filename = f"{item_id}.pdf"
        pdf_path = os.path.join(STAGING_DATA_DIR, pdf_filename)
        if os.path.exists(pdf_path):
            item_ids_to_process.add(item_id)
        else:
            print(f"Found JSON for item ID {item_id} ({filename}), but no corresponding PDF ({pdf_filename}). Skipping.")


total_items_to_process = len(item_ids_to_process)
processed_count = 0
successfully_processed_pdfs = 0
failed_to_process_pdfs = 0

# Add a small delay between processing items
PROCESSING_DELAY = 0.5 # seconds

print(f"Found {total_items_to_process} item IDs with both JSON and PDF files in the staging directory.")

for item_id in sorted(list(item_ids_to_process)): # Process in sorted order for consistency
    json_filename = f"{item_id}.json"
    pdf_filename = f"{item_id}.pdf"
    json_path = os.path.join(STAGING_DATA_DIR, json_filename)
    pdf_path = os.path.join(STAGING_DATA_DIR, pdf_filename)

    print(f"\nProcessing item ID: {item_id}")

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            item_data = json.load(f)

        # Ensure the pdf_path in JSON matches the one we found (redundant but safe)
        item_data["pdf_path"] = pdf_path

        # Extract images into a subdirectory named after the item_id within STAGING_DATA_DIR
        images_info = extract_images_from_pdf(pdf_path, item_id, STAGING_DATA_DIR)

        if images_info is not None: # Check if extraction was successful
            item_data["image_extraction"] = {
                "status": "success",
                "num_images": len(images_info),
                "images": images_info
            }
            successfully_processed_pdfs += 1

        else:
            item_data["image_extraction"] = {
                "status": "failed",
                "reason": "Error during PDF processing or image extraction."
            }
            failed_to_process_pdfs += 1


        # Save the updated JSON data
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(item_data, f, indent=4, ensure_ascii=False)
            print(f"Updated JSON metadata for {json_filename}")
        except IOError as e:
            print(f"Error saving updated JSON for {json_filename}: {e}")
            # If JSON saving fails, we still count the PDF processing status as it happened
            if images_info is not None:
                 failed_to_process_pdfs += 1 # Count as a processing failure due to JSON save issue
                 successfully_processed_pdfs -= 1 # Decrement successful count


    except (IOError, json.JSONDecodeError) as e:
        print(f"Error loading or parsing JSON file {json_filename}: {e}")
        failed_to_process_pdfs += 1

    processed_count += 1
    print(f"Finished processing item ID: {item_id}. Processed {processed_count}/{total_items_to_process} items with JSON/PDF pairs.")
    time.sleep(PROCESSING_DELAY) # Wait between processing items


print(f"\nPre-processing complete.")
print(f"Successfully processed PDFs for {successfully_processed_pdfs} items.")
print(f"Failed to process PDFs for {failed_to_process_pdfs} items.")
print(f"Image files saved to item-specific subdirectories within '{STAGING_DATA_DIR}'.")

