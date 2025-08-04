import os
import logging
from datetime import datetime

# --- Logging Configuration ---
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Create a timestamped log file name for this specific run
log_filename = datetime.now().strftime("api_run_%Y-%m-%d_%H-%M-%S.log")
log_filepath = os.path.join(LOG_DIR, log_filename)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
    filename=log_filepath,
    filemode='w'  # Use 'w' to create a new file for each run
)
logger = logging.getLogger(__name__)
logger.info(f"Logging initialized. Log file will be saved to: {log_filepath}")
