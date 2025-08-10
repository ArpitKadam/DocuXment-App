import sqlite3
import re
from pathlib import Path

DB_FILE = "claim_log.db"
OUTPUT_FILE = "links.txt"

def find_all_urls(text_block: str) -> set:
    """Uses a regular expression to find all URLs within a block of text."""
    # This pattern finds anything that starts with http:// or https://
    url_pattern = r'https?://[^\s,"\'\]\[<>]+'
    urls = re.findall(url_pattern, text_block)
    
    cleaned_urls = {url.strip() for url in urls}
    return cleaned_urls

def main():
    """Main function to run the extraction process."""
    print("🚀 Starting corrected link extraction...")
    
    if not Path(DB_FILE).exists():
        print(f"❌ ERROR: Database file not found at '{DB_FILE}'. Please check the path.")
        return
    
    all_unique_links = set()

    try:
        # Step 1: Connect to the SQLite database.
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            print(f"✅ Connected to database: {DB_FILE}")

            # Step 2: Query the database to get all entries from the 'document_links' column.
            query = "SELECT document_links FROM logs WHERE document_links IS NOT NULL AND document_links != ''"
            cursor.execute(query)
            
            rows = cursor.fetchall()
            print(f"🔍 Found {len(rows)} total entries to process.")

            # Step 3: Loop through every entry and extract the URLs.
            for row in rows:
                link_data = row[0]
                urls_found = find_all_urls(link_data)
                all_unique_links.update(urls_found)

        # Step 4: Write all the unique links to the output file.
        sorted_links = sorted(list(all_unique_links))
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            for link in sorted_links:
                f.write(link + '\n')

        print("\n" + "="*40)
        print(f"Total unique links saved: {len(sorted_links)}")
        print(f"📁 Output file is ready: {OUTPUT_FILE}")
        print("="*40)

    except sqlite3.Error as e:
        print(f"❌ DATABASE ERROR: Could not read from '{DB_FILE}'. Details: {e}")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

# This line makes the script runnable from the command line.
if __name__ == "__main__":
    main()