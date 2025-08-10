import os
import requests
from urllib.parse import urlparse
import urllib.parse

LINKS_FILE = "links.txt"
DOWNLOADS_DIR = "data"

def download_files_from_links():
    """
    Reads URLs from a text file, downloads the files (any type),
    and saves them to a specified directory.
    """
    # 1. Ensure the output directory exists
    if not os.path.exists(DOWNLOADS_DIR):
        os.makedirs(DOWNLOADS_DIR)
        print(f"✅ Created directory: '{DOWNLOADS_DIR}'")

    # 2. Read the links from the file
    try:
        with open(LINKS_FILE, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"❌ Error: The file '{LINKS_FILE}' was not found.")
        return

    if not urls:
        print(f"'{LINKS_FILE}' is empty. Nothing to download.")
        return

    print(f"🔎 Found {len(urls)} links in '{LINKS_FILE}'. Starting download process...")

    # 3. Loop through each URL and download the file
    for url in urls:
        try:
            path = urlparse(url).path
            filename = os.path.basename(path)
            filename = urllib.parse.unquote(filename)
            
            save_path = os.path.join(DOWNLOADS_DIR, filename)

            # 4. Skip the file if it already exists
            if os.path.exists(save_path):
                print(f"👍 '{filename}' already exists. Skipping.")
                continue

            print(f"Downloading '{filename}'...")

            response = requests.get(url, timeout=60, stream=True)
            response.raise_for_status()

            # 5. Save the content to the downloads folder
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f" -> ✅ Successfully saved to '{save_path}'")

        except requests.RequestException as e:
            print(f" -> ❌ FAILED to download {filename}. Error: {e}")
        except Exception as e:
            print(f" -> ❌ An unexpected error occurred for {filename}. Error: {e}")
    
    print("\nDownload process finished.")


if __name__ == "__main__":
    try:
        import requests
    except ImportError:
        print("The 'requests' library is not installed.")
        print("Please install it by running: pip install requests")
    else:
        download_files_from_links()