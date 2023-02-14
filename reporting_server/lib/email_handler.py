import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

#SET EMAIL PARAMETERS
send_address = os.environ["SEND_ADDRESS"]
send_password = os.environ["SEND_PASSWORD"]
smtp_address = os.environ["SMTP_ADDRESS"]
smtp_port = int(os.environ["SMTP_PORT"])

#EMAIL FUNCTIONS
def email_attachment(mail_content, receiver_address, subject, file):
    sender_address = send_address
    sender_password = send_password
    message = MIMEMultipart()
    message['From'] = sender_address
    message['To'] = receiver_address
    message['Subject'] = subject
    message.attach(MIMEText(mail_content, 'plain'))
    attach_file_name = file
    attach_file = open(attach_file_name, "rb")
    payload = MIMEBase('application', 'octate-stream')
    payload.set_payload(attach_file.read())
    encoders.encode_base64(payload)
    payload.add_header('Content-Disposition', 'attachment', filename='report_output.csv')
    message.attach(payload) 
    s = smtplib.SMTP(smtp_address, int(smtp_port))
    s.starttls()
    s.login(sender_address, sender_password)
    text = message.as_string()  
    s.sendmail(sender_address, receiver_address, text)
    s.quit()  