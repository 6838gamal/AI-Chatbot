import streamlit as st
import json
import os

# ---------------------------
# تحميل بيانات من ملفات JSON
# ---------------------------
def load_json(file_path, default_data=None):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default_data if default_data else []

# ---------------------------
# حفظ بيانات JSON
# ---------------------------
def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ---------------------------
# الملفات الخاصة بالإدارة
# ---------------------------
PANELS_FILE = "panels.json"
BATTERIES_FILE = "batteries.json"
INVERTERS_FILE = "inverters.json"

# ---------------------------
# تحميل البيانات
# ---------------------------
panels = load_json(PANELS_FILE, [])
batteries = load_json(BATTERIES_FILE, [])
inverters = load_json(INVERTERS_FILE, [])

# ---------------------------
# واجهة التطبيق
# ---------------------------
st.set_page_config(page_title="نظام إدارة الطاقة", layout="wide")
st.title("⚡ نظام إدارة الطاقة")

# ---------------------------
# التبويبات
# ---------------------------
tabs = st.tabs(["📊 الحسابات", "📂 إدارة الملفات", "💬 الدردشة"])

# 📊 الحسابات
with tabs[0]:
    st.header("حسابات الطاقة")
    
    if panels:
        panel_opts = [f"{p['brand']} | {p['model']} | {p.get('watt_stc','---')}W" for p in panels]
        selected_panel = st.selectbox("اختر اللوح الشمسي:", panel_opts)
    else:
        st.warning("لم يتم رفع بيانات الألواح بعد.")
    
    if batteries:
        batt_opts = [f"{b['brand']} | {b['model']} | {b.get('capacity','---')}Ah" for b in batteries]
        selected_battery = st.selectbox("اختر البطارية:", batt_opts)
    else:
        st.warning("لم يتم رفع بيانات البطاريات بعد.")
    
    if inverters:
        inv_opts = [f"{i['brand']} | {i['model']} | {i.get('power','---')}W" for i in inverters]
        selected_inverter = st.selectbox("اختر الانفرتر:", inv_opts)
    else:
        st.warning("لم يتم رفع بيانات الانفرترات بعد.")

    if st.button("🔍 حساب"):
        st.success("✅ تم تنفيذ الحسابات (هنا تضع المعادلات الخاصة بك).")

# 📂 إدارة الملفات
with tabs[1]:
    st.header("إدارة بيانات الشركة")
    st.write("يمكنك رفع ملفات JSON لتحديث البيانات.")

    uploaded_file = st.file_uploader("ارفع ملف JSON", type="json")
    if uploaded_file:
        try:
            data = json.load(uploaded_file)
            file_choice = st.selectbox("اختر نوع الملف:", ["panels", "batteries", "inverters"])
            if st.button("💾 حفظ الملف"):
                if file_choice == "panels":
                    save_json(PANELS_FILE, data)
                elif file_choice == "batteries":
                    save_json(BATTERIES_FILE, data)
                elif file_choice == "inverters":
                    save_json(INVERTERS_FILE, data)
                st.success(f"✅ تم تحديث بيانات {file_choice}.")
        except Exception as e:
            st.error(f"❌ خطأ في الملف: {e}")

# 💬 الدردشة
with tabs[2]:
    st.header("💬 واجهة الدردشة")
    st.write("هنا سيتم إضافة تكامل مع واتساب / ماسنجر / تليجرام لاحقًا.")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_input = st.text_input("اكتب رسالتك:")
    if st.button("إرسال"):
        if user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            # رد بسيط تجريبي
            st.session_state.chat_history.append({"role": "assistant", "content": f"📩 تم استلام رسالتك: {user_input}"})

    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.write(f"👤 المستخدم: {msg['content']}")
        else:
            st.write(f"🤖 النظام: {msg['content']}")
