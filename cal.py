import os
import json
import math
import pandas as pd
import streamlit as st

# (اختياري) Gemini
USE_GEMINI = True
try:
    import google.generativeai as genai
except Exception:
    USE_GEMINI = False

# ========= إعداد الصفحة =========
st.set_page_config(page_title="AI Solar Simulator", page_icon="☀️", layout="wide")
st.title("☀️ AI-powered Solar Project Estimator & Simulator")

# ========= تحميل البيانات من /data =========
DATA_DIR = "data"
FILES = {
    "panels": os.path.join(DATA_DIR, "panels.json"),
    "inverters": os.path.join(DATA_DIR, "inverters.json"),
    "batteries": os.path.join(DATA_DIR, "batteries.json"),
    "irradiance": os.path.join(DATA_DIR, "irradiance.json"),
}

def load_json_safe(path, fallback):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return fallback

panels = load_json_safe(FILES["panels"], [])
inverters = load_json_safe(FILES["inverters"], [])
batteries = load_json_safe(FILES["batteries"], [])
irr_map = load_json_safe(FILES["irradiance"], {"Default": 5.0})

# ========= الشريط الجانبي: إعدادات عامة =========
with st.sidebar:
    st.header("⚙️ Settings")
    # مفتاح Gemini (اختياري)
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
tab_sim, tab_specs, tab_report = st.tabs(["🧮 Simulation", "📚 Specs Database", "📥 Export Report"])

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
    inv_opts   = [f"{i['brand']} | {i['model']} | {i['ac_kw']} kW" for i in inverters]
    batt_opts  = [f"{b['brand']} | {b['model']} | {b['nominal_kwh']} kWh" for b in batteries]

    if not (panel_opts and inv_opts and batt_opts):
        st.error("⚠️ تأكد من وجود بيانات في ملفات: panels.json / inverters.json / batteries.json")
    else:
        panel_sel = st.selectbox("Panel", panel_opts, index=0)
        inv_sel   = st.selectbox("Inverter", inv_opts, index=0)
        batt_sel  = st.selectbox("Battery", batt_opts, index=0)

        # جلب سجلات العناصر
        p = panels[panel_opts.index(panel_sel)]
        i = inverters[inv_opts.index(inv_sel)]
        b = batteries[batt_opts.index(batt_sel)]

        # ===== الحسابات =====
        E_daily = kW_required * hours_per_day  # kWh/day
        # نستخدم derate كأولوية من اللوح (إن وُجد)، وإلا من شريط الإعداد العام
        panel_derate = float(p.get("derate", system_derate_global))
        derate_used = max(0.5, min(panel_derate, 0.98))  # ضبط آمن
        PV_kWdc = E_daily / (sun_hours * derate_used) if sun_hours > 0 else float("inf")

        N_panels = math.ceil((PV_kWdc * 1000) / float(p["watt_stc"]))

        usable_kWh_per_batt = float(b["nominal_kwh"]) * float(b.get("dod", 0.9)) * float(b.get("roundtrip_eff", 0.95))
        E_backup = kW_required * backup_hours  # kWh
        N_batt = math.ceil(E_backup / usable_kWh_per_batt) if usable_kWh_per_batt > 0 else 0

        N_inv = math.ceil((kW_required * redundancy_factor) / float(i["ac_kw"]))

        # التكاليف (اختياري)
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

        st.markdown("### Cost Estimate (Optional)")
        st.write(f"Panels: **${cost_panels:,.0f}**  |  Inverters: **${cost_inverters:,.0f}**  |  Batteries: **${cost_batt:,.0f}**")
        st.subheader(f"Estimated Total: **${total_cost:,.0f}**")

        st.markdown("### Notes / Assumptions")
        st.caption(f"- E_daily = {kW_required} kW × {hours_per_day} h = {E_daily:.1f} kWh/day")
        st.caption(f"- sun_hours ({location}) = {sun_hours} h/day  |  derate used = {derate_used:.2f}")
        st.caption(f"- Battery usable = nominal({b['nominal_kwh']} kWh) × DoD({b.get('dod',0.9):.2f}) × eff({b.get('roundtrip_eff',0.95):.2f}) = {usable_kWh_per_batt:.2f} kWh")

        # ===== مساعدة Gemini (اختياري) =====
        if USE_GEMINI and gemini_key:
            with st.expander("🤖 AI Guidance (Gemini)"):
                prompt = f"""
You are a senior solar design assistant. Validate and advise on sizing below.
Inputs:
- Required Power (kW): {kW_required}
- Usage hours/day: {hours_per_day}
- Location sun-hours: {sun_hours}
- Panel: {p['brand']} {p['model']} {p['watt_stc']}W (derate {derate_used})
- Inverter: {i['brand']} {i['model']} {i['ac_kw']}kW
- Battery: {b['brand']} {b['model']} {b['nominal_kwh']}kWh (usable ~ {usable_kWh_per_batt:.2f}kWh)
- Backup hours: {backup_hours}
- Redundancy factor: {redundancy_factor}

Computed:
- Daily energy: {E_daily:.2f} kWh
- PV kWdc: {PV_kWdc:.2f}
- Panels: {N_panels}
- Inverters: {N_inv}
- Batteries: {N_batt}

Give concise guidance: sanity-checks, edge cases, and suggestions to reach 95–100% accuracy using deterministic rules.
"""
                try:
                    r = genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt)
                    st.write(r.text)
                except Exception as e:
                    st.warning(f"Gemini advice error: {e}")

        # حفظ النتائج مؤقتًا لاستخدام التصدير
        st.session_state["last_result"] = {
            "Inputs": {
                "kW_required": kW_required,
                "hours_per_day": hours_per_day,
                "backup_hours": backup_hours,
                "location": location,
                "sun_hours": sun_hours,
                "redundancy_factor": redundancy_factor,
                "system_derate_used": derate_used
            },
            "Selected": {
                "panel": p,
                "inverter": i,
                "battery": b
            },
            "Outputs": {
                "E_daily_kWh": E_daily,
                "PV_kWdc": PV_kWdc,
                "N_panels": N_panels,
                "N_inverters": N_inv,
                "N_batteries": N_batt,
                "Cost_panels": cost_panels,
                "Cost_inverters": cost_inverters,
                "Cost_batteries": cost_batt,
                "Cost_total": total_cost
            }
        }

# ========= تبويب قاعدة المواصفات (قراءة فقط من ملفات الإدارة) =========
with tab_specs:
    st.subheader("Company Specs (read-only from /data)")
    colA, colB, colC = st.columns(3)
    with colA:
        st.markdown("#### Panels")
        if panels:
            st.dataframe(pd.DataFrame(panels))
        else:
            st.info("No panels found.")
    with colB:
        st.markdown("#### Inverters")
        if inverters:
            st.dataframe(pd.DataFrame(inverters))
        else:
            st.info("No inverters found.")
    with colC:
        st.markdown("#### Batteries")
        if batteries:
            st.dataframe(pd.DataFrame(batteries))
        else:
            st.info("No batteries found.")

    st.markdown("#### Irradiance Map")
    st.dataframe(pd.DataFrame(
        [{"location": k, "sun_hours": v} for k, v in irr_map.items()]
    ))

# ========= تبويب التصدير =========
with tab_report:
    st.subheader("Export Simulation Report")
    if "last_result" not in st.session_state:
        st.info("قم أولًا بإجراء محاكاة من تبويب Simulation.")
    else:
        res = st.session_state["last_result"]
        # جدول مُلخص للتصدير
        rows = [
            ("Required Power (kW)", res["Inputs"]["kW_required"]),
            ("Usage hours/day", res["Inputs"]["hours_per_day"]),
            ("Backup hours", res["Inputs"]["backup_hours"]),
            ("Location", res["Inputs"]["location"]),
            ("Sun hours", res["Inputs"]["sun_hours"]),
            ("System derate used", res["Inputs"]["system_derate_used"]),
            ("Panel model", f"{res['Selected']['panel']['brand']} {res['Selected']['panel']['model']}"),
            ("Inverter model", f"{res['Selected']['inverter']['brand']} {res['Selected']['inverter']['model']}"),
            ("Battery model", f"{res['Selected']['battery']['brand']} {res['Selected']['battery']['model']}"),
            ("Daily energy (kWh)", f"{res['Outputs']['E_daily_kWh']:.2f}"),
            ("PV Array (kWdc)", f"{res['Outputs']['PV_kWdc']:.2f}"),
            ("Panels (pcs)", res["Outputs"]["N_panels"]),
            ("Inverters (pcs)", res["Outputs"]["N_inverters"]),
            ("Batteries (pcs)", res["Outputs"]["N_batteries"]),
            ("Cost panels (USD)", f"{res['Outputs']['Cost_panels']:.0f}"),
            ("Cost inverters (USD)", f"{res['Outputs']['Cost_inverters']:.0f}"),
            ("Cost batteries (USD)", f"{res['Outputs']['Cost_batteries']:.0f}"),
            ("Total cost (USD)", f"{res['Outputs']['Cost_total']:.0f}")
        ]
        df = pd.DataFrame(rows, columns=["Item", "Value"])

        # تنزيل Excel
        from io import BytesIO
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Solar Estimation")
        st.download_button(
            label="⬇️ Download Excel Report",
            data=buffer.getvalue(),
            file_name="solar_estimation_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # تنزيل CSV
        st.download_button(
            label="⬇️ Download CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="solar_estimation_report.csv",
            mime="text/csv"
        )
