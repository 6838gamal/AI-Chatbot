import os
import json
import streamlit as st
import pandas as pd
import google.generativeai as genai

# ====== إعداد Gemini ======
USE_GEMINI = False
if os.getenv("GOOGLE_API_KEY"):
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    USE_GEMINI = True

# ====== تحميل البيانات من JSON ======
def load_json(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading {filename}: {e}")
        return []

panels = load_json("panels.json")
inverters = load_json("inverters.json")
batteries = load_json("batteries.json")

# ====== واجهة التطبيق ======
st.set_page_config(page_title="Solar Project Estimator", layout="wide")
st.title("🔆 Solar Project Estimator & Chat Assistant")

tab_dashboard, tab_json, tab_chat = st.tabs(["📊 Dashboard", "📂 JSON Viewer", "💬 Chat"])

# ====== Tab 1: Dashboard ======
with tab_dashboard:
    st.subheader("📊 System Inputs")

    req_kw = st.number_input("Required Power (kW)", min_value=1, value=10)
    usage_hours = st.number_input("Usage Duration (hours/day)", min_value=1, value=6)

    panel_opts = [f"{p['brand']} | {p['model']} | {p['watt_stc']}W" for p in panels]
    inverter_opts = [f"{i['brand']} | {i['model']} | {i['ac_kw']}kW" for i in inverters]
    battery_opts = [f"{b['brand']} | {b['model']} | {b['nominal_kwh']}kWh" for b in batteries]

    panel_choice = st.selectbox("Select Panel", panel_opts if panel_opts else ["No data"])
    inverter_choice = st.selectbox("Select Inverter", inverter_opts if inverter_opts else ["No data"])
    battery_choice = st.selectbox("Select Battery", battery_opts if battery_opts else ["No data"])

    if st.button("🔍 Simulate System"):
        try:
            panel = next(p for p in panels if f"{p['brand']} | {p['model']} | {p['watt_stc']}W" == panel_choice)
            inverter = next(i for i in inverters if f"{i['brand']} | {i['model']} | {i['ac_kw']}kW" == inverter_choice)
            battery = next(b for b in batteries if f"{b['brand']} | {b['model']} | {b['nominal_kwh']}kWh" == battery_choice)

            num_panels = int((req_kw * 1000) / panel['watt_stc'])
            num_inverters = max(1, int(req_kw / inverter['ac_kw']))
            num_batteries = int((req_kw * usage_hours) / battery['nominal_kwh'])

            result = {
                "Panels": num_panels,
                "Inverters": num_inverters,
                "Batteries": num_batteries,
                "Est. Cost (USD)": num_panels * panel.get("price_usd", 0)
                                   + num_inverters * inverter.get("price_usd", 0)
                                   + num_batteries * battery.get("price_usd", 0)
            }

            st.success("✅ Simulation Completed")
            st.table(pd.DataFrame([result]))

        except Exception as e:
            st.error(f"Simulation error: {e}")

# ====== Tab 2: JSON Viewer ======
with tab_json:
    st.subheader("📂 Raw JSON Data")
    st.write("### Panels")
    st.json(panels)
    st.write("### Inverters")
    st.json(inverters)
    st.write("### Batteries")
    st.json(batteries)

# ====== Tab 3: Chat ======
with tab_chat:
    st.subheader("💬 Ask About Your Solar System")

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    # صندوق إدخال
    user_input = st.text_input("اكتب سؤالك هنا...", key="chat_input")

    if st.button("إرسال"):
        if user_input.strip():
            # إضافة رسالة المستخدم
            st.session_state["chat_history"].append({"role": "user", "text": user_input})

            response_text = "No relevant info in trained data."
            found = False

            # البحث في JSON
            for p in panels:
                if p['brand'].lower() in user_input.lower() or p['model'].lower() in user_input.lower():
                    response_text = f"Panel {p['brand']} {p['model']}: {p['watt_stc']}W, Price: ${p.get('price_usd', 0)}"
                    found = True; break
            if not found:
                for i in inverters:
                    if i['brand'].lower() in user_input.lower() or i['model'].lower() in user_input.lower():
                        response_text = f"Inverter {i['brand']} {i['model']}: {i['ac_kw']}kW, Price: ${i.get('price_usd', 0)}"
                        found = True; break
            if not found:
                for b in batteries:
                    if b['brand'].lower() in user_input.lower() or b['model'].lower() in user_input.lower():
                        response_text = f"Battery {b['brand']} {b['model']}: {b['nominal_kwh']}kWh, Price: ${b.get('price_usd', 0)}"
                        found = True; break

            # لو ما وجد شيء في JSON → يستخدم Gemini
            if not found and USE_GEMINI:
                try:
                    prompt = f"You are a solar system assistant. Answer briefly:\n\nQuestion: {user_input}"
                    r = genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt)
                    response_text = r.text
                except Exception as e:
                    response_text = f"AI error: {e}"

            # إضافة رد المساعد
            st.session_state["chat_history"].append({"role": "assistant", "text": response_text})

            # تفريغ صندوق الكتابة
            st.session_state["chat_input"] = ""

    # عرض المحادثة
    for msg in st.session_state["chat_history"]:
        if msg["role"] == "user":
            st.markdown(f"🧑 **أنت:** {msg['text']}")
        else:
            st.markdown(f"🤖 **المساعد:** {msg['text']}")
