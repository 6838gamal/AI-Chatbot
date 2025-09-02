import streamlit as st
import json
import os
import math
import time
from pathlib import Path

# ==========================
# إعداد مسارات الملفات
# ==========================
DATA_DIR = Path("data")
TRAINED_FILE = DATA_DIR / "trained_data.json"

PANELS_FILE = DATA_DIR / "panels.json"
BATTERIES_FILE = DATA_DIR / "batteries.json"
INVERTERS_FILE = DATA_DIR / "inverters.json"

# ==========================
# دعم Gemini (اختياري)
# ==========================
USE_GEMINI = True
try:
    import google.generativeai as genai
except Exception:
    USE_GEMINI = False

# ==========================
# دوال مساعدة
# ==========================
def load_json(file_path, default=None):
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default if default else []

def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_all_data():
    panels = load_json(PANELS_FILE, [])
    batteries = load_json(BATTERIES_FILE, [])
    inverters = load_json(INVERTERS_FILE, [])
    return panels, batteries, inverters

# معالجة البيانات على دفعات مع شريط تقدم
def process_data_in_batches(data, batch_size=50, sleep_time=0.05):
    results = []
    total = len(data)
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i in range(0, total, batch_size):
        batch = data[i:i+batch_size]
        processed = [item for item in batch]  # ضع هنا أي عملية تدريب/تهيئة
        results.extend(processed)

        progress = min(1.0, (i + batch_size) / total)
        progress_bar.progress(progress)
        status_text.text(f"🔄 معالجة البيانات: {i+len(batch)}/{total}")
        time.sleep(sleep_time)

    status_text.text("✅ المعالجة اكتملت!")
    return results

# ==========================
# الواجهة الرئيسية
# ==========================
def main():
    st.set_page_config(page_title="☀️ AI Solar Simulator", layout="wide")
    st.title("☀️ AI Solar Simulator with Smart Chat & Training")

    # تحميل البيانات
    panels, batteries, inverters = load_all_data()
    trained_data = load_json(TRAINED_FILE, [])

    # شريط جانبي Gemini
    with st.sidebar:
        st.header("⚙️ Settings")
        gemini_key = st.text_input("GEMINI_API_KEY (optional)", type="password")
        if gemini_key and USE_GEMINI:
            try:
                genai.configure(api_key=gemini_key)
                model = genai.GenerativeModel("gemini-1.5-flash")
                st.success("Gemini ready")
            except Exception as e:
                st.error(f"Gemini init error: {e}")
                USE_GEMINI = False
        else:
            USE_GEMINI = False
        st.markdown("---")
        st.caption("البيانات تُدار من الإدارة عبر ملفات JSON في مجلد `data/`.")

    # ==========================
    # التبويبات
    # ==========================
    tab_sim, tab_files, tab_chat, tab_train, tab_report = st.tabs(
        ["🧮 Simulation", "📂 Manage Files", "💬 Smart Chat", "⚡ Training", "📥 Export"]
    )

    # ==========================
    # تبويب المحاكاة
    # ==========================
    with tab_sim:
        st.header("Project Inputs")
        col1, col2, col3 = st.columns(3)
        with col1:
            kW_required = st.number_input("Required Power (kW)", min_value=0.1, value=10.0, step=0.1)
        with col2:
            hours_per_day = st.number_input("Usage Duration (hours/day)", min_value=1.0, value=6.0, step=1.0)
        with col3:
            backup_hours = st.number_input("Backup Requirement (hours)", min_value=0.0, value=4.0, step=1.0)

        # اختيار المكونات
        if panels and batteries and inverters:
            panel_opts = [f"{p['brand']} | {p['model']} | {p.get('watt_stc','---')}W" for p in panels]
            inv_opts = [f"{i['brand']} | {i['model']} | {i.get('ac_kw','---')}kW" for i in inverters]
            batt_opts = [f"{b['brand']} | {b['model']} | {b.get('nominal_kwh','---')}kWh" for b in batteries]

            panel_sel = st.selectbox("Panel", panel_opts)
            inv_sel = st.selectbox("Inverter", inv_opts)
            batt_sel = st.selectbox("Battery", batt_opts)

            # جلب العناصر المحددة
            p = panels[panel_opts.index(panel_sel)]
            i = inverters[inv_opts.index(inv_sel)]
            b = batteries[batt_opts.index(batt_sel)]

            if st.button("Compute Simulation"):
                E_daily = kW_required * hours_per_day
                derate_used = float(p.get("derate", 0.85))
                PV_kWdc = E_daily / derate_used if derate_used > 0 else float("inf")
                N_panels = math.ceil((PV_kWdc * 1000) / float(p["watt_stc"]))
                N_inv = math.ceil(kW_required / float(i["ac_kw"]))
                N_batt = math.ceil(backup_hours * kW_required / float(b.get("nominal_kwh", 1)))

                st.metric("Panels (pcs)", N_panels)
                st.metric("Inverters (pcs)", N_inv)
                st.metric("Batteries (pcs)", N_batt)

                st.session_state["last_sim"] = {
                    "panel": p, "inverter": i, "battery": b,
                    "E_daily": E_daily, "PV_kWdc": PV_kWdc,
                    "N_panels": N_panels, "N_inv": N_inv, "N_batt": N_batt
                }
        else:
            st.warning("⚠️ البيانات غير مكتملة لتشغيل المحاكاة.")

    # ==========================
    # تبويب إدارة الملفات
    # ==========================
    with tab_files:
        st.header("Manage Company Data")
        uploaded_file = st.file_uploader("Upload JSON file", type="json")
        if uploaded_file:
            try:
                data = json.load(uploaded_file)
                file_choice = st.selectbox("Select File Type", ["panels", "batteries", "inverters"])
                if st.button("Save File"):
                    if file_choice == "panels":
                        save_json(PANELS_FILE, data)
                    elif file_choice == "batteries":
                        save_json(BATTERIES_FILE, data)
                    elif file_choice == "inverters":
                        save_json(INVERTERS_FILE, data)
                    st.success(f"✅ {file_choice} updated successfully!")
            except Exception as e:
                st.error(f"❌ Invalid file: {e}")

        st.subheader("Preview Data")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.dataframe(panels)
        with col2:
            st.dataframe(batteries)
        with col3:
            st.dataframe(inverters)

    # ==========================
    # تبويب الدردشة الذكية
    # ==========================
    with tab_chat:
        st.header("💬 Smart Chat Assistant")
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        user_input = st.text_input("Your message:")
        if st.button("Send"):
            if user_input:
                st.session_state.chat_history.append({"role": "user", "content": user_input})

                # البحث ضمن البيانات المعالجة
                response = "عذرًا، لا توجد معلومات كافية عن هذا السؤال."
                for item in trained_data:
                    if "model" in item and item["model"].lower() in user_input.lower():
                        response = f"📌 Info on {item['brand']} {item['model']}: {json.dumps(item, ensure_ascii=False)}"
                        break

                # دمج مع AI (Gemini) ضمن السياق فقط
                if USE_GEMINI and gemini_key:
                    try:
                        prompt = f"Use the following context to answer:\n{trained_data}\n\nUser question: {user_input}\nAnswer concisely within context."
                        ai_resp = genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt)
                        response += f"\n🤖 AI Suggestion: {ai_resp.text}"
                    except Exception as e:
                        response += f"\n⚠️ AI Error: {e}"

                st.session_state.chat_history.append({"role": "assistant", "content": response})

        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.write(f"👤 {msg['content']}")
            else:
                st.write(f"🤖 {msg['content']}")

    # ==========================
    # تبويب التدريب
    # ==========================
    with tab_train:
        st.header("⚡ Training / Data Preparation")
        if st.button("Start Training"):
            if panels:
                st.subheader("Processing Panels Data")
                trained_panels = process_data_in_batches(panels)
            if batteries:
                st.subheader("Processing Batteries Data")
                trained_batt = process_data_in_batches(batteries)
            if inverters:
                st.subheader("Processing Inverters Data")
                trained_inv = process_data_in_batches(inverters)

            # حفظ البيانات بعد التدريب
            trained_data_combined = trained_panels + trained_batt + trained_inv
            save_json(TRAINED_FILE, trained_data_combined)
            st.success("✅ Training completed and data saved!")

    # ==========================
    # تبويب التصدير
    # ==========================
    with tab_report:
        st.header("📥 Export Last Simulation")
        if "last_sim" not in st.session_state:
            st.info("قم أولًا بإجراء محاكاة من تبويب Simulation.")
        else:
            sim = st.session_state["last_sim"]
            st.json(sim)

if __name__ == "__main__":
    main()
