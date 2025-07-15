import streamlit as st
from supabase import create_client, Client
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from datetime import datetime
import os

# --- Configuration (IMPORTANT: Use Streamlit Secrets or Environment Variables) ---
# It's highly recommended to use Streamlit Secrets for production.
# Create a `.streamlit/secrets.toml` file with your credentials:
# SUPABASE_URL = "YOUR_SUPABASE_URL"
# SUPABASE_ANON_KEY = "YOUR_SUPABASE_ANON_KEY"
# SENDGRID_API_KEY = "YOUR_SENDGRID_API_KEY"
# SENDER_EMAIL = "your_verified_sender_email@example.com" # Your SendGrid verified sender email

# For local testing, you can uncomment these and replace with your actual keys,
# but NEVER commit them to version control.
# SUPABASE_URL = os.environ.get("SUPABASE_URL", "YOUR_SUPABASE_URL")
# SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "YOUR_SUPABASE_ANON_KEY")
# SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "YOUR_SENDGRID_API_KEY")
# SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "your_verified_sender_email@example.com")

# Access credentials from Streamlit Secrets
try:
    supabase_url = st.secrets["SUPABASE_URL"]
    supabase_anon_key = st.secrets["SUPABASE_ANON_KEY"]
    sendgrid_api_key = st.secrets["SENDGRID_API_KEY"]
    sender_email = st.secrets["SENDER_EMAIL"]
except KeyError:
    st.error("Please set your Supabase URL, Supabase Anon Key, SendGrid API Key, and Sender Email in Streamlit Secrets (`.streamlit/secrets.toml`).")
    st.stop() # Stop the app if secrets are not configured

# Supabase client initialization
try:
    supabase: Client = create_client(supabase_url, supabase_anon_key)
except Exception as e:
    st.error(f"Error initializing Supabase client: {e}")
    st.stop()

# --- Streamlit Application UI ---
st.set_page_config(page_title="User Registration & Email Sender", layout="centered")

st.title("Register and Get Your Welcome Email!")
st.markdown("Enter your details below to register and receive a confirmation email.")

# Input fields
with st.form("registration_form"):
    first_name = st.text_input("First Name", placeholder="John")
    last_name = st.text_input("Last Name", placeholder="Doe")
    email = st.text_input("Email", placeholder="john.doe@example.com")

    submitted = st.form_submit_button("Register & Send Email")

    if submitted:
        # --- Input Validation ---
        if not first_name or not last_name or not email:
            st.warning("Please fill in all fields.")
        elif "@" not in email or "." not in email:
            st.warning("Please enter a valid email address.")
        else:
            # --- Data to Insert ---
            current_time = datetime.now().isoformat() # ISO format for Supabase timestamp
            table_name = "leads" # Assuming your table name is 'leads'

            user_data = {
                "First Name": first_name,
                "Last Name": last_name,
                "Email": email,
                "Status": "Email Sent", # Set status directly upon submission
                "Email Date": current_time
            }

            # --- 1. Add Row to Supabase ---
            try:
                response = supabase.table(table_name).insert(user_data).execute()
                # Supabase client returns a dictionary with 'data' key on success
                if response.data:
                    st.success(f"Successfully added {first_name} {last_name} to Supabase!")
                    st.json(response.data) # Display the inserted data for debugging
                else:
                    st.error(f"Failed to add data to Supabase. Response: {response.status_code} - {response.text}")
                    st.json(response) # Display full response for debugging
                    # If there's an error from Supabase, stop here and don't send email
                    st.stop()
            except Exception as e:
                st.error(f"An error occurred while adding data to Supabase: {e}")
                st.stop() # Stop the app if Supabase insert fails

            # --- 2. Send Email via SendGrid ---
            try:
                sg = SendGridAPIClient(sendgrid_api_key)
                subject = f"{first_name} Virtual USAA Interview!"
                html_content = f"""
                <html>
                <body>
                    <p>Hello {first_name},</p>
                    <br>
                    <p>I am attaching a link to my schedule for USAA Interviews, please select the best time that works for you. If none of those times work, please reach out!</p>
                    <p>I look forward to interviewing you for the position!</p>
                    <p>Thank you,</p>
                    <br>
                    <table cellpadding="0" cellspacing="0" border="0">
                        <tr>
                            <td valign="top" style="padding-right: 15px;">
                                <!-- Replace with your actual logo URL -->
                                <img src="C:\Users\CallawayCrenshaw\OneDrive - Suryl, LLC\Desktop\SURYL PROJECTS\RMS-USAA\USAA AUTOMATION\suryl_logo_rgb.png" alt="Company Logo" width="80" height="80" style="display: block;">
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
                    html_content=html_content
                )

                sendgrid_response = sg.send(message)

                if sendgrid_response.status_code == 202:
                    st.success(f"Confirmation email sent to {email}!")
                else:
                    st.warning(f"Failed to send email. Status Code: {sendgrid_response.status_code}")
                    st.warning(f"SendGrid Response Body: {sendgrid_response.body}")
                    st.warning(f"SendGrid Response Headers: {sendgrid_response.headers}")

            except Exception as e:
                st.error(f"An error occurred while sending the email: {e}")

# --- Instructions for Running ---
st.markdown("---")
st.subheader("How to Run This Application:")
st.markdown("""
1.  **Install Dependencies:**
    ```bash
    pip install streamlit supabase-py sendgrid
    ```
2.  **Configure Supabase and SendGrid Secrets:**
    Create a folder named `.streamlit` in the same directory as your Python script.
    Inside `.streamlit`, create a file named `secrets.toml` and add your credentials:
    ```toml
    SUPABASE_URL = "YOUR_SUPABASE_URL"
    SUPABASE_ANON_KEY = "YOUR_SUPABASE_ANON_KEY"
    SENDGRID_API_KEY = "YOUR_SENDGRID_API_KEY"
    SENDER_EMAIL = "your_verified_sender_email@example.com"
    ```
    *Replace the placeholder values with your actual Supabase project URL, Supabase "anon" public key, SendGrid API Key, and your verified sender email address.*

3.  **Run the Streamlit App:**
    Save the code above as a Python file (e.g., `app.py`) and run it from your terminal:
    ```bash
    streamlit run app.py
    ```
""")
