"""Environment + path configuration."""

from __future__ import annotations

import os
import pathlib
from typing import Final

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

PROJECT_ROOT: Final = pathlib.Path(__file__).resolve().parent.parent.parent
AUDIO_DIR: Final = PROJECT_ROOT / "audio"
ENROLLMENT_DIR: Final = AUDIO_DIR / "enrollment"
VERIFICATION_DIR: Final = AUDIO_DIR / "verification"
DATA_DIR: Final = PROJECT_ROOT / "data"

AZURE_REGION: Final = os.environ.get("AZURE_SPEECH_REGION", "westeurope")
AZURE_HOST: Final = f"{AZURE_REGION}.api.cognitive.microsoft.com"


def get_azure_key() -> str:
    """Read the Azure Speech API key from the environment.

    Set AZURE_SPEECH_KEY in your shell or a .env file at the project root.
    """
    key = os.environ.get("AZURE_SPEECH_KEY")
    if not key:
        raise RuntimeError(
            "AZURE_SPEECH_KEY is not set. Export it, or copy .env.example to .env "
            "and fill in your key. Get one at https://portal.azure.com → Speech resource."
        )
    return key
