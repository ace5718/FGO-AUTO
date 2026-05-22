"""FGO-AUTO: Fate/Grand Order automation helper."""

__version__ = "0.2.0"

# Register submodule for static analyzers (avoids confusion with ``fgo_auto.run`` package).
from fgo_auto import run_config as run_config

__all__ = ["__version__", "run_config"]
