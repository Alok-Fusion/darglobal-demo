"""
OpenRouter API Client
Interfaces with OpenRouter to query the primary model: NVIDIA Nemotron 3.5 Super VL (free),
with automatic fallback cascade and fallback simulation if no API key is present.
"""

import json
import logging
import requests
from typing import List, Dict, Any, Generator, Optional
from app.core.config import OPENROUTER_BASE_URL, PRIMARY_MODEL, FALLBACK_MODELS

logger = logging.getLogger("OpenRouterClient")

SYSTEM_PROMPT = """You are the Senior AI Real Estate Advisor representing DarGlobal (London Stock Exchange listed luxury developer) and Wasalt (Saudi Arabia's premier PropTech marketplace backed by Dar Al Arkan and Quara Holding).

Your core objectives:
1. Provide authoritative, sophisticated, and commercially astute recommendations for luxury residential developments, branded residences, and prime real estate investments.
2. Accurately utilize the provided Ground Truth Property Context. When referring to specific properties, mention their brand partnerships (Pagani, Aston Martin, Lamborghini, Missoni, Trump, Elie Saab), locations, prices (in local currency and USD), bedroom layouts, and unique amenities.
3. For Saudi Arabia queries, reference Wasalt's verified listings, REGA compliance, prime Riyadh/Jeddah districts (Hittin, Al Malqa, Al Nakheel, Al Shati, Obhur), electronic auctions, and the 'Shabeek' broker matching service.
4. Keep responses COMPACT, HIGH-IMPACT, and STRUCTURED: use clean bullet points, bold key figures, and avoid long verbose intros or repetitive pleasantries so the consultation is immediately scannable without excessive scrolling.
5. If the context does not contain the answer, politely clarify and provide the closest relevant DarGlobal or Wasalt intelligence.
"""

class OpenRouterClient:
    def __init__(self, api_key: Optional[str] = None, model: str = PRIMARY_MODEL):
        self.api_key = api_key or ""
        self.model = model
        self.base_url = OPENROUTER_BASE_URL

    def set_api_key(self, api_key: str):
        self.api_key = api_key

    def set_model(self, model: str):
        self.model = model

    def generate_response(
        self,
        messages: List[Dict[str, str]],
        rag_context: str,
        temperature: float = 0.4,
        max_tokens: int = 1200
    ) -> Dict[str, Any]:
        """
        Calls OpenRouter with NVIDIA Nemotron 3.5 Super VL (free).
        Falls back to other free models if rate-limited.
        """
        # Inject RAG context into messages
        augmented_system_prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"=== VERIFIED REAL ESTATE CONTEXT (GROUND TRUTH) ===\n"
            f"{rag_context}\n"
            f"===================================================\n"
        )

        full_messages = [{"role": "system", "content": augmented_system_prompt}]
        full_messages.extend(messages)

        # If no API key provided, generate high-quality fallback synthesis from retrieved context
        if not self.api_key or self.api_key.strip() == "":
            return self._generate_local_synthesis(messages[-1]["content"], rag_context, model_used="Local RAG Engine (Add OpenRouter Key for Nemotron Live)")

        # Prepare request
        headers = {
            "Authorization": f"Bearer {self.api_key.strip()}",
            "HTTP-Referer": "https://darglobal-ai.onrender.com",
            "X-Title": "DarGlobal & Wasalt Real Estate AI",
            "Content-Type": "application/json"
        }

        # Model cascade: try requested model first, then fallbacks
        models_to_try = [self.model] + [m for m in FALLBACK_MODELS if m != self.model]

        last_error = None
        for candidate_model in models_to_try:
            payload = {
                "model": candidate_model,
                "messages": full_messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }

            try:
                logger.info(f"Dispatching query to OpenRouter with model: {candidate_model}")
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    data=json.dumps(payload),
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    return {
                        "content": content,
                        "model_used": candidate_model,
                        "status": "success"
                    }
                elif response.status_code == 429:
                    logger.warning(f"Model {candidate_model} rate-limited (429). Attempting fallback...")
                    last_error = f"Rate limit on {candidate_model} (HTTP 429)"
                    continue
                else:
                    logger.warning(f"Model {candidate_model} returned HTTP {response.status_code}: {response.text}")
                    last_error = f"HTTP {response.status_code}: {response.text}"
                    continue

            except Exception as e:
                logger.warning(f"Error querying {candidate_model}: {str(e)}")
                last_error = str(e)
                continue

        # If all API calls failed, gracefully fall back to local RAG synthesis
        logger.error(f"All OpenRouter attempts failed. Last error: {last_error}. Using local synthesis.")
        fallback_res = self._generate_local_synthesis(messages[-1]["content"], rag_context, model_used=f"Local Synthesis (OpenRouter: {last_error})")
        return fallback_res

    def _generate_local_synthesis(self, user_query: str, rag_context: str, model_used: str) -> Dict[str, Any]:
        """Provides a structured, professional response directly synthesized from RAG records."""
        header = f"### DarGlobal & Wasalt Real Estate Intelligence\n\n"
        body = (
            f"Based on your query: *\"{user_query}\"*, here are the curated recommendations from our verified luxury portfolio:\n\n"
            f"{rag_context}\n\n"
            f"> **Advisor Note:** For detailed floor plans, payment schedules, or private viewing appointments, "
            f"please select a property above or connect with our specialized advisory desk."
        )
        return {
            "content": header + body,
            "model_used": model_used,
            "status": "fallback"
        }
