# 🌐 Kan AI - AI Image Text Extraction & Translation Assistant

**Kan AI** makes reading foreign text as easy as taking a photo. Whether you're traveling, studying, or trying to read a menu in a different language, just snap a picture of any document, sign, or screenshot, and Kan AI will extract the text, translate it into English or your preferred language, and explain what it means.

---

## 🚀 Live Demo & Deployment

- 🌐 **Live Deployed App (Streamlit Cloud)**: [https://mukeshdio2007-netizen-macro-snap-app-4ooe4s.streamlit.app/](https://mukeshdio2007-netizen-macro-snap-app-4ooe4s.streamlit.app/)
- 🐙 **GitHub Repository**: [https://github.com/mukeshdio2007-netizen/macro_snap](https://github.com/mukeshdio2007-netizen/macro_snap)

---

## ✨ Features

- **📸 Image Text Extraction (OCR)**: Extracts visible text from documents, signboards, menus, screenshots, posters, and handwritten notes.
- **🌐 Automatic Language Detection & Translation**: Detects source languages automatically and translates into clear English or your requested target language.
- **💬 Interactive AI Chat**: Ask follow-up questions about the extracted text, context, or detailed translations.
- **📲 1-Click WhatsApp Summary**: Generate a concise translation summary and send it directly to your WhatsApp with 1 click.
- **📷 Camera Input & Drag-and-Drop**: Easily drag & drop image files, browse files, or snap photos using your device camera.
- **⚡ Quota & Error Resilience**: Built-in automatic retry logic and model fallbacks for 100% uptime.

---

## 🛠️ Tech Stack

- **Frontend / UI**: [Streamlit](https://streamlit.io/)
- **AI Core**: [Google Gemini AI API](https://ai.google.dev/) (`google-genai`)
- **Messaging**: [Twilio WhatsApp API](https://www.twilio.com/) & Universal WhatsApp Web/App Intents (`api.whatsapp.com`)
- **Language**: Python 3.9+

---

## 📦 Setup & Local Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/mukeshdio2007-netizen/macro_snap.git
   cd macro_snap
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Secrets**:
   Create `.streamlit/secrets.toml` with your API keys:
   ```toml
   GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
   GEMINI_MODEL = "gemini-3.5-flash-lite"
   TWILIO_ACCOUNT_SID = "YOUR_TWILIO_ACCOUNT_SID"
   TWILIO_AUTH_TOKEN = "YOUR_TWILIO_AUTH_TOKEN"
   TWILIO_WHATSAPP_FROM = "whatsapp:+17372508034"
   ```

4. **Run the App**:
   ```bash
   streamlit run app.py
   ```
   Open `http://localhost:8501` in your browser.

---

## 📜 License

Distributed under the MIT License.
