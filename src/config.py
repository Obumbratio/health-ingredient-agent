import os
from pathlib import Path
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

# Localizar la raíz del proyecto y cargar .env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings:
    # Modelos y LLM
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "")

    # openFDA (Opcional, funciona sin key con límite de 40 req/min)
    OPENFDA_API_KEY: str = os.getenv("OPENFDA_API_KEY", "")

    # Headers recomendados por la política de uso de Open Food Facts
    USER_AGENT: str = os.getenv(
        "USER_AGENT",
        "HealthIngredientAgent/1.0 (HackathonProject; contact@devpost.local)"
    )

    # Timeouts de red (segundos)
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "25"))


settings = Settings()
