from typing import Any, FrozenSet, Optional, Tuple

from ..config import (
    get_config_value,
    get_ini_value,
    get_ini_bool,
    load_prompt_template,
    load_prompt_tags_template,
    get_tag_detail_level,
)
from ..domain.services.ai_service import AiService

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
        "moonshotai/kimi-k2-instruct",
        "moonshotai/kimi-k2-instruct-0905",
        "openai/gpt-oss-120b",
        "whisper-large-v3",
        "whisper-large-v3-turbo",
    }
)


def _build_prompt_from_template(
    commit_message: str,
    commit_diff: str,
    version_type: str,
    max_length: int,
    locale: str,
    is_tag: bool = False,
) -> str:
    if is_tag:
        template: Optional[str] = load_prompt_tags_template()
        detail_level: str = get_tag_detail_level()
    else:
        template = load_prompt_template()
        detail_level = "concise"

    diff_truncated: str = commit_diff[:2000] if len(commit_diff) > 2000 else commit_diff

    if template:
        try:
            return (
                template.format(
                    maxLength=max_length,
                    locale=locale,
                    type=version_type,
                    detailLevel=detail_level,
                )
                + f"\n\nOriginal commit message: {commit_message}\n\nDiff:\n```\n{diff_truncated}\n```"
            )
        except KeyError:
            pass

    if is_tag:
        return f"""Generate a comprehensive git tag message (release note) based on the following commit.

Rules:
- Maximum {max_length} characters for the subject line
- Use imperative mood (e.g., "Add", "Fix", "Update", "Remove", "Refactor")
- No emojis, no decorations, no special characters
- No period at the end of the subject line
- Be specific about what changed, not why
- Language: {locale}

Format: {version_type}

Generate a {detail_level} detailed message with conventional commit format.

Original commit message: {commit_message}

Diff:
```
{diff_truncated}
```

Output only the tag message. No explanations, no alternatives, no additional text."""

    return f"""Generate a concise git tag message based on the following diff.

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


class OpenAiCompatibleAdapter(AiService):
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
        client: Any = self._get_client()

        prompt: str = _build_prompt_from_template(
            commit_message=commit_message,
            commit_diff=commit_diff,
            version_type=version_type,
            max_length=max_length,
            locale=locale,
            is_tag=True,
        )

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
        client: Any = self._get_client()

        diff_truncated: str = (
            commit_diff[:1500] if len(commit_diff) > 1500 else commit_diff
        )

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


def _is_local_provider(base_url: Optional[str]) -> bool:
    if not base_url:
        raise ValueError(
            "Base URL not configured.\n"
            "Configure it with: igv config set OPENAI.baseURL <url>"
        )

    if not api_key:
        if _is_local_provider(base_url):
            api_key = "ollama"
        else:
            raise ValueError(
                "API key not configured.\n"
                "Configure it with: igv config set OPENAI.key <your-api-key>"
            )

    model: str = get_config_value("OPENAI.model") or "llama3.2"
    return OpenAiCompatibleAdapter(api_key=api_key, base_url=base_url, model=model)


def generate_tag_message(
    commit_message: str,
    commit_diff: str,
    version_type: str,
    max_length: int = 72,
    locale: str = "es",
) -> Optional[str]:
    return get_ai_service().generate_tag_message(
        commit_message=commit_message,
        commit_diff=commit_diff,
        version_type=version_type,
        max_length=max_length,
        locale=locale,
    )


def determine_version_type(commit_message: str, commit_diff: str) -> Tuple[str, str]:
    return get_ai_service().determine_version_type(
        commit_message=commit_message,
        commit_diff=commit_diff,
    )


def list_available_models() -> list:
    api_key: Optional[str] = get_config_value("OPENAI.key")
    base_url: Optional[str] = get_config_value("OPENAI.baseURL")

    if not base_url:
        return []

    if not api_key:
        if _is_local_provider(base_url):
            api_key = "ollama"
        else:
            return []

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key, base_url=base_url)
        response = client.models.list()

        is_groq: bool = "groq.com" in base_url

        result: list = []
        for m in response.data:
            ctx: Optional[int] = None
            model_extra: dict = getattr(m, "model_extra", None) or {}
            for field in ("context_window", "context_length"):
                val = getattr(m, field, None) or model_extra.get(field)
                if val is not None:
                    ctx = int(val)
                    break

            is_free: Optional[bool] = None
            pricing: dict = model_extra.get("pricing") or {}
            if pricing:
                prompt_cost = str(pricing.get("prompt", "")).strip()
                completion_cost = str(pricing.get("completion", "")).strip()
                if prompt_cost == "0" and completion_cost == "0":
                    is_free = True
                elif prompt_cost or completion_cost:
                    is_free = False
            if m.id.endswith(":free"):
                is_free = True
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


def get_ollama_model_details(model_name: str) -> Optional[dict]:
    base_url: Optional[str] = get_config_value("OPENAI.baseURL")
    if not base_url or ("localhost" not in base_url and "127.0.0.1" not in base_url):
        return None

    import requests

    try:
        response = requests.post(
            f"{base_url}/api/show",
            json={"model": model_name},
            timeout=10,
        )
        if response.status_code == 200:
            data = response.json()
            model_info: dict = data.get("model_info", {})
            details: dict = data.get("details", {})

            ctx_key = f"{model_name.split(':')[0]}.context_length"
            context_length = model_info.get(ctx_key)

            return {
                "context_length": context_length,
                "parameters": details.get("parameter_size", ""),
                "format": details.get("format", ""),
            }
    except Exception:
        pass
    return None


def list_ollama_models() -> list:
    base_url: Optional[str] = get_config_value("OPENAI.baseURL")
    if not base_url or ("localhost" not in base_url and "127.0.0.1" not in base_url):
        return []

    base_url = base_url.replace("/v1", "").rstrip("/")

    import requests

    try:
        response = requests.get(f"{base_url}/api/tags", timeout=10)
        if response.status_code == 200:
            data = response.json()
            result: list = []
            for m in data.get("models", []):
                result.append(
                    {
                        "id": m.get("name", ""),
                        "size": m.get("size", 0),
                        "modified_at": m.get("modified_at", ""),
                    }
                )
            return result
    except Exception:
        pass
    return []
