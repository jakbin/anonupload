import yaml
from pathlib import Path
from appdirs import user_config_dir


CONFIG_DIR = Path(user_config_dir("anonupload", "anonupload"))
CONFIG_FILE = CONFIG_DIR / 'config.yaml'

default_config = {
    'custom_url': None
}

def create_default_config() -> None:
	"""Create a default config file if it doesn't exist."""
	if not CONFIG_FILE.exists():
		with open(CONFIG_FILE, 'w') as config_file:
			yaml.dump(default_config, config_file)

def load_config():
    """Load configuration from the config file."""
    try:
        with open(CONFIG_FILE, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        create_default_config()
        with open(CONFIG_FILE, 'r') as file:
            return yaml.safe_load(file)
    except yaml.YAMLError as e:
        print(f"Error reading configuration file: {e}")
        return {}

def save_config(config):
    """Save configuration to the config file."""
    try:
        with open(CONFIG_FILE, 'w') as file:
            yaml.safe_dump(config, file)
    except Exception as e:
        print(f"Error saving configuration file: {e}")

def ensure_config_dir():
    """Ensure the configuration directory exists."""
    import os
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)

def setup_config(custom_url: str = None):
    """Setup the configuration for anonupload"""
    config = load_config()
    if custom_url:
        config['custom_url'] = custom_url
    else:
        print("If you don't want to change the custom URL, just press Enter.")
        custom_url = input("Enter custom URL (or leave blank): ")
        if custom_url:
            config['custom_url'] = custom_url
    save_config(config)
    print("Configuration updated successfully.")

ensure_config_dir()
