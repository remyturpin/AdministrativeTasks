import streamlit as st
import pandas as pd
import smtplib
import schedule
import threading
import datetime
import time
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
st.title("Trading Room Mass Email Sender")

# Sidebar - SMTP Settings
st.sidebar.header("Email Settings")
email_sender = st.sidebar.text_input("Sender Email")
email_password = st.sidebar.text_input("Password", type="password")
smtp_server = st.sidebar.text_input("SMTP Server", value="smtp.gmail.com")
smtp_port = st.sidebar.number_input("SMTP Port", value=587, step=1)

# Upload Excel file
uploaded_file = st.file_uploader("Upload an Excel file with client data", type=["xlsx"])

# Email Composition
st.header("Email Customization")
subject = st.text_input("Email Subject", "Market Update: {market_index} Drops {change}%")

message_body = st.text_area(
    "Email Body (Use {placeholders} from Excel)",
    """<html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.5;
                color: #333;
            }}
            .container {{
                width: 600px;
                margin: 0 auto;
                padding: 20px;
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #f9f9f9;
            }}
            h2 {{
                color: #0056b3;
            }}
            p {{
                margin: 10px 0;
            }}
            .chart-container {{
                text-align: center;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <p>Dear <strong>{client_name}</strong>,</p>

            <p>The market is experiencing significant movements today, with 
            <strong>{market_index}</strong> showing a change of 
            <strong>{change}%</strong>.</p>

            <p><strong>Key factors:</strong></p>
            <ul>
                <li>{sector_impact}</li>
                <li>{market_drivers}</li>
                <li>{trade_recommendation}</li>
            </ul>

            <p>See the attached chart for more details.</p>

            <p>Best regards,<br><strong>{trading_desk_name}</strong></p>

            <div class="chart-container">
                <h2>Market Trend - {market_index} (Last 7 Days)</h2>
                <img src="data:image/png;base64,{img_base64}" width="550px"/>
            </div>
        </div>
    </body>
    </html>
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
    df = pd.read_excel(uploaded_file, engine="openpyxl")
    df.columns = df.columns.str.strip()  #Supprime les espaces cachés
    st.write("Preview of uploaded data:")
    st.dataframe(df)

    if "Email" not in df.columns:
        st.error("The Excel file must contain an 'Email' column.")
    else:
        # Initialisation du rapport d'envoi
        report = pd.DataFrame(columns=["Email", "Status"])  #Ajout du DataFrame

        # Function to create and embed a chart
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

                for index, row in df.iterrows():
                    email_receiver = row.loc["Email"]

                    if not pd.notna(email_receiver) or email_receiver.strip() == "":
                        st.error("One of the emails is empty! Check the Excel file.")
                        continue

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
                    report.loc[len(report)] = {"Email": email_receiver, "Status": "Sent"}
                    st.success(f"Email sent to {email_receiver}")

                server.quit()
                st.success("All emails have been sent successfully!")
                st.dataframe(report)

            except Exception as e:
                st.error(f"Error: {e}")

        # Schedule Email Sending
        def scheduled_job():
            send_emails()

        if schedule_enabled:
            schedule.clear()
            schedule.every().day.at(send_time.strftime("%H:%M")).do(scheduled_job)

            def run_scheduler():
                while True:
                    schedule.run_pending()
                    time.sleep(60)  # Check every 60 seconds

            if st.sidebar.button("Schedule Emails"):
                threading.Thread(target=run_scheduler, daemon=True).start()
                st.sidebar.success(f"Emails scheduled for {send_time.strftime('%H:%M')}")

        # Buttons for immediate sending
        if st.button("Send Emails Now"):
            send_emails()
