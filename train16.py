import os
import json
import streamlit as st
import pandas as pd
from google import genai

# ---------------------------
# Gemini API setup
# ---------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

st.set_page_config(page_title="🌞 Solar AI Project", layout="wide")
tabs = st.tabs(["📂 JSON Viewer", "⬆️ Upload JSON", "💬 Chatbot", "🔆 Solar Simulator"])

# ---------------------------
# Load JSON data
# ---------------------------
def load_json_files(folder):
    data = {}
    if os.path.exists(folder):
        for f in os.listdir(folder):
            if f.endswith(".json"):
                path = os.path.join(folder, f)
                try:
                    with open(path, "r", encoding="utf-8") as file:
                        content = json.load(file)
                        data[f.split(".json")[0]] = content
                except:
                    pass
    return data

json_data = load_json_files("data")
company_info = json_data.get("company_info", [])
panels_data = json_data.get("panels", [])
inverters_data = json_data.get("inverters", [])
batteries_data = json_data.get("batteries", [])

# ---------------------------
# Helper: company chatbot answers
# ---------------------------
def company_answer(user_input, company_info):
    text = user_input.lower()
    if "موقع" in text or "location" in text:
        return company_info.get("location", "📌 Location not available.")
    elif "خدمات" in text or "services" in text:
        services = company_info.get("services")
        if services:
            return "✅ Our services:\n- " + "\n- ".join(services)
    elif "هوية" in text or "identity" in text:
        return company_info.get("identity", "ℹ️ We are Solar AI, official company assistant.")
    elif "فريق" in text or "team" in text:
        return company_info.get("team", "👥 Team info not available.")
    elif "سعر" in text or "price" in text:
        return company_info.get("pricing", "💲 Pricing available upon request.")
    return None

# ---------------------------
# 1. JSON Viewer Tab
# ---------------------------
with tabs[0]:
    st.header("📂 JSON Viewer")
    for key, data in json_data.items():
        st.subheader(f"📄 {key}.json")
        if isinstance(data, list) and all(isinstance(i, dict) for i in data):
            st.dataframe(pd.DataFrame(data))
        elif isinstance(data, dict):
            st.dataframe(pd.DataFrame.from_dict(data, orient="index"))
        else:
            st.json(data)

# ---------------------------
# 2. Upload JSON
# ---------------------------
with tabs[1]:
    st.header("⬆️ Upload JSON")
    uploaded_file = st.file_uploader("Choose JSON", type=["json"])
    if uploaded_file:
        try:
            data = json.load(uploaded_file)
            st.success("✅ File uploaded")
            st.json(data)
        except Exception as e:
            st.error(f"❌ Error: {e}")

# ---------------------------
# 3. Chatbot
# ---------------------------
with tabs[2]:
    st.header("💬 Chat with Solar AI Assistant")
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    if st.button("🗑️ Clear Conversation"):
        st.session_state["messages"] = []
        st.experimental_rerun()

    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("✍️ Type message / اكتب رسالتك هنا...")
    if user_input:
        st.session_state["messages"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # check JSON first
        bot_reply = company_answer(user_input, company_info)
        # fallback to Gemini
        if not bot_reply and GEMINI_API_KEY:
            try:
                model = genai.GenerativeModel("gemini-1.5-flash")
                prompt = f"""
                You are the official AI assistant of Solar AI.
                Answer professionally using JSON company data.
                """
                response = model.generate_content(prompt + "\nUser: " + user_input)
                bot_reply = response.text
            except Exception as e:
                bot_reply = f"⚠️ Gemini error: {e}"
        elif not bot_reply:
            bot_reply = "⚠️ Info not available in JSON and Gemini not configured."

        st.session_state["messages"].append({"role": "assistant", "content": bot_reply})
        with st.chat_message("assistant"):
            st.markdown(bot_reply)

# ---------------------------
# 4. Solar Simulator Tab
# ---------------------------
with tabs[3]:
    st.header("🔆 Solar Project Simulator")

    st.subheader("Input Parameters")
    req_power = st.number_input("Required Power (kW)", min_value=1.0, step=1.0, value=10.0)
    usage_hours = st.number_input("System Usage Duration (hours/day)", min_value=1.0, step=1.0, value=6.0)
    backup_type = st.selectbox("Backup Type", ["Full", "Partial"])
    panel_choice = st.selectbox("Select Panel Brand/Model", [p["brand"] + " " + p["model"] for p in panels_data])
    inverter_choice = st.selectbox("Select Inverter Brand/Model", [i["brand"] + " " + i["model"] for i in inverters_data])
    battery_choice = st.selectbox("Select Battery Brand/Model", [b["brand"] + " " + b["model"] for b in batteries_data])

    if st.button("🔄 Calculate System"):
        # lookup components
        panel = next((p for p in panels_data if p["brand"] + " " + p["model"] == panel_choice), None)
        inverter = next((i for i in inverters_data if i["brand"] + " " + i["model"] == inverter_choice), None)
        battery = next((b for b in batteries_data if b["brand"] + " " + b["model"] == battery_choice), None)

        if not panel or not inverter or not battery:
            st.error("⚠️ Component not found in JSON")
        else:
            # number of panels
            panel_kw = panel["wattage"] / 1000 * panel["efficiency"]
            num_panels = round(req_power / panel_kw)
            # number of inverters
            num_inverters = round(req_power / inverter["capacity_kw"])
            # number of batteries (simplified)
            total_energy = req_power * usage_hours
            num_batteries = round(total_energy / battery["capacity_kwh"])
            # cost
            total_cost = num_panels*panel["price"] + num_inverters*inverter["price"] + num_batteries*battery["price"]

            st.success("✅ Simulation Results")
            st.write(f"**Number of Panels:** {num_panels}")
            st.write(f"**Number of Inverters:** {num_inverters}")
            st.write(f"**Number of Batteries:** {num_batteries}")
            st.write(f"**Estimated Cost:** ${total_cost}")

            # Export to Excel
            df_report = pd.DataFrame({
                "Component": ["Panels", "Inverters", "Batteries"],
                "Quantity": [num_panels, num_inverters, num_batteries],
                "Unit Price": [panel["price"], inverter["price"], battery["price"]],
                "Total Price": [num_panels*panel["price"], num_inverters*inverter["price"], num_batteries*battery["price"]]
            })
            excel_file = "solar_simulation_report.xlsx"
            df_report.to_excel(excel_file, index=False)
            st.success(f"📄 Report saved as {excel_file}")
            st.download_button("⬇️ Download Excel Report", data=open(excel_file, "rb"), file_name=excel_file)
