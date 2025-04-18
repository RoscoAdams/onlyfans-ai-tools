import uuid
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import streamlit as st
import bcrypt
from caption_generator import generate_captions
from scheduler import scheduler_ui
from personas import persona_prompts
from dm_generator import generate_dm_reply, generate_mass_dm
from email_utils import send_reset_email
from dotenv import load_dotenv
import os
import requests
import json
import streamlit.components.v1 as components

load_dotenv()

# Google Sheets auth
creds_path = st.secrets["CREDS"]

# Paystack payment details
PAYSTACK_PUBLIC_KEY = st.secrets["PAYSTACK_PUBLIC_KEY"]
PAYSTACK_SECRET_KEY = st.secrets["PAYSTACK_SECRET_KEY"]
PAYSTACK_CALLBACK_URL = st.secrets["PAYSTACK_CALLBACK_URL"]


def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        creds_path, scope)
    client = gspread.authorize(creds)
    return client.open("OnlyFansAIUsers").sheet1


def get_user(sheet, email):
    users = sheet.get_all_records()
    for i, row in enumerate(users):
        if row["Email"] == email:
            return row, i + 2
    return None, None


def register_user(sheet, email, password):
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    trial_end = (datetime.utcnow() + timedelta(hours=24)
                 ).strftime('%Y-%m-%d %H:%M:%S')
    sheet.append_row(
        [email, hashed_password.decode('utf-8'), trial_end, "trial"])
    return {"Email": email, "Password": hashed_password.decode('utf-8'), "TrialEnd": trial_end, "Plan": "trial"}


def verify_password(stored_hash, password):
    return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))


def reset_password(sheet, email):
    user_data, row_num = get_user(sheet, email)
    if user_data:
        temp_password = "TEMP_1234"  # Replace with secure random generator
        hashed_temp_password = bcrypt.hashpw(
            temp_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        sheet.update_cell(row_num, 2, hashed_temp_password)
        return temp_password
    return None


# Setup UI
st.set_page_config(page_title="Creator AI Panel", layout="wide")
# ✅ Init session state FIRST!
if "user_data" not in st.session_state:
    st.session_state.user_data = None
if "payment_reference" not in st.session_state:
    st.session_state.payment_reference = None
if "selected_plan" not in st.session_state:
    st.session_state.selected_plan = None

st.title("💋 OnlyFans AI Assistant")
st.subheader("Manage your seductive empire with AI.")

query_params = st.query_params
if "email" in query_params and st.session_state.user_data is None:
    sheet = get_sheet()
    email = query_params["email"][0]
    user_data, _ = get_user(sheet, email)
    if user_data:
        st.session_state.user_data = user_data
if "ref" in query_params and "plan" in query_params:
    st.session_state.payment_reference = query_params["ref"][0]
    st.session_state.selected_plan = query_params["plan"][0]


# Login / Register / Password Reset UI
if st.session_state.get("user_data") is None:
    with st.sidebar:
        st.header("🔐 Login or Register")
        mode = st.radio(
            "Choose mode", ["Login", "Register", "Forgot Password"])
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        auth_btn = st.button(mode)

        if auth_btn and email:
            sheet = get_sheet()
            if mode == "Login" and password:
                user_data, _ = get_user(sheet, email)
                if user_data:
                    if verify_password(user_data["Password"], password):
                        st.session_state.user_data = user_data
                        if "TEMP_" in password:
                            st.session_state.force_password_change = True
                        else:
                            st.success("✅ Logged in successfully!")
                            st.rerun()
                    else:
                        st.error("❌ Incorrect password.")
                else:
                    st.error("❌ No account found. Please register.")
            elif mode == "Register" and password:
                user_data, _ = get_user(sheet, email)
                if user_data:
                    st.error("❌ Email already registered. Please log in.")
                else:
                    new_user = register_user(sheet, email, password)
                    st.session_state.user_data = new_user
                    st.success("✅ Registered and logged in!")
                    st.rerun()
            elif mode == "Forgot Password":
                temp_password = reset_password(sheet, email)
                if temp_password:
                    if send_reset_email(email, temp_password):
                        st.success(
                            "✅ A temporary password has been sent to your email.")
                    else:
                        st.error(
                            "❌ Failed to send email. Please try again later.")
                else:
                    st.error("❌ No account found with this email.")

if st.session_state.user_data is None:
    st.stop()

# Force password change
if st.session_state.get("force_password_change"):
    st.warning("⚠️ You're using a temporary password. Please change it now.")
    new_pass = st.text_input("New Password", type="password")
    confirm_pass = st.text_input("Confirm Password", type="password")
    change_btn = st.button("Change Password")

    if change_btn:
        if new_pass != confirm_pass:
            st.error("❌ Passwords do not match.")
        elif len(new_pass) < 6:
            st.error("❌ Password must be at least 6 characters.")
        else:
            sheet = get_sheet()
            _, row_num = get_user(sheet, st.session_state.user_data["Email"])
            new_hash = bcrypt.hashpw(new_pass.encode(
                'utf-8'), bcrypt.gensalt()).decode('utf-8')
            sheet.update_cell(row_num, 2, new_hash)
            st.success("✅ Password changed successfully!")
            del st.session_state["force_password_change"]
            st.rerun()

    st.stop()

# ✅ Payment Verification
if st.session_state.payment_reference and st.session_state.selected_plan:
    ref = st.session_state.payment_reference
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
    verify_url = f"https://api.paystack.co/transaction/verify/{ref}"

    response = requests.get(verify_url, headers=headers)
    if response.status_code == 200 and response.json()["data"]["status"] == "success":
        st.success("✅ Payment confirmed! You're now on a paid plan.")
        sheet = get_sheet()
        _, row_num = get_user(sheet, st.session_state.user_data["Email"])
        plan_type = st.session_state.selected_plan
        vip_start = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

        sheet.update_cell(row_num, 4, plan_type)  # Column D = Plan
        # Column E = VIPStart (NEW COLUMN)
        sheet.update_cell(row_num, 5, vip_start)

        st.session_state.user_data["Plan"] = plan_type
        st.session_state.user_data["VIPStart"] = vip_start
        st.session_state.payment_reference = None
        st.session_state.selected_plan = None

        st.query_params.clear()

        st.rerun()

    elif response.status_code == 200:
        st.warning("⚠️ Payment not yet confirmed. Click to retry.")
        if st.button("🔁 Retry Verification"):
            st.rerun()


# Access Control
user_data = st.session_state.user_data
now = datetime.utcnow()
trial_expired = now > datetime.strptime(
    user_data["TrialEnd"], '%Y-%m-%d %H:%M:%S')
paid_user = False
if user_data["Plan"] == "vip":
    try:
        vip_start = datetime.strptime(user_data.get(
            "VIPStart", ""), '%Y-%m-%d %H:%M:%S')
        if now <= vip_start + timedelta(days=30):
            paid_user = True
        else:
            # Automatically downgrade user after 30 days
            sheet = get_sheet()
            _, row_num = get_user(sheet, user_data["Email"])
            sheet.update_cell(row_num, 4, "expired")  # Column D = Plan
            st.session_state.user_data["Plan"] = "expired"
    except Exception as e:
        st.warning("⚠️ VIP expiration check failed.")
        st.text(f"Details: {e}")


if not paid_user and trial_expired:
    st.error("⛔ Your free trial has expired.")
    st.warning("⛔ Please upgrade to continue using the platform.")

    st.markdown("🎉 **Unlock full access with the VIP Plan**")
    vip_price = 499 * 100

    if "Email" not in st.session_state.user_data or not st.session_state.user_data["Email"]:
        st.error("Please log in again before upgrading.")
        st.stop()

    if st.button("💳 Upgrade to VIP"):
        reference = str(uuid.uuid4())
        email = user_data.get("Email", "default@example.com")
        if not email or "@" not in email:
            st.error(
                "❌ Your email address is invalid or missing. Please log out and log back in.")
            st.stop()

        headers = {
            "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "email": email.strip(),
            "amount": vip_price,
            "reference": reference,
            # "callback_url": f"{PAYSTACK_CALLBACK_URL}?ref={reference}&plan=vip&email={email}"
        }

        response = requests.post(
            "https://api.paystack.co/transaction/initialize", json=payload, headers=headers)

        if response.status_code == 200:
            pay_url = response.json()["data"]["authorization_url"]
            st.session_state.payment_reference = reference
            st.session_state.selected_plan = "vip"

            js_inline = f"""
            <script src="https://js.paystack.co/v1/inline.js"></script>
            <script>
            function payWithPaystack() {{
                var handler = PaystackPop.setup({{
                    key: '{PAYSTACK_PUBLIC_KEY}',
                    email: '{email}',
                    amount: {vip_price},
                    currency: 'ZAR',
                    ref: '{reference}',
                    callback: function(response) {{
                        // Payment complete, redirect to Streamlit with query params
                        const newUrl = new URL(window.location.href);
                        newUrl.searchParams.set("ref", response.reference);
                        newUrl.searchParams.set("plan", "vip");
                        window.location.href = newUrl.toString();
                    }},
                    onClose: function() {{
                        alert('Payment window closed.');
                    }}
                }});
                handler.openIframe();
            }}
            </script>

            <button onclick="payWithPaystack()">💳 Pay Now</button>
            """

            components.html(js_inline, height=300)

        else:
            st.error("⚠️ Failed to initialize payment.")
            st.text(f"Status code: {response.status_code}")
            st.text(f"Details: {response.text}")

    st.stop()

# Logout
with st.sidebar:
    if st.button("Logout"):
        st.session_state.user_data = None
        st.rerun()

# Main App
selected_persona = st.selectbox(
    "Select your persona", list(persona_prompts.keys()))
st.markdown(f"**Style**: {persona_prompts[selected_persona]}")

tab1, tab2, tab3 = st.tabs(
    ["🖋️ Caption Generator", "📆 Content Scheduler", "💬 DM Generator"])

with tab1:
    st.subheader("Generate Captions")
    st.markdown(
        "✨ **What this does:** Automatically generates flirty, engaging, or bold captions based on your chosen persona and the photo description you provide. Great for saving time and staying consistent with your brand tone.")
    photo_desc = st.text_input("Describe the photo/outfit")
    if st.button("Generate"):
        captions = generate_captions(
            selected_persona, persona_prompts[selected_persona], photo_desc)
        st.markdown(captions)

with tab2:
    st.subheader("Schedule Your Content")
    st.markdown(
        "📆 **What this does:** Plan your posts in advance with suggested captions and personas. Makes it easier to stay consistent and reduce the stress of last-minute posting.")
    scheduler_ui(selected_persona)

with tab3:
    st.subheader("💌 Auto-DM Assistant")
    st.markdown(
        "💬 **What this does:** Create personalized replies to fan messages and generate themed promo messages you can use for mass DMs. Keeps your audience engaged and increases your chances of converting subscribers.")
    st.markdown("### 1. Fan Reply Generator")
    user_msg = st.text_input("Fan message:")
    if st.button("Generate Reply"):
        reply = generate_dm_reply(
            selected_persona, persona_prompts[selected_persona], user_msg)
        st.success(reply)

    st.markdown("---")
    st.markdown("### 2. Promo Blast Message")
    campaign = st.text_input(
        "What's the theme? (e.g. Shower Set, Tease Tuesday)")
    if st.button("Generate Promo Message"):
        promo = generate_mass_dm(
            selected_persona, persona_prompts[selected_persona], campaign)
        st.info(promo)

st.caption("Built by RCA.")
