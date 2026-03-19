import streamlit as st
import pandas as pd
import numpy as np
import joblib
from datetime import datetime
import google.generativeai as genai
from twilio.rest import Client
import math
import plotly.express as px 

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(
    page_title="Solrrbox",
    layout="wide"
)

# ===============================
# SIDEBAR STYLING
# ===============================
st.markdown(f"""
<style>
/* Sidebar fully blue */
[data-testid="stSidebar"] {{
    background-color: #38b6ff;
    color: white;
}}

/* Sidebar text color */
[data-testid="stSidebar"] .css-1d391kg, 
[data-testid="stSidebar"] .css-15zrgzn {{
    color: white;
}}

/* Sidebar buttons hover */
[data-testid="stSidebar"] button:hover {{
    background-color: #2aa0e0;
}}
</style>
""", unsafe_allow_html=True)
# ===============================
# TWILIO CONFIG
# ===============================
TWILIO_ACCOUNT_SID = "AC8967b03e5b544bf22113c464e9f6bc7e"
TWILIO_AUTH_TOKEN = "11f82aec1dc4b85bf193bfdeaac4d910"
TWILIO_SMS_NUMBER = "+15706846559"
TWILIO_WHATSAPP_NUMBER = "+14155238886"
TWILIO_CALL_NUMBER = "+15706846559"

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def send_sms_alert(message):
    try:
        twilio_client.messages.create(
            body=message,
            from_=TWILIO_SMS_NUMBER,
            to="+919791805322"
        )
    except:
        pass

def send_whatsapp_alert(message):
    try:
        twilio_client.messages.create(
            body=message,
            from_=f"whatsapp:{TWILIO_WHATSAPP_NUMBER}",
            to="whatsapp:+919791805322"
        )
    except:
        pass

def make_support_call():
    try:
        twilio_client.calls.create(
            twiml="<Response><Say>Customer has requested a support call.</Say></Response>",
            from_=TWILIO_CALL_NUMBER,
            to="+919791805322"
        )
    except:
        pass

# ===============================
# MODEL LOADING
# ===============================
@st.cache_resource
def load_model():
    return joblib.load("pv_baseline_model.pkl"), joblib.load("pv_model_features.pkl")

model, features = load_model()

# ===============================
# UTILITIES
# ===============================
def calculate_tneb_bill(units):
    bill = 0.0
    if units < 100:
        bill += units * 2.25
    if units > 100:
        bill += min(units - 100, 100) * 3.50
    if units > 200:
        bill += min(units - 200, 200) * 4.50
    if units > 400:
        bill += min(units - 400, 200) * 6.00
    if units > 600:
        bill += min(units - 600, 200) * 8.00
    if units > 800:
        bill += (units - 800) * 9.00
    return bill

def get_live_prediction():
    actual = np.random.uniform(3200, 3800)
    predicted = 4000
    energy = actual / 1000
    return {
        "actual": actual,
        "predicted": predicted,
        "energy": energy,
        "money": calculate_tneb_bill(energy),
        "carbon": energy * 0.82,
        "trees": int(energy * 0.05),
        "insight": (
            "Output is below expected — possible soiling or shading."
            if actual < 0.85 * predicted
            else "System operating within expected parameters."
        )
    }

# ===============================
# PERFORMANCE TREND DATA (GRAPH)
# ===============================
def get_performance_trend():
    times = pd.date_range(end=datetime.now(), periods=18, freq="5min")
    actual = np.random.uniform(3000, 3800, size=len(times))
    predicted = np.full(len(times), 4000)

    return pd.DataFrame({
        "Time": times,
        "Actual Power (W)": actual,
        "Expected Power (W)": predicted
    }).set_index("Time")

# ===============================
# ENERGY DECISION ENGINE
# ===============================
def energy_decision_engine(pred):
    surplus = (pred["actual"] / 1000) - 0.8
    if surplus > 1.0:
        return {"decision": "You can run heavy appliances now",
                "reason": "Solar generation exceeds base load by >1 kW",
                "confidence": "High"}
    elif surplus > 0.3:
        return {"decision": "Light appliance usage is safe now",
                "reason": "Minor solar surplus available",
                "confidence": "Medium"}
    else:
        return {"decision": "Avoid heavy appliance usage now",
                "reason": "Likely grid import if load increases",
                "confidence": "High"}
    

    

# ===============================
# APPLIANCES
# ===============================
APPLIANCES = {
    "Washing Machine": 1.2,
    "Air Conditioner": 1.5,
    "Water Heater": 2.0,
    "EV Charger": 3.3
}

def appliance_advice(pred):
    available = (pred["actual"] / 1000) - 0.8
    safe = [a for a, k in APPLIANCES.items() if k <= available]
    return f"You can safely run: {', '.join(safe)}" if safe else \
        "No heavy appliance can run safely without grid usage right now."



# ===============================
# NAVIGATION
# ===============================
# Sidebar background color
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        background-color: #38b6ff;  /* Blue sidebar */
        padding-top: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Sidebar header "Solrrbox" fully white
st.sidebar.markdown(
    """
    <h1 style='font-size:36px; font-weight:bold; color:white; margin-bottom:30px;'>
        Solrrbox
    </h1>
    """,
    unsafe_allow_html=True
)


st.markdown("""
<style>
/* Sidebar background */
[data-testid="stSidebar"] {
    background-color: #38b6ff;  /* your blue */
}

/* Sidebar radio label (menu items) */
[data-testid="stSidebar"] label {
    color: white !important;
    font-size: 1.2rem; /* make menu items bigger */
}

/* Sidebar title (radio group label) */
[data-testid="stSidebar"] .css-1d391kg, 
[data-testid="stSidebar"] .stMarkdown h2 {
    color: white !important;
    font-size: 1.6rem;  /* increase menu title */
    font-weight: 600;
}

/* Sidebar radio button hover */
[data-testid="stSidebar"] div[role="radiogroup"] > div:hover {
    background-color: #2aa0e0;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# Sidebar menu
menu = st.sidebar.radio(
    "Menu",
    ["Home","Service", "SolB Chat", "Solar Panel Details", "Maintenance", "Impact Created", "Referral", "Profile", "Contact Us"]
)


# ===============================
# HOME
# ===============================
if menu == "Home":
    st.markdown(f"## Welcome back 👋")
    pred = get_live_prediction()

    # Add CSS for the cards
    st.markdown("""
    <style>
    .card {
        background-color: #f3f9f9;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-bottom: 10px;
    }
    .metric-title {
        font-size: 1rem;
        color: #555;
        margin-bottom: 8px;
    }
    .metric-value {
        font-size: 1.5rem;
        font-weight: bold;
        color: #38b6ff;
    }
    </style>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    for col, title, value, unit in [
        (c1, "Actual Power", pred["actual"], "W"),
        (c2, "Expected Power", pred["predicted"], "W"),
        (c3, "Energy Generated", pred["energy"], "kWh"),
        (c4, "Money Saved", pred["money"], "₹")
    ]:
        col.markdown(
            f"""
            <div class="card">
                <div class="metric-title">{title}</div>
                <div class="metric-value">{value:.1f} {unit}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
                
    st.markdown("### Current Performance")
    st.info(pred["insight"])

   


    # ===== GRAPH ADDED HERE =====
    st.markdown("### 📈 Solar Performance Trend (Last 90 Minutes)")
    trend_df = get_performance_trend()
    st.line_chart(trend_df)

    

    ede = energy_decision_engine(pred)
    st.markdown("### 🔍 What should you do right now?")
    st.markdown(f"**Decision:** {ede['decision']}\n\n**Why:** {ede['reason']}\n\n**Confidence:** {ede['confidence']}")

    # Appliance advice as an info box
    st.info(appliance_advice(pred))


# ===============================
# PROFILE
# ===============================
elif menu == "Profile":
    st.markdown("## Profile Information")
    st.text_input("Name", "Harini Hemavarshini")
    st.text_input("Phone", "+919791805322")
    st.text_area("Address", "106, Gandhi Nagar, Veloore-632001")
    st.text_input("Customer ID", "SOLRR-001", disabled=True)

# ===============================
# MAINTENANCE
# ===============================
elif menu == "Maintenance":
    st.markdown("## Maintenance Schedule")
    st.success("Status: Active")
    st.write("Start Date: January 2026")
    st.write("End Date: March 2026")
    st.warning("Next maintenance due in 2 months")

# ===============================
# SOLAR DETAILS
# ===============================
elif menu == "Solar Panel Details":
    st.markdown("## Solar Panel Details")
    st.write("Capacity Installed: 5 kW")
    st.write("Module Count: 12")
    st.write("Module Brand: Goldi Solar")
    st.write("Inverter: Growatt Inverter")
    st.write("Maintenance Package: Active")
    st.download_button("Download Warranty", "Warranty PDF")
    st.download_button("Download Bills", "Bills PDF")


# ===============================
# SERVICE
# ===============================
elif menu == "Service":
    st.markdown("## Request a Service")

    # Service options as "tabs" (columns with buttons)
    services = ["Maintenance", "Cleaning", "Routine Check-up", "Inverter Service", "Other"]
    cols = st.columns(len(services))

    # Store selected service in session state
    if "selected_service" not in st.session_state:
        st.session_state.selected_service = None

    for i, s in enumerate(services):
        if cols[i].button(s):
            st.session_state.selected_service = s

    # Show selected service
    if st.session_state.selected_service:
        st.markdown(f"**Selected Service:** {st.session_state.selected_service}")

        # Optional message
        service_message = st.text_area("Add a message to your request (optional)")

        # Checkbox for call
        call_requested = st.checkbox("Request a call")

        # Submit button
        if st.button("Submit Request"):
            full_message = f"Service Request: {st.session_state.selected_service}"
            if service_message:
                full_message += f"\nMessage: {service_message}"

            st.success("Solrrbox professional will contact you shortly.")

            # Send alerts
            send_sms_alert(full_message)
            send_whatsapp_alert(full_message)
            if call_requested:
                make_support_call()

            # Reset selection after sending
            st.session_state.selected_service = None



# ===============================
# IMPACT
# ===============================
elif menu == "Impact Created":
    import math
    import plotly.express as px

    st.markdown("## 🌱 Environmental Impact (2026)")

    # Load dataset
    df = pd.read_csv("PV_dataset/Zone A4.csv")  # Replace with your dataset path
    df["Time"] = pd.to_datetime(df["Time"], dayfirst=True)

    # Filter data for 2026 up to today
    start_2026 = pd.Timestamp("2026-01-01")
    today = pd.Timestamp.now()
    df = df[(df["Time"] >= start_2026) & (df["Time"] <= today)]

    if df.empty:
        st.warning("No data available for 2026.")
        st.stop()

    # Ensure correct energy column
    if "generation(kWh)" in df.columns:
        df["Energy_kWh"] = df["generation(kWh)"]
    else:
        st.error("Dataset must have 'generation(kWh)' column.")
        st.stop()

    # Calculate carbon savings per row
    df["Carbon_kg"] = df["Energy_kWh"] * 0.82

    # Total energy and environmental impact
    total_energy = df["Energy_kWh"].sum()
    total_carbon = df["Carbon_kg"].sum()
    total_trees = math.ceil(total_energy * 0.05)

    # Display metric cards
    c1, c2, c3 = st.columns(3)
    metrics = [
        ("Carbon Reduced", f"{total_carbon:.2f}", "kg"),
        ("Trees Saved", total_trees, ""),
        ("Electricity Generated", f"{total_energy:.2f}", "kWh")
    ]
    for col, (title, value, unit) in zip([c1, c2, c3], metrics):
        col.markdown(
            f"""
            <div style="
                background-color: white;
                border-radius: 12px;
                padding: 1.5rem;
                box-shadow: 0 6px 18px rgba(0,0,0,0.06);
                text-align: center;
            ">
                <div style="font-size: 0.9rem; color: #555;">{title}</div>
                <div style="font-size: 1.8rem; font-weight: 600;">{value} {unit}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.markdown("### Daily Carbon Savings (2026)")

    # Aggregate by day
    df["Date"] = df["Time"].dt.date
    daily_carbon = df.groupby("Date")["Carbon_kg"].sum().reset_index()

    # Plot bar chart in blue shades
    fig = px.bar(
        daily_carbon,
        x="Date",
        y="Carbon_kg",
        text="Carbon_kg",
        labels={"Carbon_kg": "Carbon Reduced (kg)"},
        color="Carbon_kg",
        color_continuous_scale=px.colors.sequential.Blues,
        height=400
    )
    fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig.update_layout(
        margin=dict(t=20, b=20, l=20, r=20),
        coloraxis_showscale=False,
        xaxis_tickangle=-45
    )
    st.plotly_chart(fig, use_container_width=True)



# ===============================
# REFERRAL
# ===============================
elif menu == "Referral":
    st.markdown("## Refer & Earn")
    st.metric("Total Points", 120)
    st.metric("Referrals", 4)
    st.button("Refer Now")

# ===============================
# CONTACT
# ===============================
elif menu == "Contact Us":
    st.markdown("## Contact Us")
    st.write("📞 +91-9842330390")
    st.write("✉️ support@solrrbox.com")
    st.write("🔗 LinkedIn: Solrrbox")

# ===============================
# SOLB CHAT
# ===============================
elif menu == "SolB Chat":
    st.markdown("##  Hello I'm SolB, your personalised solar AI assistant !")
    st.markdown("Wondering about your solar setup? Let me help you!")

    st.markdown("""
    <style>
    .user-msg {background-color: #DCF8C6; padding: 8px 12px; border-radius: 12px; margin: 5px 0; max-width: 80%; text-align: left;}
    .ai-msg {background-color: #E8E8E8; padding: 8px 12px; border-radius: 12px; margin: 5px 0; max-width: 80%; text-align: left;}
    .chat-container {display: flex; flex-direction: column;}
    .user-msg-container {align-self: flex-end;}
    .ai-msg-container {align-self: flex-start;}
    </style>
    """, unsafe_allow_html=True)

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_question = st.text_input("Type your message here and press Enter:")

    if user_question:
        pred = get_live_prediction()
        prompt = f"""
        You are SolB, an expert AI assistant for solar panels.
        Current system data:
        - Actual Power: {pred['actual']:.1f} W
        - Expected Power: {pred['predicted']:.1f} W
        - Energy Generated: {pred['energy']:.2f} kWh
        - Money Saved: ₹{pred['money']:.2f}
        - Carbon Reduced: {pred['carbon']:.2f} kg
        - Trees Saved: {pred['trees']}
        - Insight: {pred['insight']}
        User Question: {user_question}
        Provide a short, concise answer with actionable insight.
        """
        try:
            genai.configure(api_key="AIzaSyA6gn_WThjaKJXQSwxk-TDSv7bfMbYz4aY")
            model_gemini = genai.GenerativeModel("gemini-2.5-flash")
            response = model_gemini.generate_content([prompt])
            st.session_state.chat_history.append(("You", user_question))
            st.session_state.chat_history.append(("SolB", response.text))
        except Exception as e:
            st.error(f"Error from SolB: {e}")

    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for speaker, message in st.session_state.chat_history:
        if speaker == "You":
            st.markdown(f'<div class="user-msg-container"><div class="user-msg">{message}</div></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="ai-msg-container"><div class="ai-msg">{message}</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
