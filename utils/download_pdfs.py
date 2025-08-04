import os
import requests
from urllib.parse import urlparse
import urllib.parse

# --- Configuration ---
LINKS_FILE = "links.txt"
PDF_DIR = "pdfs"

def download_pdfs_from_links():
    """
    Reads URLs from a text file, downloads the PDFs, and saves them
    to a specified directory.
    """
    # 1. Ensure the output directory exists
    if not os.path.exists(PDF_DIR):
        os.makedirs(PDF_DIR)
        print(f"Created directory: '{PDF_DIR}'")

    # 2. Read the links from the file
    try:
        with open(LINKS_FILE, 'r') as f:
            # Read all lines and remove any empty ones
            urls = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Error: The file '{LINKS_FILE}' was not found.")
        return

    if not urls:
        print(f"'{LINKS_FILE}' is empty. Nothing to download.")
        return

    print(f"Found {len(urls)} links in '{LINKS_FILE}'. Starting download process...")

    # 3. Loop through each URL and download the PDF
    for url in urls:
        try:
            # Generate a clean filename from the URL
            path = urlparse(url).path
            filename = os.path.basename(path)
            # Decode URL-encoded characters (like '%20' for spaces)
            filename = urllib.parse.unquote(filename)
            save_path = os.path.join(PDF_DIR, filename)

            # 4. Skip the file if it already exists
            if os.path.exists(save_path):
                print(f"'{filename}' already exists. Skipping.")
                continue

            print(f"Downloading '{filename}'...")
            
            # Make the request to download the file
            response = requests.get(url, timeout=30)
            response.raise_for_status()  # Raise an error for bad status codes (like 404)

            # 5. Save the content to the pdfs folder
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            print(f" -> Successfully saved to '{save_path}'")

        except requests.RequestException as e:
            print(f" -> FAILED to download from {url[:60]}... Error: {e}")
        except Exception as e:
            print(f" -> An unexpected error occurred for {url[:60]}... Error: {e}")
    
    print("\nDownload process finished.")


if __name__ == "__main__":
    # Ensure you have the requests library installed
    try:
        import requests
    except ImportError:
        print("The 'requests' library is not installed.")
        print("Please install it by running: pip install requests")
    else:
        download_pdfs_from_links()