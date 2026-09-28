"""At Am's AI Hub - my private AI center.

Runs on Streamlit Community Cloud (free tier).

- Chat with any free OpenRouter model (picker at the top; the list refreshes
  automatically from OpenRouter, with a built-in fallback).
- Quick links to my own AI accounts below the chat.

The API key lives in Streamlit Secrets as OPENROUTER_API_KEY
(App settings -> Secrets). It is never written into the code.
"""

import requests
import streamlit as st

OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"

SYSTEM_PROMPT = "You are a helpful assistant."

# Verified 2026-09-29; used only if the live model list cannot be fetched.
FALLBACK_FREE_MODELS = [
    "qwen/qwen3.8-27b:free",
    "google/gemma-4-31b-it:free",
    "google/gemma-4-26b-a4b-it:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    "nvidia/nemotron-3.5-lightning:free",
    "nvidia/nemotron-3.5-content-safety:free",
    "cohere/north-mini-code:free",
    "liquid/lfm-2.5-2.6b:free",
    "dots-studio/dots-3-note-preview:free",
    "inclusionai/ling-3.0-flash-sante:free",
    "poolside/laguna-s-2.1:free",
    "poolside/laguna-xs-2.1:free",
    "thinkingmachines/inkling:free",
    "thinkingmachines/inkling-small:free",
]

FRIENDLY_NAMES = {
    "qwen/qwen3.8-27b:free": "Qwen 3.8 27B",
    "google/gemma-4-31b-it:free": "Google Gemma 4 31B",
    "google/gemma-4-26b-a4b-it:free": "Google Gemma 4 26B",
    "nvidia/nemotron-3-ultra-550b-a55b:free": "Nvidia Nemotron 3 Ultra 550B",
    "nvidia/nemotron-3-super-120b-a12b:free": "Nvidia Nemotron 3 Super 120B",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free": "Nvidia Nemotron 3 Nano (reasoning)",
    "nvidia/nemotron-3.5-lightning:free": "Nvidia Nemotron 3.5 Lightning",
    "nvidia/nemotron-3.5-content-safety:free": "Nvidia Nemotron 3.5 Content Safety",
    "cohere/north-mini-code:free": "Cohere North Mini Code",
    "liquid/lfm-2.5-2.6b:free": "Liquid LFM 2.5 2.6B",
    "dots-studio/dots-3-note-preview:free": "Dots Studio Dots 3 Note (preview)",
    "inclusionai/ling-3.0-flash-sante:free": "InclusionAI Ling 3.0 Flash",
    "poolside/laguna-s-2.1:free": "Poolside Laguna S 2.1",
    "poolside/laguna-xs-2.1:free": "Poolside Laguna XS 2.1",
    "thinkingmachines/inkling:free": "Thinking Machines Inkling",
    "thinkingmachines/inkling-small:free": "Thinking Machines Inkling Small",
}

MY_AIS = [
    ("Poe", "https://poe.com"),
    ("Perplexity", "https://www.perplexity.ai"),
    ("Claude", "https://claude.ai"),
    ("Gemini", "https://gemini.google.com"),
    ("Kimi", "https://www.kimi.com"),
    ("Grok", "https://grok.com"),
    ("DeepSeek", "https://chat.deepseek.com"),
    ("Le Chat", "https://chat.mistral.ai"),
]


def _pretty(model_id: str) -> str:
    if model_id in FRIENDLY_NAMES:
        return FRIENDLY_NAMES[model_id]
    name = model_id.split("/")[-1].replace(":free", "")
    return name.replace("-", " ").replace("_", " ").title()


@st.cache_data(ttl=3600)
def _free_models():
    """Fetch the current free-model list from OpenRouter (public endpoint)."""
    try:
        resp = requests.get(OPENROUTER_MODELS_URL, timeout=30)
        resp.raise_for_status()
        ids = [m["id"] for m in resp.json().get("data", []) if m.get("id", "").endswith(":free")]
        if ids:
            return sorted(ids)
    except Exception:
        pass
    return list(FALLBACK_FREE_MODELS)


def _api_key() -> str:
    try:
        key = st.secrets["OPENROUTER_API_KEY"]
    except Exception:
        key = ""
    return (key or "").strip()


def _ask(messages, model_id: str, api_key: str) -> str:
    try:
        resp = requests.post(
            OPENROUTER_CHAT_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model_id,
                "messages": messages,
                "max_tokens": 1024,
                "temperature": 0.7,
            },
            timeout=120,
        )
    except requests.RequestException as exc:
        return f"Request failed: {exc}"
    if resp.status_code != 200:
        return f"OpenRouter error {resp.status_code}: {resp.text[:500]}"
    try:
        return resp.json()["choices"][0]["message"]["content"]
    except (KeyError, IndexError, ValueError):
        return f"Unexpected API response: {resp.text[:500]}"


st.set_page_config(page_title="At Am's AI Hub", page_icon="🤖")
st.title("🤖 At Am's AI Hub")
st.caption("My private AI center - free models on top, my AI accounts below.")

models = _free_models()
default_idx = models.index("qwen/qwen3.8-27b:free") if "qwen/qwen3.8-27b:free" in models else 0
model_id = st.selectbox("Choose a model", models, index=default_idx, format_func=_pretty)

if st.button("Clear chat"):
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

if prompt := st.chat_input("Ask anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    api_key = _api_key()
    if not api_key:
        reply = "OPENROUTER_API_KEY is not set. Add it under the app's Settings -> Secrets."
    else:
        with st.chat_message("assistant"):
            with st.spinner(f"{_pretty(model_id)} is thinking..."):
                reply = _ask(st.session_state.messages, model_id, api_key)
            st.markdown(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})

st.divider()
st.subheader("My AIs")
st.caption("My own accounts - tap to open.")
cols = st.columns(4)
for i, (name, url) in enumerate(MY_AIS):
    with cols[i % 4]:
        st.link_button(name, url, use_container_width=True)

st.caption("Chat uses free OpenRouter models. Keys stay in Secrets, never in code.")
