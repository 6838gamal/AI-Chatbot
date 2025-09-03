import os
import json
import streamlit as st
from google import genai

# ---------------------------
# تهيئة Gemini API
# ---------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    st.error("⚠️ لم يتم العثور على مفتاح Gemini في متغيرات البيئة (GEMINI_API_KEY).")
else:
    client = genai.Client(api_key=GEMINI_API_KEY)

# ---------------------------
# إعداد الصفحة
# ---------------------------
st.set_page_config(page_title="🌞 Solar AI Project", layout="wide")

tabs = st.tabs(["📂 JSON Viewer", "⬆️ Upload JSON", "💬 Chatbot"])

# ---------------------------
# 1. تبويب عرض JSON
# ---------------------------
with tabs[0]:
    st.header("📂 Solar JSON Viewer")

    sample_json = {
        "project": "Solar",
        "description": "AI-powered solar management platform",
        "panels": [
            {"id": 1, "location": "Roof A", "capacity_kw": 5.2, "status": "Active"},
            {"id": 2, "location": "Roof B", "capacity_kw": 3.8, "status": "Maintenance"}
        ],
        "analytics": {
            "total_capacity": 9.0,
            "efficiency": "92%",
            "savings_usd": 1340
        }
    }
    st.json(sample_json)

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
            st.json(data)
        except Exception as e:
            st.error(f"❌ خطأ في قراءة الملف: {e}")

# ---------------------------
# 3. تبويب الدردشة
# ---------------------------
with tabs[2]:
    st.header("💬 دردشة مع Gemini حول مشروع Solar")

    # تهيئة سجل المحادثة
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    # زر لمسح المحادثة
    if st.button("🗑️ مسح المحادثة"):
        st.session_state["messages"] = []
        st.experimental_rerun()

    # عرض الرسائل السابقة
    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # صندوق إدخال المستخدم
    user_input = st.chat_input("✍️ اكتب رسالتك هنا...")

    if user_input:
        # أضف رسالة المستخدم
        st.session_state["messages"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # رد Gemini
        if GEMINI_API_KEY:
            try:
                response = client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=user_input
                )
                bot_reply = response.text
            except Exception as e:
                bot_reply = f"⚠️ خطأ أثناء الاتصال بـ Gemini: {e}"
        else:
            bot_reply = "⚠️ لم يتم ضبط مفتاح Gemini."

        # عرض وإضافة الرد
        st.session_state["messages"].append({"role": "assistant", "content": bot_reply})
        with st.chat_message("assistant"):
            st.markdown(bot_reply)
