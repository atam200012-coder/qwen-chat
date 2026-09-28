"""Qwen chat app for Streamlit Community Cloud (free tier).

Calls the Qwen free model through the OpenRouter API. The API key is read
from Streamlit secrets as OPENROUTER_API_KEY (App settings -> Secrets).
"""

import requests
import streamlit as st

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_ID = "qwen/qwen3.8-27b:free"
SYSTEM_PROMPT = "You are a helpful assistant."

st.set_page_config(page_title="Qwen Chat", page_icon="💬")
st.title("Qwen Chat")
st.caption("Chat with Qwen (free tier) via the OpenRouter API.")


def _api_key():
    try:
        key = st.secrets["OPENROUTER_API_KEY"]
    except Exception:
        key = ""
    return (key or "").strip()


def _ask_qwen(messages, api_key):
    try:
        resp = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL_ID,
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


if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

if prompt := st.chat_input("Ask Qwen anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    api_key = _api_key()
    if not api_key:
        reply = "OPENROUTER_API_KEY is not set. Add it under the app's Settings -> Secrets."
    else:
        with st.chat_message("assistant"):
            with st.spinner("Qwen is thinking..."):
                reply = _ask_qwen(st.session_state.messages, api_key)
            st.markdown(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})
