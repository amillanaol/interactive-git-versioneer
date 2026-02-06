"""
Módulo de integración con API de OpenAI/Groq para generación de mensajes.

Usa la librería openai para compatibilidad con Groq y otros proveedores.
"""

from typing import Any, Optional, Tuple

from ..config import get_config_value


def get_openai_client() -> Any:
    """Creates and returns a configured OpenAI client.

    This function attempts to import the `OpenAI` library and then
    initializes an `OpenAI` client using API key and base URL retrieved
    from the application's configuration.

    Returns:
        Any: The configured OpenAI client instance (type `openai.OpenAI`).

    Raises:
        ImportError: If the 'openai' library is not installed.
        ValueError: If the API key or base URL are not configured.
    """
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError(
            "The 'openai' library is not installed.\n"
            "Install it with: pip install openai"
        )

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

    return OpenAI(api_key=api_key, base_url=base_url)


def generate_tag_message(
    commit_message: str,
    commit_diff: str,
    version_type: str,
    max_length: int = 72,
    locale: str = "es",
) -> Optional[str]:
    """Generates a git tag message using an AI API.

    Constructs a prompt based on the commit message, diff, version type,
    maximum length, and desired locale, then sends it to the configured
    AI model to generate a concise tag message.

    Args:
        commit_message (str): The original commit message.
        commit_diff (str): The diff of the commit (changes made).
        version_type (str): The type of version being tagged (e.g., "major", "minor", "patch").
        max_length (int): The maximum allowed length for the generated message. Defaults to 72.
        locale (str): The language for the generated message (e.g., "es", "en"). Defaults to "es".

    Returns:
        Optional[str]: The AI-generated tag message, or None if generation fails.

    Raises:
        ValueError: If configuration for the AI API is missing.
        ImportError: If the 'openai' library is not installed.
    """
    client: Any = get_openai_client()
    model: str = get_config_value("OPENAI.model") or "llama-3.3-70b-versatile"

    # Limitar el diff para evitar tokens excesivos
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

    response: Any = client.chat.completions.create(  # Use Any for response object
        model=model,
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

    # Limpiar posibles artefactos
    result = result.strip("\"'`")

    # Si hay múltiples líneas, tomar solo la primera
    if "\n" in result:
        result = result.split("\n")[0].strip()

    return result


def determine_version_type(commit_message: str, commit_diff: str) -> Tuple[str, str]:
    """Determines the semantic version type of a commit using an AI.

    Analyzes the commit message and diff to classify the change as
    "major", "minor", or "patch" based on predefined rules, and provides
    a brief justification.

    Args:
        commit_message (str): The original commit message.
        commit_diff (str): The diff of the commit (changes made).

    Returns:
        Tuple[str, str]: A tuple containing:
            - str: The determined version type ("major", "minor", or "patch").
            - str: A brief justification for the version type.

    Raises:
        ValueError: If configuration for the AI API is missing.
        ImportError: If the 'openai' library is not installed.
    """
    client: Any = get_openai_client()
    model: str = get_config_value("OPENAI.model") or "llama-3.3-70b-versatile"

    # Limitar el diff
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

    response: Any = client.chat.completions.create(  # Use Any for response object
        model=model,
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

    # Parsear respuesta
    version_type: str = "patch"  # Default
    reason: str = "Cambio menor"

    for line in result.split("\n"):
        line: str = line.strip()
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
