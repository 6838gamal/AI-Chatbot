import os
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

# تحميل متغيرات البيئة من ملف .env
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")

# التحقق من المفتاح
if not API_KEY:
    st.error("⚠️ لم يتم العثور على مفتاح API. الرجاء ضبط متغير البيئة OPENAI_API_KEY")
    st.stop()

# تهيئة العميل
client = OpenAI(api_key=API_KEY)

# إعداد واجهة Streamlit
st.set_page_config(page_title="🤖 المساعد الذكي", page_icon="✨", layout="wide")

# الشريط الجانبي
with st.sidebar:
    st.title("⚙️ الإعدادات")
    st.markdown("يمكنك تخصيص المساعد من هنا 👇")
    
    model_choice = st.selectbox("اختر النموذج:", ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"])
    clear_chat = st.button("🗑️ مسح المحادثة")
    
    st.markdown("---")
    st.info("💡 تذكر: هذه النسخة للتجربة والتطوير.")

# حالة الجلسة
if "messages" not in st.session_state or clear_chat:
    st.session_state["messages"] = [
        {"role": "system", "content": "أنت مساعد ذكي تجيب بشكل واقعي واحترافي، بلغة واضحة ومباشرة."}
    ]

# العنوان الرئيسي
st.title("✨ المساعد الذكي")
st.caption("تحدث مع الذكاء الاصطناعي مباشرة. اطرح أي سؤال وستحصل على إجابة مدروسة 👇")

# عرض المحادثات السابقة
for msg in st.session_state["messages"]:
    if msg["role"] == "user":
        with st.chat_message("user", avatar="🧑"):
            st.write(msg["content"])
    elif msg["role"] == "assistant":
        with st.chat_message("assistant", avatar="🤖"):
            st.write(msg["content"])

# إدخال المستخدم
user_input = st.chat_input("💬 اكتب سؤالك هنا...")
if user_input:
    st.session_state["messages"].append({"role": "user", "content": user_input})

    with st.chat_message("user", avatar="🧑"):
        st.write(user_input)

    try:
        response = client.chat.completions.create(
            model=model_choice,
            messages=st.session_state["messages"]
        )
        reply = response.choices[0].message.content
    except Exception as e:
        reply = f"⚠️ خطأ: {str(e)}"

    st.session_state["messages"].append({"role": "assistant", "content": reply})

    with st.chat_message("assistant", avatar="🤖"):
        st.write(reply)
