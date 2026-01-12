import json
import os
import logging

def load_config(config_path="config/config.json"):
    """Loads the configuration from a JSON file."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"Config file not found at {config_path}")
        return None
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from {config_path}")
        return None

def setup_logging(log_level=logging.INFO):
    """Sets up basic logging."""
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
