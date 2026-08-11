"""
Centralized Multi-Provider AI Client Service (Groq & Gemini Support).
Single reusable service for AI API integration across the platform.
Supports:
1. Groq Cloud API (Keys starting with 'gsk_') using Llama-3.3-70B / Llama-3.1-8B models.
2. Google Gemini API (Keys starting with 'AIzaSy' or standard Gemini format).
3. Graceful fallback logic.
"""

import os
import json
import time
import urllib.request
import urllib.error
import warnings

# Suppress google.generativeai deprecation warning on startup
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)
import google.generativeai as genai

from app.config.settings import settings
from app.ai.utils import clean_markdown_text, parse_json_from_ai_response
from app.utils.logger import logger


class GeminiService:
    """
    Centralized Singleton AI Client Service supporting both Groq Cloud and Google Gemini.
    """

    def __init__(self):
        self.api_key = (
            os.getenv("GROQ_API_KEY") or
            os.getenv("GEMINI_API_KEY") or
            getattr(settings, "GEMINI_API_KEY", "") or
            ""
        ).strip()
        
        self.is_configured = False
        self.provider = "none"
        self.model_name = "unknown"
        self._initialize_client()

    def _initialize_client(self):
        """
        Detects API Key type and configures Groq Cloud or Google Gemini client.
        """
        if not self.api_key or len(self.api_key) < 5:
            logger.info("No AI API Key configured. System will operate with dynamic context-aware fallback.")
            self.is_configured = False
            return

        # 1. Detect Groq API Key ('gsk_...')
        if self.api_key.startswith("gsk_"):
            self.provider = "groq"
            self.model_name = "llama-3.3-70b-versatile"
            self.is_configured = True
            logger.info(f"Groq AI Service initialized successfully with key prefix 'gsk_' (Model: {self.model_name}).")
            return

        # 2. Detect Google Gemini API Key
        try:
            genai.configure(api_key=self.api_key)
            try:
                self.model = genai.GenerativeModel("gemini-flash-latest")
                self.model_name = "gemini-flash-latest"
            except Exception:
                self.model = genai.GenerativeModel("models/gemini-flash-latest")
                self.model_name = "models/gemini-flash-latest"

            self.provider = "gemini"
            self.is_configured = True
            logger.info(f"Gemini Service initialized successfully with model '{self.model_name}'.")
        except Exception as e:
            logger.error(f"Failed to configure Gemini client: {e}")
            self.is_configured = False

    def generate_text(self, prompt: str, max_retries: int = 1) -> str:
        """
        Generates text using Groq Cloud API or Gemini API based on configured key.
        """
        if not self.is_configured:
            return ""

        # A. GROQ API DISPATCH
        if self.provider == "groq":
            return self._generate_groq_text(prompt, max_retries=max_retries)

        # B. GEMINI API DISPATCH
        if self.provider == "gemini":
            for attempt in range(max_retries + 1):
                try:
                    logger.info(f"Sending prompt to Gemini API (Model: {self.model_name}, Attempt {attempt + 1})...")
                    response = self.model.generate_content(prompt)
                    if response and response.text:
                        cleaned_output = clean_markdown_text(response.text.strip())
                        logger.info("Gemini API response received successfully.")
                        return cleaned_output
                except Exception as e:
                    logger.error(f"Gemini API error on model '{self.model_name}': {e}")
                    for alt_name in ["gemini-pro-latest", "gemini-2.0-flash", "models/gemini-flash-latest"]:
                        if alt_name != self.model_name:
                            try:
                                fallback_model = genai.GenerativeModel(alt_name)
                                response = fallback_model.generate_content(prompt)
                                if response and response.text:
                                    logger.info(f"Fallback model '{alt_name}' succeeded.")
                                    return clean_markdown_text(response.text.strip())
                            except Exception as fb_err:
                                pass
                    if attempt < max_retries:
                        time.sleep(0.5)

        return ""

    def _generate_groq_text(self, prompt: str, max_retries: int = 1) -> str:
        """
        Dispatches request to Groq Cloud REST API (OpenAI-compatible endpoint).
        """
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        models_to_try = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"]

        for attempt in range(max_retries + 1):
            for m_name in models_to_try:
                try:
                    logger.info(f"Sending prompt to Groq API (Model: {m_name}, Attempt {attempt + 1})...")
                    payload = {
                        "model": m_name,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.7,
                        "max_tokens": 1800
                    }

                    req = urllib.request.Request(
                        url,
                        data=json.dumps(payload).encode("utf-8"),
                        headers=headers
                    )

                    with urllib.request.urlopen(req, timeout=20) as resp:
                        res_data = json.loads(resp.read().decode("utf-8"))
                        if "choices" in res_data and len(res_data["choices"]) > 0:
                            content = res_data["choices"][0]["message"]["content"]
                            if content:
                                logger.info(f"Groq API ({m_name}) responded successfully.")
                                return clean_markdown_text(content.strip())
                except urllib.error.HTTPError as he:
                    err_body = he.read().decode("utf-8", errors="ignore")
                    logger.error(f"Groq HTTP Error {he.code} on model '{m_name}': {err_body}")
                except Exception as e:
                    logger.error(f"Groq API error on model '{m_name}': {e}")

            if attempt < max_retries:
                time.sleep(0.5)

        return ""

    def generate_json(self, prompt: str, max_retries: int = 1) -> dict:
        """
        Generates structured JSON object using AI API.
        """
        json_prompt = f"{prompt}\n\nIMPORTANT: Return ONLY a valid, raw JSON object matching the requested structure. Do NOT include any markdown block quotes, intro, or outro text."
        raw_text = self.generate_text(json_prompt, max_retries=max_retries)
        if raw_text:
            return parse_json_from_ai_response(raw_text)
        return {}


# Global Singleton Instance
gemini_service = GeminiService()
