import requests
from bs4 import BeautifulSoup
import os
import json
from dotenv import load_dotenv
import time # Import time for adding delays
from urllib.parse import urlparse # Import urlparse

# Load environment variables from .env file
load_dotenv()

# --- Configuration from .env ---
ITEM_DETAILS_BASE_URL = os.getenv("ITEM_DETAILS_BASE_URL")
COLLECTION_SEARCH_URL = os.getenv("COLLECTION_SEARCH_URL")
COLLECTION_FACET_SETNAME = os.getenv("COLLECTION_FACET_SETNAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
STAGING_DATA_DIR = os.getenv("STAGING_DATA_DIR")

# --- Extract Base URL from ITEM_DETAILS_BASE_URL ---
# This handles cases where relative URLs are used on the site
parsed_url = urlparse(ITEM_DETAILS_BASE_URL)
BASE_SITE_URL = f"{parsed_url.scheme}://{parsed_url.netloc}"
print(f"Extracted base site URL: {BASE_SITE_URL}")


# --- Ensure Staging Directory Exists ---
if not os.path.exists(STAGING_DATA_DIR):
    os.makedirs(STAGING_DATA_DIR)
    print(f"Created staging directory: {STAGING_DATA_DIR}")

# --- Base URL for Search with Facet ---
# We will append pagination like '&page=N' to this
BASE_SEARCH_URL_WITH_FACET = f"{COLLECTION_SEARCH_URL}{COLLECTION_FACET_SETNAME}"
print(f"Using base search URL: {BASE_SEARCH_URL_WITH_FACET}")

# --- Function to Get Item URLs from a Search Page ---
def get_item_urls_from_search_page(page_url):
    """Fetches a search results page and extracts item detail URLs."""
    item_urls = []
    try:
        response = requests.get(page_url)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        soup = BeautifulSoup(response.content, 'html.parser')

        # --- Find links to individual item detail pages ---
        # Find all <a> tags that link to '/details?id='
        for link in soup.select('a[href*="/details?id="]'):
             # Ensure the link is a full URL or construct it if relative
            href = link.get('href')
            if href:
                 # If href is relative, prepend the base site URL
                 if href.startswith('/'):
                     full_url = f"{BASE_SITE_URL}{href}" # Using BASE_SITE_URL here
                 else:
                     full_url = href # Assume it's already a full URL

                 # Optional: Filter to ensure it belongs to the target collection
                 if f"facet_setname_s={COLLECTION_FACET_SETNAME}" in full_url or f"id=" in full_url:
                     # Clean up the URL to remove the facet parameter if present,
                     # as the item details URL doesn't strictly need it.
                     base_item_url = full_url.split('&')[0] if '&' in full_url else full_url
                     item_urls.append(base_item_url)


    except requests.exceptions.RequestException as e:
        print(f"Error fetching search page {page_url}: {e}")
    return list(set(item_urls)) # Use set to get unique URLs

# --- Function to Extract Data and Download PDF from an Item Detail Page ---
def extract_item_data_and_download_pdf(item_url):
    """Fetches an item detail page, extracts metadata, and downloads the PDF."""
    item_data = {
        "item_url": item_url,
        "item_id": None,
        "pdf_path": None,
        "metadata": {}
    }

    try:
        response = requests.get(item_url)
        response.raise_for_status() # Raise an exception for bad status codes
        soup = BeautifulSoup(response.content, 'html.parser')

        # --- Extract Item ID ---
        # The item ID is in the URL, extract it.
        try:
            item_data["item_id"] = item_url.split('id=')[1].split('&')[0]
        except IndexError:
            print(f"Could not extract item ID from URL: {item_url}")
            return None # Cannot process without an ID

        print(f"Processing item ID: {item_data['item_id']}")

        # --- Find and Download PDF ---
        print("Attempting to find and download PDF...")
        # Find the "Download File" link by its ID or class
        download_link = soup.select_one('#download') # Selector based on your example HTML

        if download_link:
            pdf_relative_url = download_link.get('href')
            if pdf_relative_url:
                # Construct the full PDF download URL
                # Assuming the relative URL starts with '/'
                pdf_full_url = f"{BASE_SITE_URL}{pdf_relative_url}" # Using BASE_SITE_URL here
                print(f"Found PDF download URL: {pdf_full_url}")

                # Define the path to save the PDF
                pdf_filename = f"{item_data['item_id']}.pdf"
                pdf_save_path = os.path.join(STAGING_DATA_DIR, pdf_filename)

                # Check if PDF already exists to avoid re-downloading
                if os.path.exists(pdf_save_path):
                    print(f"PDF already exists for item ID {item_data['item_id']}. Skipping download.")
                    item_data["pdf_path"] = pdf_save_path # Store the local path
                else:
                    try:
                        print(f"Downloading PDF to {pdf_save_path}...")
                        pdf_response = requests.get(pdf_full_url, stream=True)
                        pdf_response.raise_for_status() # Check for errors during download

                        with open(pdf_save_path, 'wb') as f:
                            for chunk in pdf_response.iter_content(chunk_size=8192):
                                f.write(chunk)

                        item_data["pdf_path"] = pdf_save_path # Store the local path
                        print(f"Successfully downloaded PDF for item ID {item_data['item_id']}")

                    except requests.exceptions.RequestException as e:
                        print(f"Error downloading PDF from {pdf_full_url}: {e}")
                        item_data["pdf_path"] = None # Indicate download failed
                    except IOError as e:
                        print(f"Error saving PDF to {pdf_save_path}: {e}")
                        item_data["pdf_path"] = None # Indicate save failed

            else:
                print(f"Warning: 'Download File' link found for item {item_data['item_id']}, but href is missing.")
        else:
             print(f"Warning: 'Download File' link not found for item {item_data['item_id']}. Please inspect the HTML.")


        # --- Extract Metadata from Table ---
        print("Attempting to extract metadata from table...")
        # Find the table with class "table table-bordered"
        metadata_table = soup.select_one('table.table.table-bordered')

        if metadata_table:
            #print("metadata table exists!")
            #print(metadata_table)
            # Iterate through each row in the table body
            for row in metadata_table.select('tr'):
                #print(row)
                cols = row.select('td')
                #print(cols)
                #print(len(cols))
                if len(cols) == 2:
                    field_name = cols[0].get_text(strip=True)
                    field_value = cols[1].get_text(strip=True)
                    # Clean up field names if necessary (e.g., remove trailing ':')
                    if field_name.endswith(':'):
                        field_name = field_name[:-1]
                    item_data["metadata"][field_name] = field_value
            print(f"Successfully extracted {len(item_data['metadata'])} metadata fields for item ID {item_data['item_id']}")
        else:
             print(f"Warning: Metadata table ('table.table.table-bordered') not found for item {item_data['item_id']}. Please inspect the HTML.")

        if not item_data["metadata"]:
             print(f"Warning: No metadata extracted for item {item_data['item_id']}.")


    except requests.exceptions.RequestException as e:
        print(f"Error fetching item page {item_url}: {e}")
        return None

    return item_data

# --- Main Extraction Logic ---
all_item_urls = []
page_num = 1
max_pages_to_check = 20 # Increased slightly just in case, adjust as needed
# Add a small delay between page requests to be polite to the server
REQUEST_DELAY = 1 # seconds

print("Starting search page navigation...")
while page_num <= max_pages_to_check:
    search_page_url = f"{BASE_SEARCH_URL_WITH_FACET}&page={page_num}"
    print(f"Fetching search page {page_num}: {search_page_url}")
    urls_on_page = get_item_urls_from_search_page(search_page_url)

    if not urls_on_page:
        print(f"No item URLs found on page {page_num}. Assuming end of collection.")
        break # Stop if a page returns no items

    # Check if we've already seen these URLs (might happen on the last page)
    # Also, filter out URLs that don't have an 'id=' parameter, just in case.
    valid_new_urls = [url for url in urls_on_page if url not in all_item_urls and 'id=' in url]

    if not valid_new_urls:
        print(f"No new valid item URLs found on page {page_num}. Assuming end of collection or duplicate detection.")
        break

    all_item_urls.extend(valid_new_urls)
    print(f"Found {len(valid_new_urls)} new item URLs on page {page_num}. Total unique URLs found so far: {len(all_item_urls)}")
    page_num += 1
    time.sleep(REQUEST_DELAY) # Wait between search page requests

print(f"\nFinished navigating search pages. Found a total of {len(all_item_urls)} unique item URLs.")

# --- Extract Data and Download PDF for Each Item and Save ---
print("\nStarting data extraction and PDF download for each item...")
processed_count = 0
# Add a small delay between item page requests
ITEM_REQUEST_DELAY = 2 # seconds

for item_url in all_item_urls:
    item_data = extract_item_data_and_download_pdf(item_url)

    if item_data and item_data["item_id"]:
        # Define the path to save the item's metadata JSON
        item_metadata_filename = os.path.join(STAGING_DATA_DIR, f"{item_data['item_id']}.json")

        try:
            with open(item_metadata_filename, 'w', encoding='utf-8') as f:
                # Remove the pdf_path from the JSON if the download failed,
                # or keep it as the local path if successful.
                data_to_save = item_data.copy()
                # The pdf_path is useful to keep in the JSON as a reference to the downloaded file
                json.dump(data_to_save, f, indent=4, ensure_ascii=False)
            print(f"Successfully extracted metadata and saved JSON for item ID {item_data['item_id']}")
            processed_count += 1
        except IOError as e:
            print(f"Error saving metadata JSON for item ID {item_data['item_id']} to {item_metadata_filename}: {e}")
    elif item_data is None:
         print(f"Skipping item due to extraction error: {item_url}")
    # If item_data exists but item_id is None, the error was already printed inside extract_item_data

    time.sleep(ITEM_REQUEST_DELAY) # Wait between item page requests


print(f"\nData extraction and PDF download complete. Successfully processed {processed_count} items out of {len(all_item_urls)} found URLs.")
print(f"Staged data (JSON metadata and PDF files) saved to the '{STAGING_DATA_DIR}' directory.")
