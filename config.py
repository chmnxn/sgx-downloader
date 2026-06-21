import yaml
import logging
import sys
from pathlib import Path

# Set up a basic logger for the config module itself.
logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = 'config.yaml'

def load_config(config_path=None):
    """
    Loads the application configuration from a YAML file.

    Args:
        config_path (str, optional): The path to the configuration file.
                                     Defaults to 'config.yaml' in the script directory.

    Returns:
        dict: A dictionary containing the application configuration.

    Raises:
        SystemExit: If the configuration file cannot be found or parsed.
    """
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.absolute()
    
    if config_path is None:
        # Default to config.yaml in the same directory as the script
        path_to_check = script_dir / DEFAULT_CONFIG_PATH
    else:
        path_to_check = Path(config_path)
        # If config_path is relative, make it relative to the script directory
        if not path_to_check.is_absolute():
            path_to_check = script_dir / path_to_check
    
    logger.info(f"Attempting to load configuration from: {path_to_check.resolve()}")

    if not path_to_check.is_file():
        print(f"FATAL: Configuration file not found at '{path_to_check.resolve()}'", file=sys.stderr)
        print("Please ensure 'config.yaml' exists or provide a path using the --config argument.", file=sys.stderr)
        sys.exit(1)

    try:
        with open(path_to_check, 'r') as f:
            config = yaml.safe_load(f)
        
        # Make download_directory relative to script directory if it's not absolute
        download_dir = Path(config['download_directory'])
        if not download_dir.is_absolute():
            config['download_directory'] = str(script_dir / download_dir)
        
        # Make log file path relative to script directory if it's not absolute
        log_file = Path(config['logging']['log_file'])
        if not log_file.is_absolute():
            config['logging']['log_file'] = str(script_dir / log_file)
        
        logger.info("Configuration loaded successfully.")
        logger.info(f"Download directory set to: {config['download_directory']}")
        return config
    except yaml.YAMLError as e:
        print(f"FATAL: Error parsing YAML configuration file: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"FATAL: An unexpected error occurred while loading the config: {e}", file=sys.stderr)
        sys.exit(1)

