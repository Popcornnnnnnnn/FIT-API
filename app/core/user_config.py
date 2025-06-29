import json
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "config" / "user_config.json"

def load_user_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_user_config(new_config: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(new_config, f, indent=2)
