import json
import requests
import streamlit as st
from datetime import datetime

# -------------------- إعداد البيانات --------------------
DATA_FILE = "company_data.json"
CHAT_LOG_FILE = "chat_log.json"

# تحميل بيانات الشركة
def load_company_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        # بيانات افتراضية إذا الملف غير موجود
        return {
            "services": {"ar": "خدمات الشركة", "en": "Company services"},
            "address": {"ar": "عنوان الشركة", "en": "Company address"},
            "phone": {"ar": "+967-777-000-000", "en": "+967-777-000-000"},
            "email": {"ar": "info@solarcompany.com", "en": "info@solarcompany.com"},
            "working_hours": {"ar": "من 8 صباحًا حتى 6 مساءً", "en": "From 8 AM to 6 PM"}
        }

# حفظ بيانات الشركة
def save_company_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# تحميل سجل الدردشة
def load_chat_log():
    try:
        with open(CHAT_LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

# حفظ سجل الدردشة
def save_chat_log(chat_log):
    with open(CHAT_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(chat_log, f, ensure_ascii=False, indent=4)

# -------------------- استدعاء DeepSeek --------------------
DEEPSEEK_API_KEY = "sk-e6dc4a3d127445c4b5dcf4a2c97127d3"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

def ask_deepseek(prompt, context=""):
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": f"أنت مساعد ذكي لشركة طاقة شمسية. سياق الشركة: {context}"},
            {"role": "user", "content": prompt}
        ]
    }
    response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data)
    result = response.json()
    return result["choices"][0]["message"]["content"]

# -------------------- واجهة Streamlit --------------------
def main():
    st.set_page_config(page_title="Solar AI Assistant", page_icon="☀️", layout="wide")
    st.title("☀️ Solar Company AI Assistant")

    company_data = load_company_data()
    chat_log = load_chat_log()

    language = st.radio("اختر اللغة / Choose language", ("العربية", "English"), horizontal=True)

    tab1, tab2, tab3 = st.tabs(["💬 المحادثة", "📋 بيانات الشركة", "📝 سجل المحادثات"])

    # ----------- تبويب الدردشة -----------
    with tab1:
        st.subheader("تحدث مع المساعد الذكي" if language=="العربية" else "Talk to the AI Assistant")
        user_input = st.text_input("اكتب رسالتك هنا" if language=="العربية" else "Type your message here")
        if st.button("إرسال" if language=="العربية" else "Send"):
            context = {k: v["ar"] if language=="العربية" else v["en"] for k,v in company_data.items()}
            if not DEEPSEEK_API_KEY or DEEPSEEK_API_KEY.startswith("ضع"):
                st.error("⚠️ الرجاء إدخال مفتاح DeepSeek API في الكود")
            else:
                answer = ask_deepseek(user_input, str(context))
                st.success(f"🤖 المساعد: {answer}")

                # حفظ المحادثة
                chat_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "language": language,
                    "user": user_input,
                    "assistant": answer
                })
                save_chat_log(chat_log)

    # ----------- تبويب إدارة البيانات -----------
    with tab2:
        st.subheader("إدارة بيانات الشركة" if language=="العربية" else "Manage Company Data")
        for key, value in company_data.items():
            ar_val = st.text_input(f"{key} (العربية)", value["ar"])
            en_val = st.text_input(f"{key} (English)", value["en"])
            company_data[key]["ar"] = ar_val
            company_data[key]["en"] = en_val
        if st.button("حفظ البيانات" if language=="العربية" else "Save Data"):
            save_company_data(company_data)
            st.success("✅ تم حفظ البيانات بنجاح" if language=="العربية" else "Data saved successfully")

    # ----------- تبويب سجل المحادثات -----------
    with tab3:
        st.subheader("سجل المحادثات" if language=="العربية" else "Chat Log")
        for entry in reversed(chat_log[-20:]):  # عرض آخر 20 محادثة
            st.write(f"**{entry['timestamp']}**")
            st.write(f"👤 {entry['user']}")
            st.write(f"🤖 {entry['assistant']}")
            st.write("---")

if __name__ == "__main__":
    main()
