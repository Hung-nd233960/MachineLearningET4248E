# medfabric/config.py
import tomllib
from pathlib import Path
from typing import Any


CONFIG_PATH = Path.cwd() / "config.toml"


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

BASAL_CENTRAL_MAX = CRITERION.get("BasalCentral", 4)
BASAL_CORTEX_MAX = CRITERION.get("BasalCortex", 3)
CORONA_MAX = CRITERION.get("CoronaRadiata", 3)
DATA_PATH = PATHS.get("data", "/data")

SCORE_LIMITS = {
    "basal_score_central_left": BASAL_CENTRAL_MAX,
    "basal_score_central_right": BASAL_CENTRAL_MAX,
    "basal_score_cortex_left": BASAL_CORTEX_MAX,
    "basal_score_cortex_right": BASAL_CORTEX_MAX,
    "corona_score_left": CORONA_MAX,
    "corona_score_right": CORONA_MAX,
}
