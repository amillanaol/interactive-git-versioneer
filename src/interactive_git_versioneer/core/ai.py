"""OpenAI-compatible adapter for AI-powered text generation.

Implements the AiService port using the `openai` library, which is
compatible with OpenAI, Groq, OpenRouter and any provider that follows
the OpenAI API spec.

Usage (direct):
    service = OpenAiCompatibleAdapter(api_key=..., base_url=..., model=...)
    message = service.generate_tag_message(...)

Usage (from config):
    service = get_ai_service()
    message = service.generate_tag_message(...)
"""

from typing import Any, FrozenSet, Optional, Tuple

from ..config import get_config_value
from ..domain.services.ai_service import AiService

# Models available on Groq's free plan.
# Source: https://console.groq.com/docs/rate-limits (fetched 2026-02-25)
# Models NOT in this set require a Developer/paid plan on Groq.
_GROQ_FREE_MODELS: FrozenSet[str] = frozenset(
    {
        "allam-2-7b",
        "canopylabs/orpheus-arabic-saudi",
        "canopylabs/orpheus-v1-english",
        "groq/compound",
        "groq/compound-mini",
        "llama-3.1-8b-instant",
        "llama-3.3-70b-versatile",
        "meta-llama/llama-4-maverick-17b-128e-instruct",
        "meta-llama/llama-4-scout-17b-16e-instruct",
        "meta-llama/llama-guard-4-12b",
        # Versioned variant of the free moonshotai/kimi-k2-instruct
        "moonshotai/kimi-k2-instruct",
        "moonshotai/kimi-k2-instruct-0905",
        "openai/gpt-oss-120b",
        "whisper-large-v3",
        "whisper-large-v3-turbo",
    }
)


class OpenAiCompatibleAdapter(AiService):
    """Concrete AiService implementation using the openai library.

    Works with any OpenAI-compatible provider:
    - OpenAI   (base_url: https://api.openai.com/v1)
    - Groq     (base_url: https://api.groq.com/openai/v1)
    - OpenRouter (base_url: https://openrouter.ai/api/v1)
    - Any self-hosted OpenAI-compatible endpoint

    Args:
        api_key: The API key for the provider.
        base_url: The base URL of the OpenAI-compatible endpoint.
        model: The model identifier to use for completions.

    Raises:
        ImportError: If the 'openai' library is not installed.
    """

    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self._api_key = api_key
        self._base_url = base_url
        self._model = model

    def _get_client(self) -> Any:
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "The 'openai' library is not installed.\n"
                "Install it with: pip install openai"
            )
        return OpenAI(api_key=self._api_key, base_url=self._base_url)

    def generate_tag_message(
        self,
        commit_message: str,
        commit_diff: str,
        version_type: str,
        max_length: int = 72,
        locale: str = "es",
    ) -> Optional[str]:
        """Generate a concise git tag message from a commit diff."""
        client: Any = self._get_client()

        diff_truncated: str = commit_diff[:2000] if len(commit_diff) > 2000 else commit_diff

        prompt: str = f"""Generate a concise git tag message based on the following diff.

Rules:
- Maximum {max_length} characters
- Use imperative mood (e.g., "Add", "Fix", "Update", "Remove", "Refactor")
- No emojis, no decorations, no special characters
- No period at the end
- Be specific about what changed, not why
- Language: {locale}
- Version type context: {version_type}

Original commit message: {commit_message}

Diff:
```
{diff_truncated}
```

Output only the tag message. No explanations, no alternatives, no additional text."""

        response: Any = client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a git commit message generator. Output only the message, nothing else.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=100,
            temperature=0.3,
            stop=["\n\n", "---", "```"],
        )

        result: str = response.choices[0].message.content.strip()
        result = result.strip("\"'`")

        if "\n" in result:
            result = result.split("\n")[0].strip()

        return result

    def determine_version_type(
        self,
        commit_message: str,
        commit_diff: str,
    ) -> Tuple[str, str]:
        """Classify a commit into a semantic version type (major/minor/patch)."""
        client: Any = self._get_client()

        diff_truncated: str = commit_diff[:1500] if len(commit_diff) > 1500 else commit_diff

        prompt: str = f"""Classify this git commit into semantic version type.

Commit message: {commit_message}

Diff:
```
{diff_truncated}
```

Rules:
- major: breaking changes, API changes, major restructuring
- minor: new features, significant improvements (backwards compatible)
- patch: bug fixes, docs, small refactoring, maintenance

Output format (exactly 2 lines):
TYPE: [major|minor|patch]
REASON: [max 10 words in Spanish]"""

        response: Any = client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a semantic versioning classifier. Output only TYPE and REASON lines.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=50,
            temperature=0.2,
            stop=["---", "```", "\n\n\n"],
        )

        result: str = response.choices[0].message.content.strip()

        version_type: str = "patch"
        reason: str = "Cambio menor"

        for line in result.split("\n"):
            line = line.strip()
            line_upper: str = line.upper()
            if line_upper.startswith("TYPE:") or line_upper.startswith("TIPO:"):
                tipo: str = line.split(":", 1)[1].strip().lower()
                if tipo in ("major", "minor", "patch"):
                    version_type = tipo
            elif (
                line_upper.startswith("REASON:")
                or line_upper.startswith("RAZÓN:")
                or line_upper.startswith("RAZON:")
            ):
                reason = line.split(":", 1)[1].strip()

        return version_type, reason


def get_ai_service() -> AiService:
    """Factory: build an AiService from the current application configuration.

    Reads OPENAI.key, OPENAI.baseURL and OPENAI.model from ~/.igv/config.json
    and returns a configured OpenAiCompatibleAdapter.

    Returns:
        A ready-to-use AiService instance.

    Raises:
        ValueError: If the API key or base URL are not configured.
    """
    api_key: Optional[str] = get_config_value("OPENAI.key")
    base_url: Optional[str] = get_config_value("OPENAI.baseURL")

    if not api_key:
        raise ValueError(
            "API key not configured.\n"
            "Configure it with: igv config set OPENAI.key <your-api-key>"
        )

    if not base_url:
        raise ValueError(
            "Base URL not configured.\n"
            "Configure it with: igv config set OPENAI.baseURL <url>"
        )

    model: str = get_config_value("OPENAI.model") or "llama-3.3-70b-versatile"
    return OpenAiCompatibleAdapter(api_key=api_key, base_url=base_url, model=model)


# ── Backward-compatible module-level helpers ──────────────────────────────────
# These preserve the existing public API so no callers need to change.

def generate_tag_message(
    commit_message: str,
    commit_diff: str,
    version_type: str,
    max_length: int = 72,
    locale: str = "es",
) -> Optional[str]:
    """Generate a git tag message. Delegates to the configured AiService."""
    return get_ai_service().generate_tag_message(
        commit_message=commit_message,
        commit_diff=commit_diff,
        version_type=version_type,
        max_length=max_length,
        locale=locale,
    )


def determine_version_type(commit_message: str, commit_diff: str) -> Tuple[str, str]:
    """Determine the semantic version type. Delegates to the configured AiService."""
    return get_ai_service().determine_version_type(
        commit_message=commit_message,
        commit_diff=commit_diff,
    )


def list_available_models() -> list:
    """Fetch the model catalog from the configured provider's API.

    Calls the provider's ``/models`` endpoint using the credentials in
    ``~/.igv/config.json``.  Extra fields (context window, owner) are
    read from provider-specific extensions that Groq and OpenRouter
    attach to the standard OpenAI model object.

    Returns:
        List of dicts sorted by model id, each containing:
        - ``id`` (str): model identifier as used in API calls.
        - ``context_window`` (Optional[int]): max context in tokens, or None.
        - ``owned_by`` (str): provider/owner name (may be empty).

        Returns an empty list when config is incomplete or any network
        or API error occurs.
    """
    api_key: Optional[str] = get_config_value("OPENAI.key")
    base_url: Optional[str] = get_config_value("OPENAI.baseURL")

    if not api_key or not base_url:
        return []

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key, base_url=base_url)
        response = client.models.list()

        is_groq: bool = "groq.com" in base_url

        result: list = []
        for m in response.data:
            # Context window field name varies by provider:
            # Groq → context_window, OpenRouter → context_length.
            # Both may appear as direct attributes or inside model_extra.
            ctx: Optional[int] = None
            model_extra: dict = getattr(m, "model_extra", None) or {}
            for field in ("context_window", "context_length"):
                val = getattr(m, field, None) or model_extra.get(field)
                if val is not None:
                    ctx = int(val)
                    break

            # Determine if the model is free to use.
            # Groq: no pricing field in API; all models are free within rate limits.
            # OpenRouter: pricing dict with prompt/completion as string cost per token;
            #   "0" means free. Models with :free suffix are always free.
            is_free: Optional[bool] = None
            pricing: dict = model_extra.get("pricing") or {}
            if pricing:
                prompt_cost = str(pricing.get("prompt", "")).strip()
                completion_cost = str(pricing.get("completion", "")).strip()
                if prompt_cost == "0" and completion_cost == "0":
                    is_free = True
                elif prompt_cost or completion_cost:
                    is_free = False
            # OpenRouter convention: :free suffix always means free
            if m.id.endswith(":free"):
                is_free = True
            # Groq: use the documented free-plan model list as the source of truth.
            # Models absent from _GROQ_FREE_MODELS require a paid plan.
            if is_free is None and is_groq:
                is_free = m.id in _GROQ_FREE_MODELS

            result.append(
                {
                    "id": m.id,
                    "context_window": ctx,
                    "owned_by": getattr(m, "owned_by", "") or "",
                    "is_free": is_free,
                }
            )

        result.sort(key=lambda x: x["id"])
        return result

    except Exception:
        return []
