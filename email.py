pip install -r requirements1.txt

import streamlit as st
import pandas as pd
import smtplib
import schedule
import time
import threading
import datetime
import matplotlib.pyplot as plt
from io import BytesIO
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import base64

# Streamlit Page Config
st.set_page_config(page_title="Trading Desk Email Sender", layout="wide")

# Title
st.title(" Trading Room Mass Email Sender")

# Sidebar - SMTP Settings
st.sidebar.header(" Email Settings")
email_sender = st.sidebar.text_input("Sender Email")
email_password = st.sidebar.text_input("Password", type="password")
smtp_server = st.sidebar.text_input("SMTP Server", value="smtp.gmail.com")
smtp_port = st.sidebar.number_input("SMTP Port", value=587, step=1)

# Upload Excel file
uploaded_file = st.file_uploader(" Upload an Excel file with client data", type=["xlsx"])

# Email Composition
st.header("Email Customization")
subject = st.text_input("Email Subject", "Market Update: {market_index} Drops {change}%")
message_body = st.text_area(
    "Email Body (Use {placeholders} from Excel)", 
    """Dear {client_name},

The market is experiencing significant movements today, with {market_index} showing a change of {change}%.
Key factors:
- {sector_impact}
- {market_drivers}
- {trade_recommendation}

See the attached chart for more details.

Best regards,
{trading_desk_name}
"""
)

# File attachment option
attachment = st.file_uploader("Attach a file (optional)", type=["pdf", "docx", "xlsx", "png", "jpg", "jpeg"])

# Email Scheduling
st.sidebar.header("Schedule Email")
schedule_enabled = st.sidebar.checkbox("Enable Scheduling")
send_time = st.sidebar.time_input("Select Time for Scheduled Send", datetime.time(9, 0))

# Display Data Preview
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.write("Preview of uploaded data:")
    st.dataframe(df)

    if "Email" not in df.columns:
        st.error(" The Excel file must contain an 'Email' column.")
    else:
        # Generate Chart
        def create_market_chart():
            fig, ax = plt.subplots(figsize=(6, 3))
            ax.plot([1, 2, 3, 4, 5], [10, 12, 8, 15, 9], marker="o", linestyle="-")
            ax.set_title("Market Trend Overview")
            ax.set_xlabel("Time")
            ax.set_ylabel("Price")
            buf = BytesIO()
            fig.savefig(buf, format="png")
            buf.seek(0)
            return buf

        market_chart = create_market_chart()

        # Function to send emails
        def send_emails():
            try:
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
                server.login(email_sender, email_password)
                
                for _, row in df.iterrows():
                    email_receiver = row["Email"]
                    try:
                        formatted_subject = subject.format(**row)
                        formatted_body = message_body.format(**row)
                    except KeyError as e:
                        st.error(f"Error: Column {e} is missing in the Excel file!")
                        continue

                    msg = MIMEMultipart()
                    msg["From"] = email_sender
                    msg["To"] = email_receiver
                    msg["Subject"] = formatted_subject

                    # Embed Chart
                    img_data = market_chart.getvalue()
                    img_base64 = base64.b64encode(img_data).decode()
                    img_tag = f'<img src="data:image/png;base64,{img_base64}" width="600px"/>'
                    formatted_body_html = f"<html><body>{formatted_body}<br>{img_tag}</body></html>"

                    msg.attach(MIMEText(formatted_body_html, "html"))

                    # Attach File
                    if attachment:
                        file_name = attachment.name
                        attachment.seek(0)
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(attachment.read())
                        encoders.encode_base64(part)
                        part.add_header("Content-Disposition", f"attachment; filename={file_name}")
                        msg.attach(part)

                    server.sendmail(email_sender, email_receiver, msg.as_string())
                    st.success(f" Email sent to {email_receiver}")

                server.quit()
                st.success(" All emails have been sent successfully!")

            except Exception as e:
                st.error(f" Error: {e}")

        # Schedule Email Sending
        def schedule_email_sending():
            while True:
                now = datetime.datetime.now().time()
                if now.hour == send_time.hour and now.minute == send_time.minute:
                    send_emails()
                    break
                time.sleep(30)  # Check every 30 seconds

        # Buttons for immediate or scheduled sending
        if st.button("Send Emails Now"):
            send_emails()

        if schedule_enabled and st.sidebar.button("Schedule Emails"):
            st.sidebar.success(f" Emails scheduled for {send_time.strftime('%H:%M')}")
            thread = threading.Thread(target=schedule_email_sending)
            thread.start()

        # Email Sending Report
        st.header("Email Sending Report")
        report = pd.DataFrame(columns=["Email", "Status"])
        for _, row in df.iterrows():
            report = report.append({"Email": row["Email"], "Status": "Pending"}, ignore_index=True)
        st.dataframe(report)
