"""
Single shared LLM client built on LangChain.

- One client per process (v1 created five separate Gemini clients).
- Structured outputs via `with_structured_output(PydanticModel)` instead of regex-parsing JSON.
- Timeouts, retries and call telemetry; every method returns None on failure so callers can
  fall back to the question bank / offline content instead of returning HTTP 500.
"""
import logging
import threading
import time

from config import Config

log = logging.getLogger(__name__)


class LLMService:
    def __init__(self, config=Config):
        self.provider = getattr(config, 'LLM_PROVIDER', 'offline')
        self.model_name = getattr(config, 'LLM_MODEL', None)
        self._model = None
        self._lock = threading.Lock()
        self.stats = {'calls': 0, 'failures': 0, 'total_ms': 0}
        if self.provider == 'gemini' and config.GEMINI_API_KEY:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                self._model = ChatGoogleGenerativeAI(
                    model=config.LLM_MODEL,
                    google_api_key=config.GEMINI_API_KEY,
                    temperature=config.LLM_TEMPERATURE,
                    timeout=config.LLM_TIMEOUT,
                    max_retries=config.LLM_MAX_RETRIES,
                )
            except Exception as exc:  # pragma: no cover - depends on env
                log.warning('Could not initialise Gemini (%s); running offline', exc)
                self.provider = 'offline'
        else:
            self.provider = 'offline'

    @property
    def available(self):
        return self._model is not None

    def set_model(self, model, provider='custom'):
        """Inject any LangChain chat model (used by tests and for other providers)."""
        self._model = model
        self.provider = provider

    def _record(self, start, ok):
        with self._lock:
            self.stats['calls'] += 1
            self.stats['total_ms'] += int((time.perf_counter() - start) * 1000)
            if not ok:
                self.stats['failures'] += 1

    def structured(self, schema, messages):
        """Invoke the model and parse into `schema`. Returns a pydantic instance or None."""
        if not self.available:
            return None
        start = time.perf_counter()
        try:
            result = self._model.with_structured_output(schema).invoke(messages)
            ok = result is not None
            self._record(start, ok)
            return result
        except Exception as exc:
            log.warning('LLM structured call failed: %s', exc)
            self._record(start, False)
            return None

    def chat(self, messages):
        """Plain chat completion. Returns text or None."""
        if not self.available:
            return None
        start = time.perf_counter()
        try:
            msg = self._model.invoke(messages)
            self._record(start, True)
            content = msg.content
            if isinstance(content, list):  # some providers return content blocks
                content = ''.join(b.get('text', '') if isinstance(b, dict) else str(b) for b in content)
            return content
        except Exception as exc:
            log.warning('LLM chat call failed: %s', exc)
            self._record(start, False)
            return None

    def info(self):
        calls = self.stats['calls']
        return {
            'provider': self.provider,
            'model': self.model_name if self.available else None,
            'available': self.available,
            'calls': calls,
            'failures': self.stats['failures'],
            'avg_latency_ms': round(self.stats['total_ms'] / calls) if calls else 0,
        }
