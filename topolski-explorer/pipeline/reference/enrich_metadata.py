import os
import json
from dotenv import load_dotenv
import time
import fitz # PyMuPDF
import cv2 # OpenCV
import numpy as np
import pytesseract
from PIL import Image # Pillow
import re # Import re for filename parsing

# Load environment variables from .env file
load_dotenv()

# --- Configuration from .env ---
STAGING_DATA_DIR = os.getenv("STAGING_DATA_DIR")

# --- Tesseract OCR Configuration ---
# If tesseract is not in your PATH, uncomment the line below and set the correct path
# This global setting should work, but we'll also try setting it locally in the function for debugging
# pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe' # Example for Windows

# --- Ensure Staging Directory Exists ---
if not os.path.exists(STAGING_DATA_DIR):
    print(f"Error: Staging directory '{STAGING_DATA_DIR}' not found. Run data_extraction_script.py first.")
    exit()

# --- Function to Extract Existing OCR Text from PDF Page ---
def extract_existing_ocr(page):
    """Extracts text embedded in a PDF page (often from existing OCR)."""
    try:
        # getText('text') extracts text with some basic layout info
        # getText('html') or 'xml' might provide more structure if available
        text = page.get_text("text")
        return text.strip() if text else ""
    except Exception as e:
        print(f"Warning: Could not extract existing OCR from page: {e}")
        return ""

# --- Function to Perform Text Detection and OCR ---
def process_page_for_regions(page, item_id, page_num, output_base_dir):
    """Detects text and sketch regions, performs OCR, and saves clippings."""
    regions_info = []
    page_image_dir = os.path.join(output_base_dir, f"{item_id}_{page_num:04d}") # Directory for this page's clippings

    # Create the page-specific clipping directory
    if not os.path.exists(page_image_dir):
        os.makedirs(page_image_dir)
        print(f"Created clipping directory for page {page_num}: {page_image_dir}")
    else:
        print(f"Clipping directory already exists for page {page_num}: {page_image_dir}")
        # Optional: Add logic here to clear the directory if you want to force re-processing
        # import shutil
        # shutil.rmtree(page_image_dir)
        # os.makedirs(page_image_dir)
        # print(f"Cleared and recreated clipping directory: {page_image_dir}")


    # Render the page to a pixmap (image)
    # dpi can be adjusted for image quality vs processing time
    pix = page.get_pixmap(dpi=300)
    img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape((pix.h, pix.w, pix.n))

    # Convert to grayscale for image processing
    if img_array.shape[-1] == 3: # Check if it's a color image
        gray_image = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray_image = img_array # Already grayscale or single channel

    # --- Text Detection (using OpenCV contours on thresholded image) ---
    # This is a basic approach. LayoutParser is more sophisticated for complex layouts.
    print(f"Performing text detection on page {page_num}...")
    # Apply thresholding to get a binary image
    # Adjust threshold values based on image quality
    _, thresh = cv2.threshold(gray_image, 150, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Find contours (potential text regions)
    # Use RETR_EXTERNAL to find only outer contours if needed, or RETR_LIST/TREE
    contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    text_region_count = 0
    sketch_region_count = 0

    # Sort contours by their y-coordinate to process text roughly top-to-bottom
    contours = sorted(contours, key=lambda c: cv2.boundingRect(c)[1])

    # Process contours
    for i, contour in enumerate(contours):
        # Get bounding box coordinates (x, y, w, h)
        x, y, w, h = cv2.boundingRect(contour)

        # Filter out very small or very large regions that are unlikely to be text
        # These thresholds may need tuning based on your collection's content
        area = w * h
        aspect_ratio = w / h if h > 0 else 0

        if area < 100 or area > 0.8 * gray_image.size or aspect_ratio > 10 or aspect_ratio < 0.1:
            continue # Skip unlikely text regions

        # --- OCR on Text Region ---
        # Crop the region from the original color image (if available) or grayscale
        # Add a small padding to the bounding box for better OCR results
        padding = 5
        x1, y1, x2, y2 = max(0, x - padding), max(0, y - padding), min(pix.w, x + w + padding), min(pix.h, y + h + padding)
        cropped_img_array = img_array[y1:y2, x1:x2]

        # Convert cropped image array to PIL Image for pytesseract
        cropped_pil_img = Image.fromarray(cropped_img_array)

        extracted_text = ""
        try:
            # --- Debug: Print the Tesseract command path being used ---
            print(f"  Debug: pytesseract.pytesseract.tesseract_cmd is set to: {pytesseract.pytesseract.tesseract_cmd}")
            # --- End Debug ---

            # Use pytesseract to do OCR on the cropped image
            # Explicitly set the command path here for debugging
            # Replace 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe' with your actual path
            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

            extracted_text = pytesseract.image_to_string(cropped_pil_img, lang='eng').strip()
            # Clean up extracted text (remove excessive whitespace, etc.)
            extracted_text = re.sub(r'\s+', ' ', extracted_text).strip()

            if extracted_text:
                print(f"  Detected Text Region (Page {page_num}, Region {text_region_count + 1}): '{extracted_text[:50]}...'") # Print snippet
                region_type = "text"
                text_region_count += 1
                clipping_filename = f"text_box_{text_region_count:04d}.jpg"
                clipping_path = os.path.join(page_image_dir, clipping_filename)
                # Save the clipping
                try:
                    cropped_pil_img.save(clipping_path)
                except Exception as e:
                    print(f"Error saving text clipping {clipping_path}: {e}")
                    clipping_path = None # Mark path as None if saving fails

                regions_info.append({
                    "type": region_type,
                    "bbox": [x1, y1, x2, y2], # Bounding box coordinates
                    "text": extracted_text,
                    "clipping_filename": clipping_filename,
                    "clipping_path": clipping_path # Local path to the clipping image
                })
            # else:
                # print(f"  Skipping detected region with no significant text (Page {page_num}, Contour {i})")


        except pytesseract.TesseractNotFoundError:
            print("Error: Tesseract OCR engine not found. Please install it or set pytesseract.tesseract_cmd.")
            # Decide if you want to exit or continue without OCR
            # For now, we'll print error and continue
        except Exception as e:
            print(f"Error performing OCR on region (Page {page_num}, Contour {i}): {e}")
            # Continue processing other regions even if one fails

    # --- Basic Sketch Region Identification (Heuristic) ---
    # This is a simple approach: identify areas not covered by text bounding boxes
    # and check for edge density. More sophisticated methods are possible.
    print(f"Attempting to identify sketch regions on page {page_num}...")
    # Create a mask of text regions
    text_mask = np.zeros_like(gray_image, dtype=np.uint8)
    for region in regions_info:
        if region["type"] == "text":
            x1, y1, x2, y2 = region["bbox"]
            cv2.rectangle(text_mask, (x1, y1), (x2, y2), 255, -1) # Draw filled rectangle on mask

    # Invert the mask to get non-text areas
    non_text_mask = cv2.bitwise_not(text_mask)

    # Apply edge detection to the grayscale image
    edges = cv2.Canny(gray_image, 100, 200) # Adjust thresholds as needed

    # Find contours in the non-text areas
    # Apply the non-text mask to the edges before finding contours
    edges_in_non_text = cv2.bitwise_and(edges, edges, mask=non_text_mask)
    sketch_contours, _ = cv2.findContours(edges_in_non_text, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter and process potential sketch regions
    for i, contour in enumerate(sketch_contours):
         x, y, w, h = cv2.boundingRect(contour)
         area = w * h

         # Filter out small regions or regions that are too large (might be background)
         # These thresholds need tuning
         if area < 500 or area > 0.9 * gray_image.size:
             continue

         # Calculate edge density within the contour bounding box
         # High edge density in a non-text area might indicate a sketch
         cropped_edges = edges[y:y+h, x:x+w]
         edge_pixels = np.sum(cropped_edges > 0)
         total_pixels = w * h
         edge_density = edge_pixels / total_pixels if total_pixels > 0 else 0

         # Adjust this threshold based on experimentation
         if edge_density > 0.05: # Example threshold for edge density
              print(f"  Potential Sketch Region (Page {page_num}, Region {sketch_region_count + 1}) with edge density {edge_density:.4f}")
              region_type = "sketch"
              sketch_region_count += 1
              clipping_filename = f"sketch_region_{sketch_region_count:04d}.jpg"
              clipping_path = os.path.join(page_image_dir, clipping_filename)

              # Crop the potential sketch region
              x1, y1, x2, y2 = x, y, x + w, y + h # No padding for sketch regions
              cropped_img_array = img_array[y1:y2, x1:x2]
              cropped_pil_img = Image.fromarray(cropped_img_array)

              # Save the clipping
              try:
                  cropped_pil_img.save(clipping_path)
              except Exception as e:
                  print(f"Error saving sketch clipping {clipping_path}: {e}")
                  clipping_path = None # Mark path as None if saving fails

              regions_info.append({
                  "type": region_type,
                  "bbox": [x1, y1, x2, y2], # Bounding box coordinates
                  "clipping_filename": clipping_filename,
                  "clipping_path": clipping_path # Local path to the clipping image
              })
         # else:
             # print(f"  Skipping potential sketch region with low edge density (Page {page_num}, Contour {i})")


    print(f"Finished processing page {page_num}. Found {text_region_count} text regions and {sketch_region_count} potential sketch regions.")
    return regions_info


# --- Main Enrichment Logic ---
print("\nStarting metadata enrichment...")

# Find all item IDs by looking for .json and .pdf files in the staging directory
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
processed_items_count = 0
successfully_enriched_items = 0
failed_enriched_items = 0

# Add a small delay between processing items
PROCESSING_DELAY = 0.5 # seconds

print(f"Found {total_items_to_process} item IDs with both JSON and PDF files in the staging directory.")

for item_id in sorted(list(item_ids_to_process)): # Process in sorted order for consistency
    json_filename = f"{item_id}.json"
    pdf_filename = f"{item_id}.pdf"
    json_path = os.path.join(STAGING_DATA_DIR, json_filename)
    pdf_path = os.path.join(STAGING_DATA_DIR, pdf_filename)
    item_dir_path = os.path.join(STAGING_DATA_DIR, item_id) # Base directory for item's processed data

    print(f"\nProcessing item ID: {item_id}")

    item_enrichment_success = True # Flag to track if this item's enrichment was fully successful

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            item_data = json.load(f)

        # Add a new key to store enriched data if it doesn't exist
        if "enriched_data" not in item_data:
            item_data["enriched_data"] = {
                "pages": []
            }

        # Check if this item has already been processed for enrichment
        # We can check if the 'pages' list in 'enriched_data' is populated
        # If it has the same number of pages as the PDF, assume it's done
        try:
            doc_check = fitz.open(pdf_path)
            pdf_page_count = doc_check.page_count
            doc_check.close()

            if len(item_data["enriched_data"]["pages"]) == pdf_page_count:
                 print(f"Item ID {item_id} appears to be already enriched (page count matches). Skipping.")
                 successfully_enriched_items += 1
                 processed_items_count += 1
                 continue
            elif len(item_data["enriched_data"]["pages"]) > 0 and len(item_data["enriched_data"]["pages"]) != pdf_page_count:
                 print(f"Warning: Item ID {item_id} has partial enrichment data ({len(item_data['enriched_data']['pages'])}/{pdf_page_count} pages). Re-processing.")
                 # Clear existing partial data to start fresh for this item
                 item_data["enriched_data"]["pages"] = []

        except Exception as e:
             print(f"Warning: Could not check PDF page count for item {item_id}: {e}. Proceeding with enrichment.")
             # If page count check fails, proceed with processing


        # Open the PDF
        doc = fitz.open(pdf_path)
        print(f"Opened PDF: {pdf_path} with {doc.page_count} pages.")

        # Process each page
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)

            # Extract existing OCR text
            existing_ocr_text = extract_existing_ocr(page)
            if existing_ocr_text:
                 print(f"Extracted existing OCR from page {page_num + 1}.")

            # Process the page for regions (text, sketch)
            regions_on_page = process_page_for_regions(page, item_id, page_num + 1, item_dir_path)

            # Store page enrichment data
            item_data["enriched_data"]["pages"].append({
                "page_number": page_num + 1,
                "existing_ocr": existing_ocr_text,
                "regions": regions_on_page
            })

        doc.close() # Close the PDF

        # Save the updated JSON data
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(item_data, f, indent=4, ensure_ascii=False)
            print(f"Updated JSON metadata for {json_filename}")
        except IOError as e:
            print(f"Error saving updated JSON for {json_filename}: {e}")
            item_enrichment_success = False # Mark as failed if JSON saving fails


    except (IOError, json.JSONDecodeError) as e:
        print(f"Error loading or parsing JSON file {json_path}: {e}")
        item_enrichment_success = False # Mark as failed if JSON loading fails
    except fitz.FileDataError as e:
        print(f"Error opening or reading PDF file {pdf_path}: {e}")
        item_enrichment_success = False # Mark as failed if PDF cannot be opened
    except Exception as e:
        print(f"An unexpected error occurred while processing item ID {item_id}: {e}")
        item_enrichment_success = False # Mark as failed for any other unexpected error


    # Track item success/failure
    if item_enrichment_success:
        successfully_enriched_items += 1
    else:
        failed_enriched_items += 1

    processed_items_count += 1
    print(f"Finished processing item ID: {item_id}. Processed {processed_items_count}/{total_items_to_process} items.")
    time.sleep(PROCESSING_DELAY) # Wait between processing items


print(f"\nMetadata enrichment complete.")
print(f"Successfully enriched {successfully_enriched_items} items.")
print(f"Failed to enrich {failed_enriched_items} items.")
print(f"Clipping images saved to item-specific subdirectories within '{STAGING_DATA_DIR}'.")
