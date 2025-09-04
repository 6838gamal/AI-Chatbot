import os
import json
import streamlit as st
import pandas as pd
from google import genai

# ---------------------------
# Gemini API setup
# ---------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    st.error("⚠️ Gemini API key not found in environment variables (GEMINI_API_KEY).")
else:
    genai.configure(api_key=GEMINI_API_KEY)

# ---------------------------
# Page setup
# ---------------------------
st.set_page_config(page_title="🌞 Solar AI Project", layout="wide")
tabs = st.tabs(["📂 JSON Viewer", "⬆️ Upload JSON", "💬 Chatbot"])

# ---------------------------
# Load company data from JSON files
# ---------------------------
def load_company_data():
    data_folder = "data"
    company_data = {}
    if os.path.exists(data_folder):
        for file in os.listdir(data_folder):
            if file.endswith(".json"):
                file_path = os.path.join(data_folder, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            company_data.update(data)
                except:
                    pass
    return company_data

company_info = load_company_data()

# ---------------------------
# Function to answer from JSON
# ---------------------------
def company_answer(user_input, company_info):
    text = user_input.lower()
    if "موقع" in text or "location" in text:
        return company_info.get("location", "📌 Our location is not available in the current data.")
    elif "خدمات" in text or "services" in text:
        services = company_info.get("services")
        if services:
            return "✅ Our services:\n- " + "\n- ".join(services)
        else:
            return "⚠️ Service details are not available in the current data."
    elif "هوية" in text or "identity" in text:
        return company_info.get("identity", "ℹ️ We are Solar AI, an official company assistant.")
    elif "فريق" in text or "team" in text:
        return company_info.get("team", "👥 Team information is not available.")
    elif "سعر" in text or "price" in text:
        return company_info.get("pricing", "💲 Pricing details are available upon request.")
    else:
        return None

# ---------------------------
# 1. JSON Viewer
# ---------------------------
with tabs[0]:
    st.header("📂 Solar JSON Viewer (data/ folder)")
    data_folder = "data"
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)
    json_files = [f for f in os.listdir(data_folder) if f.endswith(".json")]
    if not json_files:
        st.info("ℹ️ No JSON files found in `data/`.")
    else:
        for file in json_files:
            st.subheader(f"📄 {file}")
            file_path = os.path.join(data_folder, file)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list) and all(isinstance(i, dict) for i in data):
                    st.dataframe(pd.DataFrame(data))
                elif isinstance(data, dict):
                    try:
                        df = pd.DataFrame.from_dict(data, orient="index")
                        st.dataframe(df)
                    except Exception:
                        st.json(data)
                else:
                    st.json(data)
            except Exception as e:
                st.error(f"❌ Error reading {file}: {e}")

# ---------------------------
# 2. Upload JSON
# ---------------------------
with tabs[1]:
    st.header("⬆️ Upload JSON File")
    uploaded_file = st.file_uploader("Choose a JSON file to view its data", type=["json"])
    if uploaded_file is not None:
        try:
            data = json.load(uploaded_file)
            st.success("✅ File uploaded successfully")
            if isinstance(data, list) and all(isinstance(i, dict) for i in data):
                st.dataframe(pd.DataFrame(data))
            elif isinstance(data, dict):
                try:
                    df = pd.DataFrame.from_dict(data, orient="index")
                    st.dataframe(df)
                except Exception:
                    st.json(data)
            else:
                st.json(data)
        except Exception as e:
            st.error(f"❌ Error reading file: {e}")

# ---------------------------
# 3. Chatbot
# ---------------------------
with tabs[2]:
    st.header("💬 Chat with Solar AI Assistant")
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    if st.button("🗑️ Clear Conversation"):
        st.session_state["messages"] = []
        st.experimental_rerun()

    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("✍️ Type your message here / اكتب رسالتك هنا...")

    if user_input:
        st.session_state["messages"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # أولاً: البحث في JSON
        bot_reply = company_answer(user_input, company_info)

        # إذا لم نجد إجابة → استخدام Gemini
        if not bot_reply and GEMINI_API_KEY:
            try:
                model = genai.GenerativeModel("gemini-1.5-flash")
                company_prompt = """
                🤖 [ENGLISH VERSION]
                You are the official AI assistant of Solar AI Company.
                Always reply as "we" or "our company".
                Use JSON company data as the single source of truth.
                If info is missing, politely say it's not available.
                
                🤖 [النسخة العربية]
                أنت المساعد الرسمي لشركة Solar AI.
                أجب دائماً بصيغة الشركة (نحن، شركتنا).
                استخدم بيانات JSON كمصدر أساسي للمعلومات.
                إذا لم تتوفر المعلومة، أجب بلطف: "المعلومة غير متوفرة حالياً ضمن بياناتنا".
                """
                final_prompt = f"{company_prompt}\n\n👤 User Question: {user_input}"
                response = model.generate_content(final_prompt)
                bot_reply = response.text
            except Exception as e:
                bot_reply = f"⚠️ Error connecting to Gemini: {e}"
        elif not bot_reply:
            bot_reply = "⚠️ Information not available in JSON and Gemini API not configured."

        st.session_state["messages"].append({"role": "assistant", "content": bot_reply})
        with st.chat_message("assistant"):
            st.markdown(bot_reply)
