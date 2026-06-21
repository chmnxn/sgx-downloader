import argparse
import logging
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

from config import load_config
from downloader import Downloader

def setup_logging(config):
    """
    Configures the logging system based on the provided configuration.
    """
    log_config = config['logging']
    log_file = Path(log_config['log_file'])
    
    # Ensure the log directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG) # Set the lowest level on the root logger

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_config['log_level_console'].upper())
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File Handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_config['log_level_file'].upper())
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    logging.info("Logging configured.")


def main():
    """
    Main function to parse arguments and run the downloader.
    """
    parser = argparse.ArgumentParser(description="SGX Derivatives Data Downloader")
    parser.add_argument(
        '--config',
        type=str,
        help="Path to the configuration file (e.g., config.yaml)",
        default='config.yaml'
    )
    parser.add_argument(
        '--date',
        type=str,
        help="A specific date to download data for in YYYY-MM-DD format."
    )
    parser.add_argument(
        '--start-date',
        type=str,
        help="The start date for a date range download in YYYY-MM-DD format."
    )
    parser.add_argument(
        '--end-date',
        type=str,
        help="The end date for a date range download in YYYY-MM-DD format."
    )
    args = parser.parse_args()

    # Load configuration and set up logging
    config = load_config(args.config)
    setup_logging(config)
    
    # Determine the date(s) to process
    dates_to_process = []
    try:
        if args.date:
            dates_to_process.append(datetime.strptime(args.date, '%Y-%m-%d').date())
        elif args.start_date and args.end_date:
            start = datetime.strptime(args.start_date, '%Y-%m-%d').date()
            end = datetime.strptime(args.end_date, '%Y-%m-%d').date()
            if start > end:
                logging.error("Start date cannot be after end date.")
                sys.exit(1)
            
            current_date = start
            while current_date <= end:
                dates_to_process.append(current_date)
                current_date += timedelta(days=1)
        else:
            # Default to today's date
            dates_to_process.append(datetime.now().date())
    except ValueError:
        logging.error("Invalid date format. Please use YYYY-MM-DD.")
        sys.exit(1)

    # Run the downloader
    downloader = Downloader(config)
    request_delay = config['network']['request_delay_seconds']

    for i, process_date in enumerate(dates_to_process):
        downloader.download_files_for_date(process_date)
        # If processing a range and it's not the last date, apply the delay
        if len(dates_to_process) > 1 and i < len(dates_to_process) - 1:
            logging.info(f"Waiting for {request_delay} seconds before next date...")
            time.sleep(request_delay)

    logging.info("SGX Downloader job finished.")


if __name__ == "__main__":
    main()
