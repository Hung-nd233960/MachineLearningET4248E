# medfabric/config.py
import tomllib
from pathlib import Path
from typing import Any

CONFIG_PATH = Path("/medfabric/config.toml")


def load_config() -> dict[str, Any]:
    """Load the full config.toml as a dict."""
    with CONFIG_PATH.open("rb") as f:
        return tomllib.load(f)


def get_criterion() -> dict[str, int]:
    """Return scoring thresholds from [criterion] section."""
    return load_config().get("criterion", {})


def get_paths() -> dict[str, str]:
    """Return paths from [path] section."""
    return load_config().get("path", {})


CRITERION = get_criterion()
PATHS = get_paths()

BASEL_CENTRAL_MAX = CRITERION.get("BasalCentral", 4)
BASEL_CORTEX_MAX = CRITERION.get("BasalCortex", 3)
CORONA_MAX = CRITERION.get("CoronaRadiata", 3)
DATA_PATH = PATHS.get("data", "/data")
