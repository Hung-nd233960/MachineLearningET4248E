# pylint: disable = missing-module-docstring
import os
import toml


def load_toml_config(filename: str = "config.toml") -> dict:
    """
    Loads a TOML configuration file.

    Args:
        filename (str): Path to the TOML file.

    Returns:
        dict: Parsed configuration.
        Example usage:
        config = load_toml_config()
        print(config)
    """
    if not os.path.isfile(filename):
        raise FileNotFoundError(f"Config file '{filename}' not found.")
    with open(filename, "r", encoding= "utf-8") as f:
        config = toml.load(f)
    return config

if __name__ == "__main__":
    config_dict = load_toml_config()
    print(config_dict)
