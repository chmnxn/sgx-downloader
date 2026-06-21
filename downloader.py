import requests
import logging
import time
import zipfile
from pathlib import Path

# Get a logger for this module.
logger = logging.getLogger(__name__)

class Validator:
    """
    Contains static methods for validating downloaded files.
    """
    @staticmethod
    def is_zip_valid(filepath: Path) -> bool:
        """
        Validates a ZIP file by checking its integrity.

        Args:
            filepath (Path): The path to the ZIP file.

        Returns:
            bool: True if the file is a valid ZIP archive, False otherwise.
        """
        if not filepath.exists() or filepath.stat().st_size == 0:
            logger.warning(f"Validation failed: ZIP file is empty or does not exist at {filepath}")
            return False
        try:
            with zipfile.ZipFile(filepath, 'r') as zf:
                # testzip() checks CRC for all files in the archive.
                # Returns the name of the first corrupt file, or None if all are OK.
                corrupt_file = zf.testzip()
                if corrupt_file:
                    logger.error(f"Validation failed: Corrupt file '{corrupt_file}' found in ZIP archive: {filepath}")
                    return False
            logger.debug(f"Validation successful for ZIP file: {filepath}")
            return True
        except zipfile.BadZipFile:
            logger.error(f"Validation failed: File is not a valid ZIP archive: {filepath}")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred during ZIP validation for {filepath}: {e}")
            return False

    @staticmethod
    def is_text_file_valid(filepath: Path) -> bool:
        """
        Validates a text file by ensuring it is not empty.

        Args:
            filepath (Path): The path to the text file.

        Returns:
            bool: True if the file exists and is not empty, False otherwise.
        """
        if filepath.exists() and filepath.stat().st_size > 0:
            logger.debug(f"Validation successful for text file: {filepath}")
            return True
        logger.warning(f"Validation failed: Text file is empty or does not exist at {filepath}")
        return False


class Downloader:
    """
    Handles the entire process of downloading and managing SGX data files.
    """
    def __init__(self, config):
        """
        Initializes the Downloader with application configuration.
        """
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.config['network']['user_agent']})

    def download_files_for_date(self, target_date):
        """
        Orchestrates the download of all required files for a single day.
        This includes both dated and static files.
        """
        date_str = target_date.strftime('%Y%m%d')
        logger.info(f"--- Starting download process for date: {target_date.strftime('%Y-%m-%d')} ---")

        # Download dated files
        for url_pattern in self.config['files']['dated_patterns']:
            url = url_pattern.format(date=date_str)
            filename = Path(url).name
            
            # Construct the final path within the date-structured directory
            date_dir = Path(self.config['download_directory']) / str(target_date.year) / f"{target_date.month:02d}" / f"{target_date.day:02d}"
            final_path = date_dir / filename
            
            self._download_file(url, final_path)

        # Download static files (always overwrites to get the latest version)
        for static_file in self.config['files']['static_urls']:
            url = static_file['url']
            filename = static_file['name']
            final_path = Path(self.config['download_directory']) / filename
            self._download_file(url, final_path, overwrite=True)
            
        logger.info(f"--- Finished download process for date: {target_date.strftime('%Y-%m-%d')} ---")


    def _download_file(self, url: str, final_path: Path, overwrite: bool = False):
        """
        Handles the download of a single file with idempotency checks, retry logic,
        atomic writes, and validation.

        Args:
            url (str): The URL of the file to download.
            final_path (Path): The final destination path for the file.
            overwrite (bool): If True, always re-download the file. Used for static files.
        """
        # 1. Idempotency Check: Skip if the file exists and is valid (unless overwrite is True)
        if not overwrite and final_path.exists():
            logger.info(f"Skipping '{final_path.name}': File already exists.")
            return

        # Ensure the destination directory exists
        final_path.parent.mkdir(parents=True, exist_ok=True)
        
        temp_path = final_path.with_suffix(final_path.suffix + '.part')
        retries = self.config['retry']['max_retries']
        backoff_factor = self.config['retry']['backoff_factor']

        for attempt in range(retries + 1):
            try:
                logger.info(f"Downloading '{final_path.name}' from {url}")
                with self.session.get(url, stream=True, timeout=self.config['network']['timeout_seconds']) as r:
                    r.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
                    
                    with open(temp_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                
                logger.info(f"Successfully downloaded to temporary file: {temp_path}")

                # 2. Validation
                is_valid = False
                if final_path.suffix == '.zip':
                    is_valid = Validator.is_zip_valid(temp_path)
                else:
                    is_valid = Validator.is_text_file_valid(temp_path)

                # 3. Atomic Write (Rename)
                if is_valid:
                    temp_path.rename(final_path)
                    logger.info(f"Successfully downloaded and saved: {final_path}")
                    return  # Success, exit the retry loop
                else:
                    logger.error(f"Download failed for '{final_path.name}': File is invalid after download.")
                    temp_path.unlink(missing_ok=True) # Clean up invalid part file
                    return # Do not retry invalid files

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    logger.warning(f"Could not download '{final_path.name}': File not found (404). This may be a non-trading day.")
                    return # Don't retry on 404
                elif 500 <= e.response.status_code < 600:
                    logger.warning(f"Server error ({e.response.status_code}) for '{final_path.name}'. Retrying...")
                else:
                    logger.error(f"HTTP error for '{final_path.name}': {e}")
                    break # Don't retry on other client errors (4xx)
            
            except requests.exceptions.RequestException as e:
                logger.warning(f"Network error downloading '{final_path.name}': {e}. Retrying...")

            # If this attempt failed and there are retries left, wait before the next attempt.
            if attempt < retries:
                wait_time = backoff_factor * (2 ** attempt)
                logger.info(f"Waiting {wait_time} seconds before next attempt...")
                time.sleep(wait_time)

        logger.error(f"Failed to download '{final_path.name}' after {retries + 1} attempts.")
        # Clean up the part file if it exists after all retries failed
        temp_path.unlink(missing_ok=True)

