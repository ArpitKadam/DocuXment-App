import sqlite3
import pandas as pd
import json

DB_NAME = "claim_log.db"
OUTPUT_FILE = "links.txt"

def extract_and_save_links():
    """
    Connects to the database, extracts the most recent unique document links,
    cleans them, and saves them to a text file.
    """
    try:
        with sqlite3.connect(DB_NAME) as conn:
            query = """
                        SELECT document_links FROM (
                            SELECT
                                *,
                                ROW_NUMBER() OVER(PARTITION BY document_links ORDER BY timestamp DESC) as rn
                            FROM logs
                            WHERE document_links IS NOT NULL
                        )
                        WHERE rn = 1
                        ORDER BY timestamp DESC;
                    """
            df = pd.read_sql_query(query, conn)

            if df.empty:
                print("No logs with document links found in the database.")
                return

            clean_links = []
            for item in df['document_links']:
                try:
                    # The link is stored as a JSON string '["url"]', so we parse it
                    links_list = json.loads(item)
                    if links_list:
                        # Add the first link from the list to our clean list
                        clean_links.append(links_list[0])
                except (json.JSONDecodeError, IndexError):
                    # Handle cases where the format might be incorrect or the list is empty
                    print(f"Could not parse item: {item}")
                    continue

            # Save the cleaned links to the output file
            with open(OUTPUT_FILE, 'w') as f:
                for link in clean_links:
                    f.write(link + '\n')
            
            print(f"Successfully extracted {len(clean_links)} unique links to {OUTPUT_FILE}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    extract_and_save_links()