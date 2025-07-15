import streamlit as st
from supabase import create_client, Client
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from datetime import datetime
import os
try:
    supabase_url = st.secrets["SUPABASE_URL"]
    supabase_anon_key = st.secrets["SUPABASE_ANON_KEY"]
    sendgrid_api_key = st.secrets["SENDGRID_API_KEY"]
    sender_email = st.secrets["SENDER_EMAIL"]
except KeyError:
    st.error("Please set your Supabase URL, Supabase Anon Key, SendGrid API Key, and Sender Email in Streamlit Secrets (`.streamlit/secrets.toml`).")
    st.stop() # Stop the app if secrets are not configured
try:
    supabase: Client = create_client(supabase_url, supabase_anon_key)
except Exception as e:
    st.error(f"Error initializing Supabase client: {e}")
    st.stop()

# --- Streamlit Application UI ---
st.set_page_config(page_title="User Registration & Email Sender", layout="centered")
st.title("Register and Get Your Welcome Email!")
st.markdown("Enter your details below to register and receive a confirmation email.")
with st.form("registration_form"):
    first_name = st.text_input("First Name", placeholder="John")
    last_name = st.text_input("Last Name", placeholder="Doe")
    email = st.text_input("Email", placeholder="john.doe@example.com")
    submitted = st.form_submit_button("Register & Send Email")
    if submitted:
        if not first_name or not last_name or not email:
            st.warning("Please fill in all fields.")
        elif "@" not in email or "." not in email:
            st.warning("Please enter a valid email address.")
        else:
            current_time = datetime.now().isoformat()
            table_name = "Email Database"
            user_data = {
                "First Name": first_name,
                "Last Name": last_name,
                "Email": email,
                "Status": "Email Sent",
                "Email Date": current_time}
            try:
                response = supabase.table(table_name).insert(user_data).execute()
                if response.data:
                    st.success(f"Successfully added {first_name} {last_name} to Supabase!")
                    st.json(response.data) # Display the inserted data for debugging
                else:
                    st.error(f"Failed to add data to Supabase. Response: {response.status_code} - {response.text}")
                    st.json(response) # Display full response for debugging
                    st.stop()
            except Exception as e:
                st.error(f"An error occurred while adding data to Supabase: {e}")
                st.stop()
            try:
                sg = SendGridAPIClient(sendgrid_api_key)
                subject = f"{first_name} Virtual USAA Interview!"
                html_content = f"""
                <html>
                <body>
                    <p>Hello {first_name},</p>
                    <p style="margin: 0;">I am attaching a link to my schedule for USAA Interviews, please select the best time that works for you. If none of those times work, please reach out!</p>
                    <p style="margin: 0;">I look forward to interviewing you for the position!</p>
                    <p>Thank you,</p>
                    <br>
                    <table cellpadding="0" cellspacing="0" border="0">
                        <tr>
                            <td valign="middle" style="padding-right: 15px; width: 120px;">
                                <!-- Replace with your actual logo URL -->
                                <img src="https://github.com/Callaway-Crenshaw/USAA-AUTOMATION/blob/main/suryl_logo_rgb.png?raw=true" alt="Company Logo" width="80" height="auto" style="display: block;">
                            </td>
                            <td valign="top" style="border-left: 1px solid #e0e0e0; padding-left: 15px;">
                                <p style="margin: 0; font-size: 14px; line-height: 1.5;"><strong>Callaway Crenshaw</strong></p>
                                <p style="margin: 0; font-size: 14px; line-height: 1.5;">IT Analyst, Suryl</p>
                                <p style="margin: 0; font-size: 14px; line-height: 1.5;">405-403-9513 | <a href="mailto:Callaway.Crenshaw@Suryl.com" style="color: #1a73e8; text-decoration: none;">Callaway.Crenshaw@Suryl.com</a></p>
                                <p style="margin-top: 10px; font-size: 14px; line-height: 1.5;"><a href="https://outlook.office.com/bookwithme/user/e04031b927fb422fb39dbab02a827171@suryl.com/meetingtype/V5A9uUz5REmI_1DSxJ_lgQ2?anonymous&ep=mLinkFromTile" target="_blank" style="color: #1a73e8; text-decoration: none; font-weight: bold;">Book time to meet with me</a></p>
                            </td>
                        </tr>
                    </table>
                </body>
                </html>
                """
                message = Mail(
                    from_email=sender_email,
                    to_emails=email,
                    subject=subject,
                    html_content=html_content)
                sendgrid_response = sg.send(message)
                if sendgrid_response.status_code == 202:
                    st.success(f"Confirmation email sent to {email}!")
                else:
                    st.warning(f"Failed to send email. Status Code: {sendgrid_response.status_code}")
                    st.warning(f"SendGrid Response Body: {sendgrid_response.body}")
                    st.warning(f"SendGrid Response Headers: {sendgrid_response.headers}")
            except Exception as e:
                st.error(f"An error occurred while sending the email: {e}")
