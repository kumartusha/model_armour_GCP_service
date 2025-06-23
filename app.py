import streamlit as st
import time
import requests
from google.auth import default
from google.auth.transport.requests import Request
from vertexai.generative_models import GenerativeModel


# === Config ===
PROJECT_ID = "modelarmor-463317"
REGION = "us-central1"
TEMPLATE_ID = "demo-armor-template-1"
MODEL_NAME = "gemini-2.0-flash-001"  # Configure your model here

# === Get Access Token ===
@st.cache_resource
def get_access_token():
    credentials, _ = default()
    credentials.refresh(Request())
    return credentials.token

# === Call Model Armor ===
def sanitize_prompt(user_prompt):
    url = f"https://modelarmor.{REGION}.rep.googleapis.com/v1/projects/{PROJECT_ID}/locations/{REGION}/templates/{TEMPLATE_ID}:sanitizeUserPrompt"
    headers = {
        "Authorization": f"Bearer {get_access_token()}",
        "Content-Type": "application/json"
    }
    payload = {"user_prompt_data": {"text": user_prompt}}

    start_time = time.time()
    response = requests.post(url, json=payload, headers=headers)
    end_time = time.time()

    response_time_ms = (end_time - start_time) * 1000
    return response.json(), response_time_ms

# === Pretty Print Model Armor Filters ===
def pretty_print_armor_result(result):
    st.markdown("### 🛡️ Model Armor Evaluation Summary")
    match_state = result.get("sanitizationResult", {}).get("filterMatchState", "UNKNOWN")

    if match_state == "MATCH_FOUND":
        st.error("❌ Prompt blocked due to policy violation")
    else:
        st.success("✅ Prompt is safe and allowed")

    st.markdown("### 🧾 Detailed Filter Breakdown")

    filters = {
        "dangerous": "Dangerous Content",
        "harassment": "Harassment",
        "sexually_explicit": "Sexually Explicit",
        "hate_speech": "Hate Speech",
        "pi_and_jailbreak": "PI & Jailbreak",
        "csam": "CSAM (Child Safety)",
        "malicious_uris": "Malicious URIs",
        "sdp": "SDP (Sensitive Data)"
    }

    filter_results = result.get("sanitizationResult", {}).get("filterResults", {})

    rai_filters = filter_results.get("rai", {}).get("raiFilterResult", {}).get("raiFilterTypeResults", {})
    pi_and_jailbreak_filter = filter_results.get("pi_and_jailbreak", {}).get("piAndJailbreakFilterResult", {})
    sdp_filter = filter_results.get("sdp", {}).get("sdpFilterResult", {})

    # Prepare table rows
    rows = []
    for key, label in filters.items():
        if key == "pi_and_jailbreak":
            state = pi_and_jailbreak_filter.get("matchState", "N/A")
            conf = pi_and_jailbreak_filter.get("confidenceLevel", "-")
        elif key == "sdp":
            state = sdp_filter.get("inspectResult", {}).get("matchState", "N/A")
            conf = "-"
        elif key in rai_filters:
            item = rai_filters[key]
            state = item.get("matchState", "N/A")
            conf = item.get("confidenceLevel", "-")
        else:
            # fallback to filterResults top-level keys
            found_key = next((k for k in filter_results if key in k), None)
            if found_key:
                item = filter_results.get(found_key, {})
                # Some filters have nested structure
                if isinstance(item, dict) and "matchState" not in item and len(item) > 0:
                    # Try to get first nested dict's matchState
                    first_key = next(iter(item))
                    state = item.get(first_key, {}).get("matchState", "N/A")
                    conf = item.get(first_key, {}).get("confidenceLevel", "-")
                else:
                    state = item.get("matchState", "N/A")
                    conf = item.get("confidenceLevel", "-")
            else:
                state, conf = "N/A", "-"

        emoji = "✅" if state == "NO_MATCH_FOUND" else "⚠️" if state != "N/A" else "❓"
        rows.append({"Filter Name": label, "Match State": f"{emoji} {state}", "Confidence Level": conf})

    # Show as table
    st.table(rows)

    return match_state == "MATCH_FOUND"

# === Call Gemini Model ===
def call_vertex_ai_gemini(prompt_text):
    st.markdown("### 🧠 Sending safe prompt to Gemini...")
   
    model = GenerativeModel(MODEL_NAME)  # Use configurable model name
    response = model.generate_content(prompt_text)
    return response.text

# === Streamlit UI ===
def main():
    st.title("🔐 Model Armor + Gemini Chat Demo")
    user_prompt = st.text_area("Enter your prompt here:", height=150)

    if st.button("Send Prompt"):
        if not user_prompt.strip():
            st.warning("Please enter a prompt.")
            return
        
        with st.spinner("Checking prompt safety with Model Armor..."):
            armor_result, latency = sanitize_prompt(user_prompt)
        
        blocked = pretty_print_armor_result(armor_result)
        
        if blocked:
            st.error("🚫 Prompt blocked due to policy violation. Not sending to Gemini.")
            return

        with st.spinner("Prompt safe. Sending to Gemini..."):
            gemini_response = call_vertex_ai_gemini(user_prompt)
            st.markdown("### 🤖 Gemini Response:")
            st.write(gemini_response)

if __name__ == "__main__":
    main()