import os
import json
import streamlit as st
import pandas as pd
import google.generativeai as genai

#from google import genai

# ---------------------------
# تهيئة Gemini API
# ---------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    st.error("⚠️ لم يتم العثور على مفتاح Gemini في متغيرات البيئة (GEMINI_API_KEY).")
else:
    client =    genai.configure(api_key=GEMINI_API_KEY) #genai.Client(api_key=GEMINI_API_KEY)

# ---------------------------
# إعداد الصفحة
# ---------------------------
st.set_page_config(page_title="🌞 Solar AI Project", layout="wide")

tabs = st.tabs(["📂 JSON Viewer", "⬆️ Upload JSON", "💬 Chatbot"])

# ---------------------------
# 1. تبويب عرض JSON من مجلد data
# ---------------------------
with tabs[0]:
    st.header("📂 Solar JSON Viewer (مجلد data/)")

    data_folder = "data"
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)

    json_files = [f for f in os.listdir(data_folder) if f.endswith(".json")]

    if not json_files:
        st.info("ℹ️ لم يتم العثور على أي ملفات JSON داخل مجلد `data/`.")
    else:
        for file in json_files:
            st.subheader(f"📄 {file}")
            file_path = os.path.join(data_folder, file)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # إذا كان list of dicts → جدول
                if isinstance(data, list) and all(isinstance(i, dict) for i in data):
                    st.dataframe(pd.DataFrame(data))

                # إذا كان dict يحتوي على dicts أو lists → يحول لجدول
                elif isinstance(data, dict):
                    try:
                        df = pd.DataFrame.from_dict(data, orient="index")
                        st.dataframe(df)
                    except Exception:
                        st.json(data)

                # fallback
                else:
                    st.json(data)

            except Exception as e:
                st.error(f"❌ خطأ في قراءة {file}: {e}")

# ---------------------------
# 2. تبويب رفع JSON
# ---------------------------
with tabs[1]:
    st.header("⬆️ رفع ملف JSON")

    uploaded_file = st.file_uploader("اختر ملف JSON لعرض بياناته", type=["json"])

    if uploaded_file is not None:
        try:
            data = json.load(uploaded_file)
            st.success("✅ تم رفع الملف بنجاح")

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
            st.error(f"❌ خطأ في قراءة الملف: {e}")

# ---------------------------
# 3. تبويب الدردشة
# ---------------------------
with tabs[2]:
    st.header("💬 دردشة مع Gemini حول مشروع Solar")

    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    if st.button("🗑️ مسح المحادثة"):
        st.session_state["messages"] = []
        st.experimental_rerun()

    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("✍️ اكتب رسالتك هنا...")

    if user_input:
        st.session_state["messages"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        if GEMINI_API_KEY:
            try:
                response =  genai.GenerativeModel('gemini-1.5-flash')
 #client.models.generate_content(
                   # model="gemini-1.5-flash",
                   # contents=user_input
                #)
                bot_reply = response.text
            except Exception as e:
                bot_reply = f"⚠️ خطأ أثناء الاتصال بـ Gemini: {e}"
        else:
            bot_reply = "⚠️ لم يتم ضبط مفتاح Gemini."

        st.session_state["messages"].append({"role": "assistant", "content": bot_reply})
        with st.chat_message("assistant"):
            st.markdown(bot_reply)

