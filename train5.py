import streamlit as st
import json
import os
import math
import pandas as pd
import time  # لتقسيم الدفعات
from io import BytesIO

# ========= Gemini setup =========
USE_GEMINI = True
try:
    import google.generativeai as genai
except Exception:
    USE_GEMINI = False

# ========= إعداد الصفحة =========
st.set_page_config(page_title="AI Solar Simulator + Gemini", page_icon="☀️", layout="wide")
st.title("☀️ AI Solar Simulator + JSON Manager + Gemini Chat")

# ========= بيانات الشركة =========
DATA_DIR = "data"
FILES = {
    "panels": os.path.join(DATA_DIR, "panels.json"),
    "inverters": os.path.join(DATA_DIR, "inverters.json"),
    "batteries": os.path.join(DATA_DIR, "batteries.json"),
    "irradiance": os.path.join(DATA_DIR, "irradiance.json")
}

def load_json_safe(path, fallback):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return fallback

# شريط تقدم لتحميل البيانات
progress_text = st.empty()
progress_bar = st.progress(0)
json_data = {}
total_files = len(FILES)
for idx, (name, path) in enumerate(FILES.items(), 1):
    json_data[name] = load_json_safe(path, [])
    progress_text.text(f"Loading {name}...")
    progress_bar.progress(idx/total_files)
progress_text.empty()
progress_bar.empty()

panels = json_data.get("panels", [])
inverters = json_data.get("inverters", [])
batteries = json_data.get("batteries", [])
irr_map = json_data.get("irradiance", {"Default": 5.0})

# ========= Sidebar: Gemini API =========
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

# ========= التبويبات =========
tab_sim, tab_specs, tab_chat = st.tabs(["🧮 Simulation", "📚 Specs Database", "💬 Chat with Gemini"])

# ========= تبويب المحاكاة =========
with tab_sim:
    st.subheader("Project Inputs")

    col1, col2, col3 = st.columns(3)
    with col1:
        kW_required = st.number_input("Required Power (kW)", min_value=0.1, value=10.0, step=0.1)
    with col2:
        hours_per_day = st.number_input("Usage Duration (hours/day)", min_value=1.0, value=6.0, step=1.0)
    with col3:
        backup_hours = st.number_input("Backup Requirement (hours)", min_value=0.0, value=4.0, step=1.0)

    col4, col5, col6 = st.columns(3)
    with col4:
        location = st.selectbox("Location (irradiance map)", options=sorted(list(irr_map.keys())))
        sun_hours = irr_map.get(location, irr_map.get("Default", 5.0))
    with col5:
        redundancy_factor = st.slider("Inverter Redundancy Factor", 1.0, 1.3, 1.1, 0.05)
    with col6:
        system_derate_global = st.slider("System Derate (overall losses)", 0.70, 0.95, 0.85, 0.01)

    st.markdown("### Component Selection")
    # لوائح ماركات
    panel_opts = [f"{p['brand']} | {p['model']} | {p['watt_stc']}W" for p in panels]
    inv_opts = [f"{i['brand']} | {i['model']} | {i['ac_kw']} kW" for i in inverters]
    batt_opts = [f"{b['brand']} | {b['model']} | {b['nominal_kwh']} kWh" for b in batteries]

    if not (panel_opts and inv_opts and batt_opts):
        st.error("⚠️ تأكد من وجود بيانات في ملفات: panels.json / inverters.json / batteries.json")
    else:
        panel_sel = st.selectbox("Panel", panel_opts, index=0)
        inv_sel = st.selectbox("Inverter", inv_opts, index=0)
        batt_sel = st.selectbox("Battery", batt_opts, index=0)

        # جلب سجلات العناصر
        p = panels[panel_opts.index(panel_sel)]
        i = inverters[inv_opts.index(inv_sel)]
        b = batteries[batt_opts.index(batt_sel)]

        # ===== الحسابات =====
        E_daily = kW_required * hours_per_day  # kWh/day
        panel_derate = float(p.get("derate", system_derate_global))
        derate_used = max(0.5, min(panel_derate, 0.98))
        PV_kWdc = E_daily / (sun_hours * derate_used) if sun_hours > 0 else float("inf")
        N_panels = math.ceil((PV_kWdc * 1000) / float(p["watt_stc"]))
        usable_kWh_per_batt = float(b["nominal_kwh"]) * float(b.get("dod", 0.9)) * float(b.get("roundtrip_eff", 0.95))
        E_backup = kW_required * backup_hours
        N_batt = math.ceil(E_backup / usable_kWh_per_batt) if usable_kWh_per_batt > 0 else 0
        N_inv = math.ceil((kW_required * redundancy_factor) / float(i["ac_kw"]))
        cost_panels = N_panels * float(p.get("price_usd", 0))
        cost_inverters = N_inv * float(i.get("price_usd", 0))
        cost_batt = N_batt * float(b.get("price_usd", 0))
        total_cost = cost_panels + cost_inverters + cost_batt

        # ===== عرض النتائج =====
        st.markdown("### Results")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Panels (pcs)", f"{N_panels}")
        c2.metric("Inverters (pcs)", f"{N_inv}")
        c3.metric("Batteries (pcs)", f"{N_batt}")
        c4.metric("PV Array Size (kWdc)", f"{PV_kWdc:.2f}")

        st.markdown("### Cost Estimate")
        st.write(f"Panels: **${cost_panels:,.0f}**  |  Inverters: **${cost_inverters:,.0f}**  |  Batteries: **${cost_batt:,.0f}**")
        st.subheader(f"Estimated Total: **${total_cost:,.0f}**")

        # ===== مساعدة Gemini (اختياري) =====
        if USE_GEMINI and gemini_key:
            with st.expander("🤖 AI Guidance (Gemini)"):
                prompt = f"""
You are a senior solar design assistant. Validate sizing below.
Inputs:
- Required Power: {kW_required} kW
- Usage hours/day: {hours_per_day}
- Location sun-hours: {sun_hours}
- Panel: {p['brand']} {p['model']} {p['watt_stc']}W
- Inverter: {i['brand']} {i['model']} {i['ac_kw']}kW
- Battery: {b['brand']} {b['model']} {b['nominal_kwh']}kWh
- Backup hours: {backup_hours}
- Redundancy factor: {redundancy_factor}

Computed:
- Daily energy: {E_daily:.2f} kWh
- PV kWdc: {PV_kWdc:.2f}
- Panels: {N_panels}
- Inverters: {N_inv}
- Batteries: {N_batt}

Provide concise guidance for 95–100% sizing accuracy.
"""
                try:
                    r = genai.generate_text(model="gemini-1.5-flash", prompt=prompt)
                    st.write(r.text)
                except Exception as e:
                    st.warning(f"Gemini advice error: {e}")

        st.session_state["last_result"] = {
            "Inputs": {"kW_required": kW_required, "hours_per_day": hours_per_day, "backup_hours": backup_hours, "location": location, "sun_hours": sun_hours, "redundancy_factor": redundancy_factor, "system_derate_used": derate_used},
            "Selected": {"panel": p, "inverter": i, "battery": b},
            "Outputs": {"E_daily_kWh": E_daily, "PV_kWdc": PV_kWdc, "N_panels": N_panels, "N_inverters": N_inv, "N_batteries": N_batt, "Cost_panels": cost_panels, "Cost_inverters": cost_inverters, "Cost_batteries": cost_batt, "Cost_total": total_cost}
        }

# ========= تبويب JSON =========
with tab_specs:
    st.subheader("Company Specs")
    for name, data in json_data.items():
        with st.expander(f"📄 {name}"):
            st.dataframe(pd.DataFrame(data))
            query = st.text_input(f"Search in {name}", key=f"search_{name}")
            if query:
                results = [item for item in data if any(query.lower() in str(v).lower() for v in item.values())]
                if results:
                    st.success(f"Found {len(results)} matching items")
                    st.json(results)
                elif USE_GEMINI:
                    with st.spinner("Querying Gemini..."):
                        prompt = f"You are a solar expert. Question: {query}. Answer only if possible using data from {name}"
                        try:
                            r = genai.generate_text(model="gemini-1.5-flash", prompt=prompt)
                            st.info(r.text)
                        except Exception as e:
                            st.error(f"Gemini error: {e}")

# ========= تبويب الدردشة =========
with tab_chat:
    st.subheader("💬 Chat with Gemini")
    user_input = st.text_area("Ask the AI:", height=120)
    if st.button("Send"):
        if not user_input.strip():
            st.warning("Please type a question first")
        else:
            if USE_GEMINI:
                with st.spinner("Processing..."):
                    try:
                        r = genai.generate_text(model="gemini-1.5-flash", prompt=user_input)
                        st.success("Answer:")
                        st.write(r.text)
                    except Exception as e:
                        st.error(f"Gemini error: {e}")
            else:
                st.warning("Gemini not configured or API key missing.")
