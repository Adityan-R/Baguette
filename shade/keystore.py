import keyring
from rich.prompt import Prompt
from .renderer import console

KEYRING_SERVICE = "shade"

PROVIDER_KEY_NAMES = {
    "openai":    "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini":    "GEMINI_API_KEY",
    "groq":      "GROQ_API_KEY",
}

PROVIDER_URLS = {
    "openai":    "https://platform.openai.com/api-keys",
    "anthropic": "https://console.anthropic.com/keys",
    "gemini":    "https://aistudio.google.com/app/apikey",
    "groq":      "https://console.groq.com/keys",
}

def get_key(provider: str) -> str | None:
    env_var = PROVIDER_KEY_NAMES.get(provider)
    if not env_var:
        return None
    import os
    # Check env var first, then keyring
    if env_val := os.environ.get(env_var):
        return env_val
    try:
        return keyring.get_password(KEYRING_SERVICE, env_var)
    except Exception:
        return None

def set_key(provider: str, key: str) -> None:
    env_var = PROVIDER_KEY_NAMES.get(provider)
    if not env_var:
        raise ValueError(f"Unknown provider: {provider}")
    keyring.set_password(KEYRING_SERVICE, env_var, key)

def delete_key(provider: str) -> None:
    env_var = PROVIDER_KEY_NAMES.get(provider)
    if env_var:
        try:
            keyring.delete_password(KEYRING_SERVICE, env_var)
        except keyring.errors.PasswordDeleteError:
            pass # Already deleted or not found

def prompt_and_store_key(provider: str) -> str:
    console.print(f"\n[bold]No API key found for [cyan]{provider}[/cyan].[/bold]")
    console.print(f"Get yours at: {PROVIDER_URLS.get(provider, 'the provider website')}")
    key = Prompt.ask(f"Enter your {PROVIDER_KEY_NAMES.get(provider, 'API Key')}", password=True)
    if not key.strip():
        raise ValueError("API key cannot be empty.")
    set_key(provider, key.strip())
    console.print(f"[green]✓ Key stored in system keychain. You won't be asked again.[/green]\n")
    return key.strip()

def list_stored_keys() -> dict[str, bool]:
    return {
        provider: get_key(provider) is not None
        for provider in PROVIDER_KEY_NAMES
    }
