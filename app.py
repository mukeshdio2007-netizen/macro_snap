import json
import os
from google import genai
from google.genai import types
import streamlit as st
from twilio.rest import Client as TwilioClient

from prompts import (
    SYSTEM_PROMPT,
    WELCOME_MESSAGE_TEMPLATE,
    SUMMARY_REQUEST_PROMPT
)

def load_secret(key, default=None):
    try:
        if key in st.secrets:
            val = st.secrets[key]
            if val:
                return val
    except Exception:
        pass

    env_val = os.getenv(key)
    if env_val:
        return env_val

    for fname in [".streamlit/secrets.toml", ".streamlit/Secrets.toml"]:
        if os.path.exists(fname):
            try:
                import toml
                parsed = toml.load(fname)
                if key in parsed and parsed[key]:
                    return parsed[key]
            except Exception:
                pass
    return default


GEMINI_API_KEY = load_secret("GEMINI_API_KEY")
GEMINI_MODEL = load_secret("GEMINI_MODEL", "gemini-3.5-flash-lite")
TWILIO_ACCOUNT_SID = load_secret("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = load_secret("TWILIO_AUTH_TOKEN")
TWILIO_CONTENT_SID = load_secret("TWILIO_CONTENT_SID")
TWILIO_WHATSAPP_FROM = load_secret("TWILIO_WHATSAPP_FROM", "whatsapp:+17372508034")

if not GEMINI_API_KEY:
    st.error("Gemini API key is missing! Please configure GEMINI_API_KEY in .streamlit/secrets.toml or as an environment variable.")
    st.stop()


@st.cache_resource
def get_gemini_client(api_key):
    return genai.Client(api_key=api_key)


@st.cache_resource
def get_twilio_client(account_sid, auth_token):
    if account_sid and auth_token:
        return TwilioClient(account_sid, auth_token)
    return None


gemini_client = get_gemini_client(GEMINI_API_KEY)
twilio_client = get_twilio_client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def clean_whatsapp_text(text):
    if not text:
        return "No nutrition summary available."
    text = " ".join(text.split())  # collapse whitespace/newlines
    return text[:1500] + "..." if len(text) > 1500 else text


def send_whatsapp(to_number, user_name, summary):
    if not twilio_client:
        return False, "Twilio client is not configured (missing SID or Auth Token)."
    try:
        to_clean = to_number.strip().replace(" ", "")
        if not to_clean.startswith("whatsapp:"):
            to_clean = f"whatsapp:{to_clean}"

        kwargs = {
            "from_": TWILIO_WHATSAPP_FROM,
            "to": to_clean,
        }
        if TWILIO_CONTENT_SID and TWILIO_CONTENT_SID.strip():
            content_variables = json.dumps(
                {"1": user_name, "2": clean_whatsapp_text(summary)}, ensure_ascii=False
            )
            kwargs["content_sid"] = TWILIO_CONTENT_SID
            kwargs["content_variables"] = content_variables
        else:
            kwargs["body"] = f"Hi {user_name}!\n\nHere is your MacroSnap summary:\n\n{summary}"

        message = twilio_client.messages.create(**kwargs)
        return True, message.sid
    except Exception as error:
        err_msg = str(error)
        if "trial accounts have limited parameter access" in err_msg or "ContentSid Required" in err_msg or "predefined SMS templates" in err_msg:
            return False, (
                "Twilio Trial Account Restriction: Free trial accounts require an upgraded Twilio account or pre-approved Content Template to send outbound WhatsApp messages. "
                "Your daily summary has been posted in the chat below!"
            )
        return False, err_msg


def render_message(message):
    with st.chat_message(message["role"]):
        if message["kind"] == "text":
            st.write(message["content"])
        elif message["kind"] == "image":
            st.image(message["content"])


def add_message(role, kind, content):
    st.session_state.messages.append({"role": role, "kind": kind, "content": content})
    render_message(st.session_state.messages[-1])


import time


def ask_gemini(parts):
    try:
        return st.session_state.chat.send_message(parts).text
    except Exception:
        pass

    # Automatic fallback cascade to alternate working models if primary model quota is exhausted
    fallback_models = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.8-flash", "gemini-flash-latest"]
    for alt_model in fallback_models:
        try:
            res = gemini_client.models.generate_content(
                model=alt_model,
                contents=parts
            )
            if res and res.text:
                return res.text
        except Exception:
            continue

    return "⚠️ All Gemini AI model quotas are currently busy. Please wait a moment and try again!"


def format_whatsapp_number(phone_str):
    digits = "".join(filter(str.isdigit, phone_str))
    if len(digits) == 10:
        # Default 10 digit numbers to India (+91)
        digits = f"91{digits}"
    return digits


# Step 1: Onboarding (Name and WhatsApp number)
if "onboarded" not in st.session_state:
    st.title("🌐 MacroSnap")
    st.caption("Snap it. Translate it. Text yourself the results.")

    with st.form("onboarding_form"):
        name = st.text_input("Your Name", placeholder="e.g. Mukesh")
        col_code, col_num = st.columns([1, 2])
        with col_code:
            country_code = st.selectbox(
                "Country Code",
                ["+91 (India)", "+1 (US/CA)", "+44 (UK)", "+61 (AU)", "+971 (UAE)", "Other"],
                index=0
            )
        with col_num:
            phone_input = st.text_input("WhatsApp Number", placeholder="9080543824")

        submitted = st.form_submit_button("Let's go 🚀")

    if submitted:
        if not name.strip() or not phone_input.strip():
            st.warning("Please fill in both your name and WhatsApp number.")
        else:
            # Format number cleanly with country code
            code_prefix = country_code.split(" ")[0].replace("+", "")
            raw_digits = "".join(filter(str.isdigit, phone_input))
            if raw_digits.startswith(code_prefix):
                full_number = f"+{raw_digits}"
            else:
                full_number = f"+{code_prefix}{raw_digits}"

            st.session_state.name = name.strip()
            st.session_state.whatsapp_number = full_number
            # Activate Gemini AI chat
            st.session_state.chat = gemini_client.chats.create(
                model=GEMINI_MODEL,
                config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
            )
            st.session_state.messages = []
            st.session_state.onboarded = True
            st.rerun()
    st.stop()


# Sidebar Controls & File Uploads
with st.sidebar:
    st.header("🌐 MacroSnap")
    st.markdown(f"**User:** {st.session_state.name}\n\n**WhatsApp:** {st.session_state.whatsapp_number}")
    st.divider()
    st.subheader("📸 Upload Image to Translate")
    st.caption("Drag & drop an image, browse files, or take a photo.")
    
    sidebar_file = st.file_uploader("Drag & Drop or Browse Image", type=["jpg", "jpeg", "png", "webp"], key="sidebar_uploader")
    
    with st.expander("📷 Camera Input"):
        camera_file = st.camera_input("Take a photo to translate", key="camera_input")
    
    st.divider()
    if st.button("🔄 Reset Session / Logout", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# Process image from sidebar uploader or camera input
active_upload = sidebar_file or camera_file
if active_upload is not None:
    upload_id = f"{active_upload.name}_{active_upload.size}"
    if st.session_state.get("last_processed_upload") != upload_id:
        st.session_state.last_processed_upload = upload_id
        photo_bytes = active_upload.getvalue()
        add_message("user", "image", photo_bytes)
        parts = [
            types.Part.from_bytes(data=photo_bytes, mime_type=active_upload.type or "image/jpeg"),
            "Extract all visible text from this image, identify the source language, translate it into English, and provide a clear explanation."
        ]
        with st.spinner("Extracting & translating text..."):
            answer = ask_gemini(parts)
        add_message("assistant", "text", answer)
        st.rerun()


import urllib.parse


def get_whatsapp_direct_url(phone_number, user_name, summary):
    formatted_phone = format_whatsapp_number(phone_number)
    text = f"🌐 *MacroSnap Translation Summary for {user_name}*\n\n{summary}"
    encoded = urllib.parse.quote(text)
    return f"https://api.whatsapp.com/send?phone={formatted_phone}&text={encoded}"


header_col, button_col = st.columns([5, 2], vertical_alignment="center")

with header_col:
    st.title("🌐 MacroSnap")

with button_col:
    if st.button("📤 Send to WhatsApp", use_container_width=True):
        if len(st.session_state.messages) <= 1:
            st.info("💡 Upload an image or send a message first, then click here to generate & text your translation summary!")
        else:
            with st.spinner("Summarizing your translations..."):
                summary = ask_gemini([SUMMARY_REQUEST_PROMPT])
            
            wa_url = get_whatsapp_direct_url(
                st.session_state.whatsapp_number, st.session_state.name, summary
            )
            
            # Display summary in chat UI with direct link
            add_message(
                "assistant",
                "text",
                f"📋 **Image Translation Summary:**\n\n{summary}\n\n📲 **[Click here to open in WhatsApp]({wa_url})**"
            )
            
            # Send message via Twilio API directly to user's WhatsApp phone number
            success, info = send_whatsapp(
                st.session_state.whatsapp_number, st.session_state.name, summary
            )
            if success:
                st.success(f"📱 Message sent to your WhatsApp number ({st.session_state.whatsapp_number})! Check your phone 📲")
            else:
                st.warning(f"ℹ️ Twilio status: {info}")
                
            st.link_button("💬 Open & Send in WhatsApp App / Web", wa_url, use_container_width=True)

st.caption(
    f"Logged in as **{st.session_state.name}** - updates go to **{st.session_state.whatsapp_number}**"
)

if not st.session_state.messages:
    add_message(
        "assistant",
        "text",
        WELCOME_MESSAGE_TEMPLATE.format(name=st.session_state.name),
    )
else:
    for message in st.session_state.messages:
        render_message(message)


user_input = st.chat_input(
    "Ask a question or upload an image containing text (use 📎 paperclip or sidebar to upload)",
    accept_file=True,
    file_type=["jpg", "jpeg", "png", "webp"],
)

if user_input:
    photo = user_input.files[0] if user_input.files else None
    text = user_input.text
    parts = []

    if photo is not None:
        photo_bytes = photo.getvalue()
        add_message("user", "image", photo_bytes)
        parts.append(types.Part.from_bytes(data=photo_bytes, mime_type=photo.type or "image/jpeg"))
    if text:
        add_message("user", "text", text)
        parts.append(text)
    elif photo is not None:
        parts.append("Extract all visible text from this image, identify the source language, translate it into English, and explain the meaning.")

    with st.spinner("Extracting & translating text..."):
        answer = ask_gemini(parts)
    add_message("assistant", "text", answer)

