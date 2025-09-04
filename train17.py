import os
import json
import streamlit as st
import pandas as pd
import google.generativeai as genai

# ---------------------------
# Gemini API setup
# ---------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

st.set_page_config(page_title="🌞 Solar AI Project", layout="wide")

# Initialize language in session state
if "language" not in st.session_state:
    st.session_state.language = "ar"

# Dynamic tabs based on language
if st.session_state.language == "ar":
    tabs = st.tabs(["📂 عارض البيانات", "⬆️ رفع ملف", "💬 المحادثة", "🔆 محاكي الطاقة الشمسية", "⚙️ الإعدادات"])
else:
    tabs = st.tabs(["📂 JSON Viewer", "⬆️ Upload JSON", "💬 Chatbot", "🔆 Solar Simulator", "⚙️ Settings"])

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
company_info = json_data.get("company_full_info", {})
panels_data = json_data.get("panels", [])
inverters_data = json_data.get("inverters", [])
batteries_data = json_data.get("batteries", [])

# ---------------------------
# Helper: company chatbot answers
# ---------------------------
# Helper: detect if text is Arabic or English
def detect_language(text):
    arabic_chars = set("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")
    text_chars = set(text)
    if arabic_chars & text_chars:
        return "ar"
    return "en"

def company_answer(user_input, company_info):
    text = user_input.lower()
    lang = detect_language(user_input)
    
    if "موقع" in text or "location" in text:
        location = company_info.get("location", "")
        if location:
            if lang == "ar":
                return f"🏢 شركة Solar AI تقع في {location}. نحن نخدم العملاء في جميع أنحاء المنطقة ونقدم الاستشارات والحلول المبتكرة في مجال الطاقة الشمسية."
            else:
                return f"🏢 Solar AI Company is located in {location}. We serve clients throughout the region and provide innovative consulting and solutions in solar energy."
        if lang == "ar":
            return "📍 موقع الشركة غير متوفر حاليًا، يرجى التواصل معنا للحصول على معلومات أكثر تفصيلاً."
        else:
            return "📍 Company location is not currently available. Please contact us for more detailed information."
    
    elif "خدمات" in text or "services" in text:
        services = company_info.get("services", [])
        if services:
            if lang == "ar":
                services_text = "، ".join(services)
                return f"🌟 نحن في Solar AI نقدم مجموعة شاملة من الخدمات المتميزة تشمل: {services_text}. فريقنا المتخصص مستعد لمساعدتك في تحقيق أهدافك في مجال الطاقة المتجددة."
            else:
                services_text = ", ".join(services)
                return f"🌟 At Solar AI, we offer a comprehensive range of excellent services including: {services_text}. Our specialized team is ready to help you achieve your renewable energy goals."
        if lang == "ar":
            return "⚡ نحن نقدم خدمات متنوعة في مجال الطاقة الشمسية. يرجى التواصل معنا لمعرفة تفاصيل خدماتنا."
        else:
            return "⚡ We offer various services in solar energy. Please contact us to learn more about our services."
    
    elif "هوية" in text or "identity" in text or "من" in text or "who" in text:
        identity = company_info.get("identity", "")
        vision = company_info.get("vision", "")
        founded = company_info.get("founded", "")
        
        if lang == "ar":
            response = f"👋 {identity if identity else 'مرحبًا! أنا المساعد الذكي لشركة Solar AI'}"
            if founded:
                response += f" تأسست شركتنا عام {founded}"
            if vision:
                response += f" رؤيتنا هي: {vision}"
            response += " نحن هنا لمساعدتك في جميع استفساراتك حول الطاقة الشمسية والذكاء الاصطناعي."
        else:
            response = f"👋 {identity if identity else 'Hello! I am the AI assistant for Solar AI Company'}"
            if founded:
                response += f" Our company was founded in {founded}"
            if vision:
                response += f" Our vision is: {vision}"
            response += " We are here to help you with all your inquiries about solar energy and artificial intelligence."
        return response
    
    elif "فريق" in text or "team" in text:
        team = company_info.get("team", "")
        if team:
            if lang == "ar":
                return f"👥 {team} نحن نؤمن بقوة العمل الجماعي والخبرة المتنوعة لتقديم أفضل الحلول لعملائنا."
            else:
                return f"👥 {team} We believe in the power of teamwork and diverse expertise to deliver the best solutions to our clients."
        if lang == "ar":
            return "🤝 فريقنا يتكون من خبراء متخصصين في الطاقة الشمسية والذكاء الاصطناعي، نعمل معًا لتقديم أفضل الخدمات."
        else:
            return "🤝 Our team consists of experts specialized in solar energy and artificial intelligence, working together to provide the best services."
    
    elif "سعر" in text or "price" in text or "تكلفة" in text or "cost" in text:
        pricing = company_info.get("pricing_policy", "")
        if pricing:
            if lang == "ar":
                return f"💰 {pricing} نحن نقدم عروض أسعار مخصصة تناسب احتياجاتك ومتطلبات مشروعك. فريقنا سيساعدك في الحصول على أفضل الحلول بأنسب الأسعار."
            else:
                return f"💰 {pricing} We provide customized quotes that suit your needs and project requirements. Our team will help you get the best solutions at the most suitable prices."
        if lang == "ar":
            return "💲 نقدم عروض أسعار مخصصة لكل عميل حسب احتياجاته. يرجى التواصل معنا للحصول على عرض سعر مفصل."
        else:
            return "💲 We provide customized quotes for each client based on their needs. Please contact us for a detailed price quote."
    
    elif "رؤية" in text or "vision" in text:
        vision = company_info.get("vision", "")
        if vision:
            if lang == "ar":
                return f"🎯 رؤيتنا: {vision} نعمل بجد لتحقيق هذه الرؤية من خلال الابتكار المستمر والتطوير."
            else:
                return f"🎯 Our vision: {vision} We work hard to achieve this vision through continuous innovation and development."
        if lang == "ar":
            return "🌅 رؤيتنا هي قيادة التحول نحو الطاقة المتجددة باستخدام أحدث التقنيات."
        else:
            return "🌅 Our vision is to lead the transformation towards renewable energy using the latest technologies."
    
    elif "رسالة" in text or "mission" in text:
        mission = company_info.get("mission", "")
        if mission:
            if lang == "ar":
                return f"🚀 رسالتنا: {mission} نلتزم بتقديم أفضل الخدمات والحلول المبتكرة."
            else:
                return f"🚀 Our mission: {mission} We are committed to providing the best services and innovative solutions."
        if lang == "ar":
            return "📋 رسالتنا هي تقديم حلول الطاقة الشمسية المبتكرة والموثوقة لجميع عملائنا."
        else:
            return "📋 Our mission is to provide innovative and reliable solar energy solutions for all our clients."
    
    return None

# ---------------------------
# 1. JSON Viewer Tab
# ---------------------------
with tabs[0]:
    if st.session_state.language == "ar":
        st.header("📂 عارض البيانات")
    else:
        st.header("📂 JSON Viewer")
    for key, data in json_data.items():
        st.subheader(f"📄 {key}.json")
        if isinstance(data, list) and all(isinstance(i, dict) for i in data):
            try:
                st.dataframe(pd.DataFrame(data))
            except:
                st.json(data)
        elif isinstance(data, dict):
            try:
                # Filter out complex nested structures for DataFrame display
                simple_data = {k: v for k, v in data.items() if not isinstance(v, (list, dict))}
                if simple_data:
                    st.dataframe(pd.DataFrame.from_dict(simple_data, orient="index", columns=["Value"]))
                st.json(data)
            except:
                st.json(data)
        else:
            st.json(data)

# ---------------------------
# 2. Upload JSON
# ---------------------------
with tabs[1]:
    if st.session_state.language == "ar":
        st.header("⬆️ رفع ملف")
        uploaded_file = st.file_uploader("اختر ملف JSON", type=["json"])
        if uploaded_file:
            try:
                data = json.load(uploaded_file)
                st.success("✅ تم رفع الملف بنجاح")
                st.json(data)
            except Exception as e:
                st.error(f"❌ خطأ: {e}")
    else:
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
    if st.session_state.language == "ar":
        st.header("💬 المحادثة مع مساعد Solar AI")
    else:
        st.header("💬 Chat with Solar AI Assistant")
    
    # Add custom CSS for better chat styling
    st.markdown("""
    <style>
    /* Main chat container styling */
    .chat-messages {
        max-height: 400px;
        overflow-y: auto;
        padding: 20px;
        border: 2px solid #e8f4fd;
        border-radius: 15px;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        margin: 20px 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    /* User message styling */
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px 20px;
        border-radius: 20px 20px 8px 20px;
        margin: 12px 0;
        margin-left: 25%;
        box-shadow: 0 3px 10px rgba(102, 126, 234, 0.3);
        word-wrap: break-word;
        position: relative;
        animation: slideInRight 0.3s ease-out;
    }
    
    .user-message:before {
        content: '';
        position: absolute;
        bottom: 0;
        right: -8px;
        width: 0;
        height: 0;
        border: 8px solid transparent;
        border-top-color: #764ba2;
        border-right: 0;
        margin-bottom: -8px;
    }
    
    /* Assistant message styling */
    .assistant-message {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        padding: 15px 20px;
        border-radius: 20px 20px 20px 8px;
        margin: 12px 0;
        margin-right: 25%;
        box-shadow: 0 3px 10px rgba(17, 153, 142, 0.3);
        word-wrap: break-word;
        position: relative;
        animation: slideInLeft 0.3s ease-out;
    }
    
    .assistant-message:before {
        content: '';
        position: absolute;
        bottom: 0;
        left: -8px;
        width: 0;
        height: 0;
        border: 8px solid transparent;
        border-top-color: #38ef7d;
        border-left: 0;
        margin-bottom: -8px;
    }
    
    /* Animation keyframes */
    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideInLeft {
        from { transform: translateX(-100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    /* Welcome message styling */
    .welcome-message {
        text-align: center;
        padding: 40px 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 15px;
        margin: 20px 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    /* Clear button styling */
    .stButton > button {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 8px 16px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(238, 90, 36, 0.3);
    }
    
    /* Sticky chat input */
    .stChatFloatingInputContainer {
        position: sticky !important;
        bottom: 0px !important;
        z-index: 999 !important;
        background: white;
        padding: 15px 0;
        border-top: 2px solid #e8f4fd;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
    }
    
    /* Scrollbar styling */
    .chat-messages::-webkit-scrollbar {
        width: 8px;
    }
    
    .chat-messages::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    
    .chat-messages::-webkit-scrollbar-thumb {
        background: #888;
        border-radius: 10px;
    }
    
    .chat-messages::-webkit-scrollbar-thumb:hover {
        background: #555;
    }
    </style>
    """, unsafe_allow_html=True)
    
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    # Clear conversation button with better styling
    col1, col2 = st.columns([1, 6])
    with col1:
        if st.session_state.language == "ar":
            clear_button_text = "🗑️ مسح المحادثة"
        else:
            clear_button_text = "🗑️ Clear Chat"
        
        if st.button(clear_button_text):
            st.session_state["messages"] = []
            st.rerun()
    
    # Chat messages container with custom styling
    if not st.session_state["messages"]:
        if st.session_state.language == "ar":
            welcome_html = """
            <div class="welcome-message">
                <h3>👋 مرحباً بك في Solar AI Assistant</h3>
                <p>🌟 اسأل أي سؤال عن الطاقة الشمسية وحلولنا</p>
                <p>💬 ابدأ المحادثة الآن!</p>
            </div>
            """
        else:
            welcome_html = """
            <div class="welcome-message">
                <h3>👋 Welcome to Solar AI Assistant</h3>
                <p>🌟 Ask any question about solar energy and our solutions</p>
                <p>💬 Start chatting now!</p>
            </div>
            """
        st.markdown(welcome_html, unsafe_allow_html=True)
    else:
        # Create scrollable chat container
        st.markdown('<div class="chat-messages" id="chat-container">', unsafe_allow_html=True)
        
        for i, msg in enumerate(st.session_state["messages"]):
            if msg["role"] == "user":
                # Escape any HTML/CSS/JS content in user messages
                safe_content = msg["content"].replace("<", "&lt;").replace(">", "&gt;")
                user_label = "أنت" if st.session_state.language == "ar" else "You"
                st.markdown(f"""
                <div class="user-message">
                    <strong>👤 {user_label}:</strong><br>
                    {safe_content}
                </div>
                """, unsafe_allow_html=True)
            else:
                # Escape any HTML/CSS/JS content in assistant messages  
                safe_content = msg["content"].replace("<", "&lt;").replace(">", "&gt;")
                st.markdown(f"""
                <div class="assistant-message">
                    <strong>🤖 Solar AI:</strong><br>
                    {safe_content}
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Fixed chat input at the bottom
    if st.session_state.language == "ar":
        input_placeholder = "✍️ اكتب رسالتك هنا..."
    else:
        input_placeholder = "✍️ Type your message here..."
    
    user_input = st.chat_input(input_placeholder)
    if user_input:
        st.session_state["messages"].append({"role": "user", "content": user_input})
        
        # Show loading indicator
        with st.spinner("🤔 جاري التفكير... / Thinking..."):
            # check JSON first
            bot_reply = company_answer(user_input, company_info)
            # fallback to Gemini
            if not bot_reply and GEMINI_API_KEY:
                try:
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    user_lang = detect_language(user_input)
                    
                    if user_lang == "ar":
                        prompt = f"""
                        أنت المساعد الذكي الرسمي لشركة Solar AI. 
                        - أجب بطريقة طبيعية ومحادثة عادية باللغة العربية
                        - كن ودودًا ومفيدًا ولا تستخدم تنسيق JSON في إجاباتك
                        - اجعل إجابتك سردية وطبيعية مثل محادثة حقيقية
                        - استخدم الرموز التعبيرية بشكل مناسب
                        - إذا لم تعرف معلومة معينة، اعتذر بأدب واقترح التواصل مع فريق الشركة
                        
                        معلومات عن الشركة:
                        - اسم الشركة: Solar AI
                        - نتخصص في حلول الطاقة الشمسية والذكاء الاصطناعي
                        - نقدم استشارات ومحاكيات للمشاريع الشمسية
                        """
                    else:
                        prompt = f"""
                        You are the official AI assistant of Solar AI Company.
                        - Answer in a natural and conversational way in English
                        - Be friendly and helpful, do not use JSON format in your responses
                        - Make your answer narrative and natural like a real conversation
                        - Use appropriate emojis
                        - If you don't know specific information, apologize politely and suggest contacting our team
                        
                        Company Information:
                        - Company name: Solar AI
                        - We specialize in solar energy solutions and artificial intelligence
                        - We provide consultations and simulations for solar projects
                        """
                    
                    response = model.generate_content(prompt + "\nUser: " + user_input)
                    bot_reply = response.text
                except Exception as e:
                    bot_reply = f"⚠️ خطأ في الاتصال / Connection error: {e}"
            elif not bot_reply:
                user_lang = detect_language(user_input)
                if user_lang == "ar":
                    bot_reply = "⚠️ المعلومات غير متوفرة في البيانات ولم يتم تكوين الذكاء الاصطناعي."
                else:
                    bot_reply = "⚠️ Information not available in data and AI not configured."

        st.session_state["messages"].append({"role": "assistant", "content": bot_reply})
        
        # Auto-scroll to bottom after new message
        st.rerun()

# ---------------------------
# 4. Solar Simulator Tab
# ---------------------------
with tabs[3]:
    if st.session_state.language == "ar":
        st.header("🔆 محاكي مشاريع الطاقة الشمسية")
        st.subheader("المعاملات المطلوبة")
        req_power = st.number_input("القدرة المطلوبة (كيلو وات)", min_value=1.0, step=1.0, value=10.0)
        usage_hours = st.number_input("مدة تشغيل النظام (ساعة/يوم)", min_value=1.0, step=1.0, value=6.0)
        backup_type = st.selectbox("نوع النسخ الاحتياطي", ["كامل", "جزئي"])
        panel_choices = [p["brand"] + " " + p["model"] for p in panels_data] if panels_data else ["لا توجد ألواح متاحة"]
        inverter_choices = [i["brand"] + " " + i["model"] for i in inverters_data] if inverters_data else ["لا توجد عاكسات متاحة"]
        battery_choices = [b["brand"] + " " + b["model"] for b in batteries_data] if batteries_data else ["لا توجد بطاريات متاحة"]
        
        panel_choice = st.selectbox("اختر نوع/موديل اللوح الشمسي", panel_choices)
        inverter_choice = st.selectbox("اختر نوع/موديل العاكس", inverter_choices)
        battery_choice = st.selectbox("اختر نوع/موديل البطارية", battery_choices)
        calculate_button_text = "🔄 احسب النظام"
    else:
        st.header("🔆 Solar Project Simulator")
        st.subheader("Input Parameters")
        req_power = st.number_input("Required Power (kW)", min_value=1.0, step=1.0, value=10.0)
        usage_hours = st.number_input("System Usage Duration (hours/day)", min_value=1.0, step=1.0, value=6.0)
        backup_type = st.selectbox("Backup Type", ["Full", "Partial"])
        panel_choices = [p["brand"] + " " + p["model"] for p in panels_data] if panels_data else ["No panels available"]
        inverter_choices = [i["brand"] + " " + i["model"] for i in inverters_data] if inverters_data else ["No inverters available"]
        battery_choices = [b["brand"] + " " + b["model"] for b in batteries_data] if batteries_data else ["No batteries available"]
        
        panel_choice = st.selectbox("Select Panel Brand/Model", panel_choices)
        inverter_choice = st.selectbox("Select Inverter Brand/Model", inverter_choices)
        battery_choice = st.selectbox("Select Battery Brand/Model", battery_choices)
        calculate_button_text = "🔄 Calculate System"

    if st.button(calculate_button_text):
        # lookup components
        panel = next((p for p in panels_data if p["brand"] + " " + p["model"] == panel_choice), None)
        inverter = next((i for i in inverters_data if i["brand"] + " " + i["model"] == inverter_choice), None)
        battery = next((b for b in batteries_data if b["brand"] + " " + b["model"] == battery_choice), None)

        if not panel or not inverter or not battery:
            if st.session_state.language == "ar":
                st.error("⚠️ لم يتم العثور على المكون في البيانات")
            else:
                st.error("⚠️ Component not found in JSON")
        else:
            # number of panels - handle different field names
            panel_watt = panel.get("wattage", panel.get("watt_stc", 300))
            panel_kw = panel_watt / 1000 * panel["efficiency"]
            num_panels = max(1, round(req_power / panel_kw))
            # number of inverters
            inverter_capacity = inverter.get("capacity_kw", inverter.get("capacity", 5))
            num_inverters = max(1, round(req_power / inverter_capacity))
            # number of batteries (simplified)
            total_energy = req_power * usage_hours
            battery_capacity = battery.get("capacity_kwh", battery.get("capacity", 10))
            num_batteries = max(1, round(total_energy / battery_capacity))
            # cost - handle different field names
            panel_price = panel.get("price", panel.get("cost", 250))
            inverter_price = inverter.get("price", inverter.get("cost", 1000))
            battery_price = battery.get("price", battery.get("cost", 500))
            total_cost = num_panels*panel_price + num_inverters*inverter_price + num_batteries*battery_price

            if st.session_state.language == "ar":
                st.success("✅ نتائج المحاكاة")
                st.write(f"**عدد الألواح الشمسية:** {num_panels}")
                st.write(f"**عدد العاكسات:** {num_inverters}")
                st.write(f"**عدد البطاريات:** {num_batteries}")
                st.write(f"**التكلفة المقدرة:** ${total_cost}")
                
                # Export to Excel
                df_report = pd.DataFrame({
                    "المكون": ["ألواح شمسية", "عاكسات", "بطاريات"],
                    "الكمية": [num_panels, num_inverters, num_batteries],
                    "سعر الوحدة": [panel_price, inverter_price, battery_price],
                    "السعر الإجمالي": [num_panels*panel_price, num_inverters*inverter_price, num_batteries*battery_price]
                })
                excel_file = "تقرير_محاكاة_الطاقة_الشمسية.xlsx"
                df_report.to_excel(excel_file, index=False)
                st.success(f"📄 تم حفظ التقرير باسم {excel_file}")
                with open(excel_file, "rb") as file:
                    st.download_button("⬇️ تحميل تقرير Excel", data=file.read(), file_name=excel_file)
            else:
                st.success("✅ Simulation Results")
                st.write(f"**Number of Panels:** {num_panels}")
                st.write(f"**Number of Inverters:** {num_inverters}")
                st.write(f"**Number of Batteries:** {num_batteries}")
                st.write(f"**Estimated Cost:** ${total_cost}")

                # Export to Excel
                df_report = pd.DataFrame({
                    "Component": ["Panels", "Inverters", "Batteries"],
                    "Quantity": [num_panels, num_inverters, num_batteries],
                    "Unit Price": [panel_price, inverter_price, battery_price],
                    "Total Price": [num_panels*panel_price, num_inverters*inverter_price, num_batteries*battery_price]
                })
                excel_file = "solar_simulation_report.xlsx"
                df_report.to_excel(excel_file, index=False)
                st.success(f"📄 Report saved as {excel_file}")
                with open(excel_file, "rb") as file:
                    st.download_button("⬇️ Download Excel Report", data=file.read(), file_name=excel_file)

# ---------------------------
# 5. Settings Tab
# ---------------------------
with tabs[4]:
    if st.session_state.language == "ar":
        st.header("⚙️ الإعدادات")
        
        st.subheader("🔑 إعدادات API")
        st.info("💡 للحصول على إجابات ذكية من الذكاء الاصطناعي، أضف مفتاح Gemini API الخاص بك.")
        
        # Check if API key exists
        if GEMINI_API_KEY:
            st.success("✅ تم تكوين مفتاح Gemini API بنجاح")
            st.write("🤖 المحادثة الذكية نشطة ومتاحة")
        else:
            st.warning("⚠️ لم يتم تكوين مفتاح Gemini API")
            st.write("🔧 لإضافة المفتاح، قم بتعيين متغير البيئة GEMINI_API_KEY")
            st.code("export GEMINI_API_KEY='your_api_key_here'", language="bash")
        
        st.subheader("ℹ️ معلومات النظام")
        st.write("📊 **عدد ملفات البيانات المحملة:**", len(json_data))
        if json_data:
            for key in json_data.keys():
                data_count = len(json_data[key]) if isinstance(json_data[key], list) else 1
                st.write(f"  - {key}.json: {data_count} عنصر")
        
        st.subheader("🎨 إعدادات الواجهة")
        
        # Language selector
        st.write("🌐 **اختيار اللغة:**")
        current_lang_index = 0 if st.session_state.language == "ar" else 1
        selected_language = st.selectbox(
            "اختر لغة الواجهة:",
            ["العربية", "English"],
            index=current_lang_index,
            key="settings_language_ar"
        )
        
        # Apply language change button
        if st.button("🔄 تطبيق تغيير اللغة", key="apply_lang_ar"):
            if selected_language == "العربية":
                st.session_state.language = "ar"
            else:
                st.session_state.language = "en"
            st.success("✅ تم تغيير اللغة بنجاح!")
            st.rerun()
        
        st.write("💬 **وضع المحادثة:** ذكي + بيانات الشركة")
        
        st.subheader("📖 دليل الاستخدام")
        st.write("1. **عارض البيانات**: عرض بيانات الألواح والعاكسات والبطاريات")
        st.write("2. **رفع ملف**: رفع ملفات JSON جديدة للنظام")
        st.write("3. **المحادثة**: تحدث مع المساعد الذكي بالعربية أو الإنجليزية")
        st.write("4. **محاكي الطاقة الشمسية**: احسب متطلبات مشروعك الشمسي")
        
    else:
        st.header("⚙️ Settings")
        
        st.subheader("🔑 API Configuration")
        st.info("💡 To get smart AI responses, add your Gemini API key.")
        
        # Check if API key exists
        if GEMINI_API_KEY:
            st.success("✅ Gemini API key configured successfully")
            st.write("🤖 Smart conversation is active and available")
        else:
            st.warning("⚠️ Gemini API key not configured")
            st.write("🔧 To add the key, set the GEMINI_API_KEY environment variable")
            st.code("export GEMINI_API_KEY='your_api_key_here'", language="bash")
        
        st.subheader("ℹ️ System Information")
        st.write("📊 **Loaded data files:**", len(json_data))
        if json_data:
            for key in json_data.keys():
                data_count = len(json_data[key]) if isinstance(json_data[key], list) else 1
                st.write(f"  - {key}.json: {data_count} items")
        
        st.subheader("🎨 Interface Settings")
        
        # Language selector
        st.write("🌐 **Language Selection:**")
        current_lang_index = 0 if st.session_state.language == "ar" else 1
        selected_language = st.selectbox(
            "Choose interface language:",
            ["العربية", "English"],
            index=current_lang_index,
            key="settings_language_en"
        )
        
        # Apply language change button
        if st.button("🔄 Apply Language Change", key="apply_lang_en"):
            if selected_language == "العربية":
                st.session_state.language = "ar"
            else:
                st.session_state.language = "en"
            st.success("✅ Language changed successfully!")
            st.rerun()
        
        st.write("💬 **Chat Mode:** Smart AI + Company Data")
        
        st.subheader("📖 User Guide")
        st.write("1. **JSON Viewer**: View solar panels, inverters, and battery data")
        st.write("2. **Upload JSON**: Upload new JSON files to the system")
        st.write("3. **Chatbot**: Chat with the AI assistant in Arabic or English")
        st.write("4. **Solar Simulator**: Calculate your solar project requirements")
