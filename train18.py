import os
import json
import math
import pandas as pd
import streamlit as st
from io import BytesIO
from fpdf import FPDF

# ==========================
# Gemini AI Setup (optional)
# ==========================
USE_GEMINI = False
gemini_key = os.environ.get("GEMINI_API_KEY")
if gemini_key:
    try:
        import google.generativeai as genai
        genai.configure(api_key=gemini_key)
        USE_GEMINI = True
    except:
        USE_GEMINI = False

# ==========================
# Page Config
# ==========================
st.set_page_config(page_title="🌞 Solar AI Simulator", layout="wide")

# ==========================
# Session State Defaults
# ==========================
if "language" not in st.session_state:
    st.session_state.language = "ar"
if "messages" not in st.session_state:
    st.session_state.messages = []

# ==========================
# Load JSON Data
# ==========================
DATA_DIR = "data"
def load_json_safe(path, fallback):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return fallback

panels = load_json_safe(os.path.join(DATA_DIR, "panels.json"), [])
inverters = load_json_safe(os.path.join(DATA_DIR, "inverters.json"), [])
batteries = load_json_safe(os.path.join(DATA_DIR, "batteries.json"), [])
irr_map = load_json_safe(os.path.join(DATA_DIR, "irradiance.json"), {"Default": 5.0})
company_info = load_json_safe(os.path.join(DATA_DIR, "company_full_info.json"), {})

# ==========================
# Tabs
# ==========================
if st.session_state.language == "ar":
    tabs = st.tabs(["🔆 محاكي الطاقة الشمسية", "💬 المحادثة", "⚙️ الإعدادات"])
else:
    tabs = st.tabs(["🔆 Solar Simulator", "💬 Chat", "⚙️ Settings"])

# ==========================
# Helper: Language Detection
# ==========================
def detect_language(text):
    arabic_chars = set("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")
    return "ar" if arabic_chars & set(text) else "en"

# ==========================
# Helper: Company Chatbot
# ==========================
def company_answer(user_input):
    text = user_input.lower()
    lang = detect_language(user_input)
    # Example simple rules, expand as needed
    if "موقع" in text or "location" in text:
        loc = company_info.get("location", "غير متوفر")
        return f"🏢 موقع الشركة: {loc}" if lang=="ar" else f"🏢 Company location: {loc}"
    if "خدمات" in text or "services" in text:
        svcs = ", ".join(company_info.get("services", [])) or "غير متوفر"
        return f"🌟 خدماتنا: {svcs}" if lang=="ar" else f"🌟 Our services: {svcs}"
    return None

# ==========================
# Tab 1: Solar Simulator
# ==========================
with tabs[0]:
    lang = st.session_state.language
    st.header("🔆 Solar Project Simulator" if lang=="en" else "🔆 محاكي مشاريع الطاقة الشمسية")
    
    # --- Inputs ---
    col1, col2, col3 = st.columns(3)
    with col1:
        kW_required = st.number_input("Required Power (kW)" if lang=="en" else "القدرة المطلوبة (كيلو وات)",
                                      min_value=0.1, value=10.0, step=0.1)
    with col2:
        hours_per_day = st.number_input("Usage Duration (hours/day)" if lang=="en" else "مدة التشغيل (ساعة/يوم)",
                                        min_value=1.0, value=6.0, step=1.0)
    with col3:
        backup_hours = st.number_input("Backup Requirement (hours)" if lang=="en" else "ساعات النسخ الاحتياطي",
                                       min_value=0.0, value=4.0, step=1.0)
    
    col4, col5, col6 = st.columns(3)
    with col4:
        location = st.selectbox("Location" if lang=="en" else "الموقع", options=sorted(irr_map.keys()))
        sun_hours = irr_map.get(location, irr_map.get("Default", 5.0))
    with col5:
        redundancy_factor = st.slider("Inverter Redundancy Factor" if lang=="en" else "عامل الاحتياط للعاكس",
                                      1.0, 1.3, 1.1, 0.05)
    with col6:
        system_derate_global = st.slider("System Derate (losses)" if lang=="en" else "خسائر النظام",
                                         0.70, 0.95, 0.85, 0.01)
    
    # --- Component Selection ---
    panel_opts = [f"{p['brand']} | {p['model']} | {p['watt_stc']}W" for p in panels] or ["N/A"]
    inv_opts = [f"{i['brand']} | {i['model']} | {i['ac_kw']}kW" for i in inverters] or ["N/A"]
    batt_opts = [f"{b['brand']} | {b['model']} | {b['nominal_kwh']}kWh" for b in batteries] or ["N/A"]
    
    panel_sel = st.selectbox("Panel" if lang=="en" else "لوحة", panel_opts, index=0)
    inv_sel = st.selectbox("Inverter" if lang=="en" else "عاكس", inv_opts, index=0)
    batt_sel = st.selectbox("Battery" if lang=="en" else "بطارية", batt_opts, index=0)
    
    # --- Calculations ---
    p = panels[panel_opts.index(panel_sel)] if panels else {}
    i = inverters[inv_opts.index(inv_sel)] if inverters else {}
    b = batteries[batt_opts.index(batt_sel)] if batteries else {}
    
    E_daily = kW_required * hours_per_day
    panel_derate = float(p.get("derate", system_derate_global)) if p else system_derate_global
    PV_kWdc = E_daily / (sun_hours * panel_derate) if sun_hours>0 else float("inf")
    N_panels = math.ceil((PV_kWdc*1000)/float(p.get("watt_stc",1))) if p else 0
    usable_kWh_per_batt = float(b.get("nominal_kwh",0))*float(b.get("dod",0.9))*float(b.get("roundtrip_eff",0.95)) if b else 1
    N_batt = math.ceil(kW_required*backup_hours/usable_kWh_per_batt) if usable_kWh_per_batt>0 else 0
    N_inv = math.ceil((kW_required*redundancy_factor)/float(i.get("ac_kw",1))) if i else 0
    
    cost_panels = N_panels*float(p.get("price_usd",0)) if p else 0
    cost_inverters = N_inv*float(i.get("price_usd",0)) if i else 0
    cost_batt = N_batt*float(b.get("price_usd",0)) if b else 0
    total_cost = cost_panels + cost_inverters + cost_batt
    
    # --- Display Results ---
    st.subheader("Results" if lang=="en" else "النتائج")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Panels" if lang=="en" else "عدد الألواح", f"{N_panels}")
    c2.metric("Inverters" if lang=="en" else "عدد العاكسات", f"{N_inv}")
    c3.metric("Batteries" if lang=="en" else "عدد البطاريات", f"{N_batt}")
    c4.metric("PV Size (kWdc)" if lang=="en" else "حجم الألواح (kWdc)", f"{PV_kWdc:.2f}")
    
    st.markdown("### Cost Estimate" if lang=="en" else "تقدير التكلفة")
    st.write(f"Panels: ${cost_panels:.0f} | Inverters: ${cost_inverters:.0f} | Batteries: ${cost_batt:.0f}")
    st.subheader(f"Total: ${total_cost:.0f}")
    
    # --- Export Report ---
    if st.button("⬇️ Download Excel / PDF" if lang=="en" else "⬇️ تحميل التقرير Excel / PDF"):
        rows = [("Parameter","Value"),("Required Power (kW)",kW_required),("Usage Hours",hours_per_day),
                ("Backup Hours",backup_hours),("Location",location),
                ("Panels",N_panels),("Inverters",N_inv),("Batteries",N_batt),
                ("PV Size (kWdc)",PV_kWdc),("Total Cost USD",total_cost)]
        df = pd.DataFrame(rows[1:], columns=["Item","Value"])
        # Excel
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
        st.download_button("⬇️ Excel", buffer.getvalue(), "solar_report.xlsx")
        # PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0,10,"Solar Simulation Report",ln=True,align="C")
        pdf.set_font("Arial","",12)
        for item,value in rows[1:]:
            pdf.cell(0,8,f"{item}: {value}",ln=True)
        pdf_output = BytesIO()
        pdf.output(pdf_output)
        st.download_button("⬇️ PDF", pdf_output.getvalue(), "solar_report.pdf")

# ==========================
# Tab 2: Chat
# ==========================
with tabs[1]:
    st.header("💬 Chat with Solar AI Assistant" if st.session_state.language=="en" else "💬 المحادثة مع مساعد Solar AI")
    col1, col2 = st.columns([1,6])
    with col1:
        if st.button("🗑️ Clear Chat" if lang=="en" else "🗑️ مسح المحادثة"):
            st.session_state.messages=[]
            st.rerun()
    
    if not st.session_state.messages:
        st.info("Start chatting with the assistant..." if lang=="en" else "ابدأ المحادثة مع المساعد...")
    else:
        for msg in st.session_state.messages:
            role = "You" if msg["role"]=="user" else "Solar AI"
            st.markdown(f"**{role}:** {msg['content']}")
    
    user_input = st.chat_input("Type your message..." if lang=="en" else "✍️ اكتب رسالتك هنا...")
    if user_input:
        st.session_state.messages.append({"role":"user","content":user_input})
        reply = company_answer(user_input)
        if not reply and USE_GEMINI:
            try:
                model = genai.GenerativeModel("gemini-1.5-flash")
                prompt = f"You are Solar AI assistant. Answer naturally: {user_input}"
                resp = model.generate_content(prompt)
                reply = resp.text
            except:
                reply = "⚠️ AI unavailable"
        elif not reply:
            reply = "⚠️ No information available"
        st.session_state.messages.append({"role":"assistant","content":reply})
        st.rerun()

# ==========================
# Tab 3: Settings
# ==========================
with tabs[2]:
    st.header("⚙️ Settings" if lang=="en" else "⚙️ الإعدادات")
    new_lang = st.radio("Language" if lang=="en" else "اختر اللغة", options=["English","Arabic"],
                        index=0 if st.session_state.language=="en" else 1)
    st.session_state.language = "en" if new_lang=="English" else "ar"
    st.success("✅ Language updated" if lang=="en" else "✅ تم تحديث اللغة")
