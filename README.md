# **SGX Derivatives Data Downloader**

A simple, robust, and configurable Python command-line utility to download daily derivatives data from the Singapore Exchange (SGX) website. This tool is designed to be run as a scheduled job (e.g., via cron).

## **Features**

* **Configurable:** All settings (URLs, paths, timeouts) are managed in config.yaml.  
* **Idempotent:** The script automatically skips downloads for files that already exist, making it safe to re-run.  
* **Robust:** Includes automatic retries with exponential backoff for transient network/server errors.  
* **Atomic Writes:** Downloads files to a temporary .part file and only renames upon success, preventing corrupted files.  
* **Data Validation:** Performs basic integrity checks on downloaded ZIP archives.  
* **Flexible Date Handling:**  
  * Download for the current day (default).  
  * Download for a specific historical date.  
  * Download for a date range to backfill missing data.  
* **Structured Logging:** Logs to both console and a file with configurable verbosity.

## **Setup**

1. **Prerequisites:**  
   * Python 3.8 or higher.  
2. Create the Project Files:  
   Place all the provided Python files (main.py, downloader.py, config.py) and configuration files (config.yaml, requirements.txt) in a single directory.  
3. Install Dependencies:  
   Navigate to the project directory and install the required Python packages, preferably within a virtual environment.  
   pip install \-r requirements.txt

4. **Configure** the **Application:**  
   * Open config.yaml in a text editor.  
   * Adjust the download\_directory to your desired location.  
   * Review other settings like timeouts and retry attempts.

## **Usage**

The script is run from the command line.

#### **To download data for the current day:**

This is the default behavior.

python main.py

#### **To download data for a specific historical date:**

python main.py \--date 2025-08-22

#### **To backfill data for a date range:**

This is useful for recovering data from days where the job failed.

python main.py \--start-date 2025-08-18 \--end-date 2025-08-20

#### **To use a custom configuration file:**

python main.py \--config /path/to/your/custom\_config.yaml

## **Automation with cron**

To run this script automatically every weekday, you can add an entry to your crontab.

1. Open your crontab for editing:  
   crontab \-e

2. Add the following line to run the script at 6:30 PM (18:30) from Monday to Friday. **Make sure to use absolute paths** for the Python interpreter and the script.  
   \# Run the SGX downloader every weekday at 6:30 PM  
   30 18 \* \* 1-5 /path/to/your/venv/bin/python /path/to/your/sgx\_downloader/main.py \>\> /path/to/your/sgx\_downloader/logs/cron.log 2\>&1

This setup will execute the script and append all console output (both stdout and stderr) to a cron.log file for later inspection.
