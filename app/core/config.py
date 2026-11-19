"""
Configuration and Environment Settings for DarGlobal AI Assistant.
"""

import os

# Graceful .env loading (works whether python-dotenv is installed or not)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

# OpenRouter Settings
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions")

# Target Model: NVIDIA Nemotron 3.5 Super VL (free)
PRIMARY_MODEL = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3.5-super-vl:free")

# High-reliability fallback models in case of rate limits on the free tier
FALLBACK_MODELS = [
    "nvidia/nemotron-3.5-super-vl:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemini-2.0-flash-exp:free",
    "mistralai/mistral-7b-instruct:free",
    "qwen/qwen-2.5-72b-instruct:free"
]

# Application Settings
APP_TITLE = "DarGlobal & Wasalt AI Real Estate Advisory Engine"
APP_SUBTITLE = "Applied AI Assistant powered by NVIDIA Nemotron 3.5 Super VL (Free Tier)"
PORT = int(os.getenv("PORT", 8501))
HOST = os.getenv("HOST", "0.0.0.0")

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KNOWLEDGE_BASE_PATH = os.path.join(BASE_DIR, "data", "knowledge_base.json")
