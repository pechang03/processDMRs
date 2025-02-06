from pathlib import Path
from functools import lru_cache

__all__ = ['get_project_root']

@lru_cache()
def get_project_root() -> Path:
    """Returns root directory of project containing processDMR.env.
    Result is cached for efficiency."""
    current = Path(__file__).resolve().parent
    while current.parent != current:
        if (current / 'processDMR.env').exists():
            return current
        current = current.parent
    raise FileNotFoundError(
        'Could not find project root with processDMR.env'
    )

