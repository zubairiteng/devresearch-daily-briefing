"""Provider-agnostic LLM summarizer supporting Gemini, OpenAI, Anthropic, and heuristic fallback."""
import json
import logging
from typing import Optional
import httpx

from .base import SummaryResult
from .heuristic import generate_heuristic_summary
from fetchers.base import RawItem
from config.settings import settings
from config.profile_loader import UserProfile

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a senior full-stack engineer and computer science colleague writing a daily briefing for an MS CS university lecturer, placement officer, NAVTTC skills trainer, and AI researcher.

Writing guidelines (STRICT):
1. Write like a smart, pragmatic human colleague chatting over coffee. NOT like an AI assistant.
2. Absolutely DO NOT use robotic cliches: 'In conclusion', 'Delve', 'It is worth noting', 'Moreover', 'Testament to', 'Revolutionize', 'Tapestry', 'Beacon'.
3. No bullet-point stuffing, no emoji spam.
4. Keep it conversational, concise, and specific. Include real numbers, architectures, and entity names.
5. Never invent facts, benchmarks, or links.

Output strictly valid JSON with these keys:
{
  "headline": "Catchy, concise human headline (max 10 words)",
  "summary_text": "2 to 4 punchy sentences explaining what is new, why it matters, and any known limitations or fixes over previous versions.",
  "why_it_matters": "One clear sentence on how this relates to teaching, placement, cloud/dev, or active research.",
  "research_gap": "If this is a research paper or emerging concept, describe a concrete open research gap or publication opportunity. Otherwise null."
}
"""


class LLMSummarizer:
    def __init__(self, profile: UserProfile):
        self.profile = profile
        self.provider = settings.LLM_PROVIDER.lower()

    async def summarize(self, item: RawItem, category: str) -> SummaryResult:
        """Summarize an item using configured LLM provider or fallback."""
        # 1. Try Gemini
        if self.provider == "gemini" and settings.GEMINI_API_KEY:
            try:
                res = await self._call_gemini(item, category)
                if res:
                    return res
            except Exception as e:
                logger.warning(f"Gemini summarization failed, falling back to heuristic: {e}")

        # 2. Try OpenAI
        elif self.provider == "openai" and settings.OPENAI_API_KEY:
            try:
                res = await self._call_openai(item, category)
                if res:
                    return res
            except Exception as e:
                logger.warning(f"OpenAI summarization failed, falling back to heuristic: {e}")

        # 3. Try Anthropic
        elif self.provider == "anthropic" and settings.ANTHROPIC_API_KEY:
            try:
                res = await self._call_anthropic(item, category)
                if res:
                    return res
            except Exception as e:
                logger.warning(f"Anthropic summarization failed, falling back to heuristic: {e}")

        # Default fallback to heuristic engine
        return generate_heuristic_summary(item, category, self.profile)

    async def _call_gemini(self, item: RawItem, category: str) -> Optional[SummaryResult]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
        user_prompt = f"Category: {category}\nTitle: {item.title}\nSource: {item.source_name}\nContent:\n{item.content[:2000]}"
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": f"{SYSTEM_PROMPT}\n\n{user_prompt}"}]}
            ],
            "generationConfig": {"temperature": 0.4, "response_mime_type": "application/json"}
        }
        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(text)
                return SummaryResult(
                    headline=parsed.get("headline", item.title),
                    summary_text=parsed.get("summary_text", item.summary),
                    why_it_matters=parsed.get("why_it_matters", ""),
                    research_gap=parsed.get("research_gap")
                )
        return None

    async def _call_openai(self, item: RawItem, category: str) -> Optional[SummaryResult]:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}
        user_prompt = f"Category: {category}\nTitle: {item.title}\nSource: {item.source_name}\nContent:\n{item.content[:2000]}"
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.4
        }
        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                text = data["choices"][0]["message"]["content"]
                parsed = json.loads(text)
                return SummaryResult(
                    headline=parsed.get("headline", item.title),
                    summary_text=parsed.get("summary_text", item.summary),
                    why_it_matters=parsed.get("why_it_matters", ""),
                    research_gap=parsed.get("research_gap")
                )
        return None

    async def _call_anthropic(self, item: RawItem, category: str) -> Optional[SummaryResult]:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": settings.ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        user_prompt = f"Category: {category}\nTitle: {item.title}\nSource: {item.source_name}\nContent:\n{item.content[:2000]}\nOutput ONLY JSON."
        payload = {
            "model": "claude-3-haiku-20240307",
            "max_tokens": 1024,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": user_prompt}],
            "temperature": 0.4
        }
        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                text = data["content"][0]["text"]
                parsed = json.loads(text)
                return SummaryResult(
                    headline=parsed.get("headline", item.title),
                    summary_text=parsed.get("summary_text", item.summary),
                    why_it_matters=parsed.get("why_it_matters", ""),
                    research_gap=parsed.get("research_gap")
                )
        return None
