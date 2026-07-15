from pathlib import Path
import yaml


def load_yaml_config(config_path: str | Path) -> dict:
    """
    Load a YAML config file and return it as a Python dictionary.
    """
    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)