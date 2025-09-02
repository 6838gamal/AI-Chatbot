import streamlit as st
import pandas as pd
import time
import os
from transformers import pipeline

# ---------------------------
# إعدادات عامة
# ---------------------------
st.set_page_config(page_title="AI Assistant", layout="wide")

DATA_FILE = "trained_data.csv"

# ---------------------------
# تحميل البيانات
# ---------------------------
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=["question", "answer"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# ---------------------------
# نموذج الذكاء الاصطناعي العام (LLM)
# ---------------------------
qa_model = pipeline("text2text-generation", model="google/flan-t5-small")

def ai_answer(prompt):
    response = qa_model(prompt, max_length=200, do_sample=True)
    return response[0]["generated_text"]

# ---------------------------
# التدريب على البيانات
# ---------------------------
def train_on_data(uploaded_file):
    df = load_data()
    new_data = pd.read_csv(uploaded_file)

    progress = st.progress(0)
    status = st.empty()

    for i in range(0, len(new_data), 10):  # تقسيم على دفعات (batch size = 10)
        batch = new_data.iloc[i:i+10]
        df = pd.concat([df, batch], ignore_index=True)
        save_data(df)

        progress.progress(min((i+10)/len(new_data), 1.0))
        status.text(f"📊 معالجة {i+10 if i+10 < len(new_data) else len(new_data)} / {len(new_data)} صفوف ...")
        time.sleep(0.3)

    status.text("✅ اكتمل التدريب على البيانات")
    st.success("تم تدريب البيانات وحفظها بنجاح!")

# ---------------------------
# البحث في البيانات المدربة
# ---------------------------
def search_in_data(user_input, df):
    matches = df[df['question'].str.contains(user_input, case=False, na=False)]
    if not matches.empty:
        return matches.iloc[0]['answer']
    return None

# ---------------------------
# التبويبات
# ---------------------------
tabs = st.tabs(["📂 التدريب على البيانات", "🛠️ إدارة البيانات", "💬 الدردشة"])

# ---------------------------
# التبويب الأول: التدريب
# ---------------------------
with tabs[0]:
    st.header("📂 التدريب على البيانات")
    uploaded_file = st.file_uploader("ارفع ملف CSV يحتوي على (question, answer)", type=["csv"])

    if uploaded_file:
        if st.button("ابدأ التدريب"):
            train_on_data(uploaded_file)

# ---------------------------
# التبويب الثاني: إدارة البيانات
# ---------------------------
with tabs[1]:
    st.header("🛠️ إدارة البيانات")
    df = load_data()
    st.dataframe(df)

    if st.button("🗑️ حذف كل البيانات"):
        save_data(pd.DataFrame(columns=["question", "answer"]))
        st.warning("تم حذف كل البيانات!")

# ---------------------------
# التبويب الثالث: الدردشة
# ---------------------------
with tabs[2]:
    st.header("💬 الدردشة مع المساعد")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_input = st.text_input("📝 اكتب سؤالك هنا...")

    if st.button("إرسال"):
        df = load_data()
        answer = search_in_data(user_input, df)

        if answer:
            final_answer = answer
        else:
            final_answer = ai_answer(user_input)

        st.session_state.chat_history.append(("👤", user_input))
        st.session_state.chat_history.append(("🤖", final_answer))

    # عرض المحادثة
    for sender, msg in st.session_state.chat_history:
        st.write(f"**{sender}:** {msg}")
