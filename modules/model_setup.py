import ollama
import streamlit as st


MODEL_NAME = "gemma3:4b"


def ollama_is_running() -> bool:
    """Return True if the local Ollama server responds."""
    try:
        ollama.list()
        return True
    except Exception:
        return False


def model_is_installed(model: str = MODEL_NAME) -> bool:
    """Return True if the given model is already pulled locally."""
    try:
        models = ollama.list()
        names = []
        for m in models.get("models", []):
            name = m.get("model") or m.get("name") or ""
            names.append(name)
        return any(model in n for n in names)
    except Exception:
        return False


def pull_model_with_progress_bar(model: str = MODEL_NAME) -> bool:
    """Stream the pull and show a Streamlit progress bar."""
    progress_bar = st.progress(0)
    status_text = st.empty()
    status_text.info(
        f"Downloading **{model}** — this is a one-time setup. "
        "It may take several minutes depending on your connection."
    )

    last_status = ""
    try:
        for chunk in ollama.pull(model, stream=True):
            status = chunk.get("status", "")
            completed = chunk.get("completed", 0)
            total = chunk.get("total", 0)

            if total:
                pct = int(completed / total * 100)
                progress_bar.progress(min(pct, 100))
                status_text.info(
                    f"Downloading **{model}** — {pct}% "
                    f"({completed // (1024 * 1024)} MB / {total // (1024 * 1024)} MB)"
                )
            elif status and status != last_status:
                status_text.info(f"{status}…")
                last_status = status

        progress_bar.progress(100)
        status_text.success(f"✅ **{model}** is ready.")
        return True
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"Failed to download the model: {e}")
        return False