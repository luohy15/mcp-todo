import os
import toml
import platform

def get_default_config():
    """Get default configuration"""
    return {
        "data_file": "~/.local/share/todo/tasks.jsonl",
        "config_file": "~/.config/todo/config.toml"
    }

def load_config():
    """Load configuration from TOML file or create with defaults if it doesn't exist"""
    # toml config file
    CONFIG_FILE = os.path.expanduser(get_default_config()["config_file"])
    # ensure the directory exists
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)

    # Create default config if file doesn't exis
    if not os.path.exists(CONFIG_FILE):
        config = get_default_config()
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            toml.dump(config, f)
    else:
        # read existing config file
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = toml.load(f)
            # Merge with defaults to ensure all required fields exis
            defaults = get_default_config()
            for key, value in defaults.items():
                if key not in config:
                    config[key] = value

    DATA_FILE = os.path.expanduser(config["data_file"])
    # ensure the directory exists
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

    return config, DATA_FILE

config, DATA_FILE = load_config()
