"""Gemini chat app for Streamlit Community Cloud (free tier).

Calls Google's Gemini API (free tier). The API key is read from Streamlit
secrets as GEMINI_API_KEY (App settings -> Secrets).
"""

import requests
import streamlit as st

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
SYSTEM_PROMPT = "You are a helpful assistant."

st.set_page_config(page_title="Gemini Chat", page_icon="💬")
st.title("Gemini Chat")
st.caption("Chat with Gemini (free tier) via the Google AI Studio API.")


def _api_key():
    try:
        key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        key = ""
    return (key or "").strip()


def _to_gemini_contents(messages):
    contents = []
    for m in messages:
        role = m.get("role")
        if role == "system":
            continue
        gem_role = "model" if role == "assistant" else "user"
        contents.append({"role": gem_role, "parts": [{"text": m.get("content", "")}]})
    return contents


def _ask_gemini(messages, api_key):
    body = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": _to_gemini_contents(messages),
        "generationConfig": {"maxOutputTokens": 1024, "temperature": 0.7},
    }
    try:
        resp = requests.post(
            GEMINI_URL,
            headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
            json=body,
            timeout=120,
        )
    except requests.RequestException as exc:
        return f"Request failed: {exc}"
    if resp.status_code != 200:
        return f"Gemini API error {resp.status_code}: {resp.text[:500]}"
    try:
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, ValueError):
        return f"Unexpected API response: {resp.text[:500]}"


if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

if prompt := st.chat_input("Ask Gemini anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    api_key = _api_key()
    if not api_key:
        reply = "GEMINI_API_KEY is not set. Add it under the app's Settings -> Secrets."
    else:
        with st.chat_message("assistant"):
            with st.spinner("Gemini is thinking..."):
                reply = _ask_gemini(st.session_state.messages, api_key)
            st.markdown(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})
