import streamlit as st
from transformers import pipeline

# ---------------- تحميل الموديل ----------------
@st.cache_resource
def load_model():
    return pipeline(
        "text2text-generation",
        model="google/flan-t5-small",
        device=-1  # CPU فقط
    )

qa_model = load_model()

# ---------------- إعداد الصفحة ----------------
st.set_page_config(page_title="AI Assistant", page_icon="🤖", layout="wide")

st.title("🤖 مساعد ذكي خفيف")
st.caption("مدعوم بـ FLAN-T5-Small + ONNXRuntime (خيار اقتصادي وخفيف)")

# ---------------- تبويبات ----------------
tab1, tab2, tab3 = st.tabs(["📚 سؤال وجواب", "💬 دردشة", "📝 تلخيص"])

# =================================================
# --- التاب الأول: سؤال وجواب ---
# =================================================
with tab1:
    st.header("❓ اطرح سؤالاً")
    question = st.text_area("✍️ اكتب سؤالك هنا")
    if st.button("إجابة", key="qa"):
        if question.strip():
            result = qa_model(question, max_length=200, do_sample=False)
            st.success(result[0]['generated_text'])
        else:
            st.warning("⚠️ الرجاء كتابة سؤال أولاً.")

# =================================================
# --- التاب الثاني: دردشة ---
# =================================================
with tab2:
    st.header("💬 محادثة تفاعلية")

    # تهيئة ذاكرة المحادثة
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    chat_input = st.text_area("💭 رسالتك", key="chat_input")

    col1, col2 = st.columns([1, 1])
    with col1:
        send = st.button("إرسال", key="chat_send")
    with col2:
        reset = st.button("🔄 إعادة تعيين", key="chat_reset")

    # عند الإرسال
    if send and chat_input.strip():
        response = qa_model(chat_input, max_length=200, do_sample=False)
        answer = response[0]['generated_text']
        st.session_state.chat_history.append(("👤", chat_input))
        st.session_state.chat_history.append(("🤖", answer))
        st.experimental_rerun()

    # عند إعادة التعيين
    if reset:
        st.session_state.chat_history = []
        st.experimental_rerun()

    # عرض المحادثة
    if st.session_state.chat_history:
        st.subheader("📜 سجل المحادثة")
        for role, msg in st.session_state.chat_history:
            if role == "👤":
                st.markdown(f"**{role}**: {msg}")
            else:
                st.markdown(f"{role}: {msg}")

# =================================================
# --- التاب الثالث: تلخيص ---
# =================================================
with tab3:
    st.header("📝 تلخيص نصوص طويلة")
    text_input = st.text_area("📖 ضع النص هنا للتلخيص")
    if st.button("تلخيص", key="summ"):
        if text_input.strip():
            summary = qa_model("summarize: " + text_input, max_length=150, do_sample=False)
            st.success(summary[0]['generated_text'])
        else:
            st.warning("⚠️ ضع نص للتلخيص أولاً.")
