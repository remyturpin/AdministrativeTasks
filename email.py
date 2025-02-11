import streamlit as st
import pandas as pd
import smtplib
import schedule
import threading
import datetime
import time
import yfinance as yf
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

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

# Function to create a chart with Yahoo Finance data
def create_market_chart(ticker):
    """
    Fetches historical stock data from Yahoo Finance for the past 7 days
    and generates a market trend chart.
    """
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="7d")

        if df.empty:
            return None

        fig, ax = plt.subplots(figsize=(6, 3))
        ax.plot(df.index, df["Close"], marker="o", linestyle="-", color="b", label=ticker)
        ax.set_title(f"Market Trend - {ticker} (Last 7 Days)")
        ax.set_xlabel("Date")
        ax.set_ylabel("Price")
        ax.legend()
        ax.grid(True)

        buf = BytesIO()
        fig.savefig(buf, format="png")
        buf.seek(0)
        return buf
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None

# Function to send emails
def send_emails():
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(email_sender, email_password)

        report = pd.DataFrame(columns=["Email", "Status"])

        for index, row in df.iterrows():
            email_receiver = row.loc["Email"]
            ticker = row.get("market_index", "").strip()

            if not ticker:
                st.error(f"No market index (ticker) found for {email_receiver}. Skipping.")
                continue

            market_chart = create_market_chart(ticker)
            if market_chart is None:
                st.error(f"No data found for {ticker}. Skipping email for {email_receiver}.")
                continue

            img_data = market_chart.getvalue()
            img_base64 = base64.b64encode(img_data).decode()
            img_tag = f'<img src="data:image/png;base64,{img_base64}" width="600px"/>'

            formatted_body_html = message_body.format(
                client_name=row["client_name"],
                market_index=row["market_index"],
                change=row["change"],
                sector_impact=row["sector_impact"],
                market_drivers=row["market_drivers"],
                trade_recommendation=row["trade_recommendation"],
                trading_desk_name=row["trading_desk_name"],
                img_base64=img_base64
            )

            msg = MIMEMultipart()
            msg["From"] = email_sender
            msg["To"] = email_receiver
            msg["Subject"] = subject.format(**row)
            msg.attach(MIMEText(formatted_body_html, "html"))

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
            time.sleep(60)

    if st.sidebar.button("Schedule Emails"):
        threading.Thread(target=run_scheduler, daemon=True).start()
        st.sidebar.success(f"Emails scheduled for {send_time.strftime('%H:%M')}")

# Buttons for immediate sending
if uploaded_file:
    df = pd.read_excel(uploaded_file, engine="openpyxl")
    df.columns = df.columns.str.strip()
    st.write("Preview of uploaded data:")
    st.dataframe(df)

    if "Email" in df.columns:
        if st.button(" Send Emails Now"):
            send_emails()

