#----------------------------------------------------
#INITIALISATION
#----------------------------------------------------
import os
import pandas as pd
import mysql.connector
import smtplib
import datetime
import logging
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

logging.warning("Program Started")

#SET DB PARAMETERS
db_host = os.environ["DB_IP"]
db_user = os.environ["DB_USER"]
db_password = os.environ["DB_PASS"]
db_schema = os.environ["DB_SCHEMA"]
db_port = os.environ["DB_PORT"]

reports_dir = "/var/reports"

#SET EMAIL PARAMETERS
send_address = os.environ["SEND_ADDRESS"]
send_password = os.environ["SEND_PASSWORD"]
smtp_address = os.environ["SMTP_ADDRESS"]
smtp_port = int(os.environ["SMTP_PORT"])



#----------------------------------------------------
#UNDERLYING FUNCTIONS
#----------------------------------------------------
#READ FROM DB
def query_db(query):
    db = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_schema,
        port=db_port
    )
    cursor = db.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    return(result)

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

#def email_plain(mail_content, receiver_address, subject):
#    sender_address = send_address
#    sender_password = send_password
#    message = MIMEMultipart()
#    message['From'] = sender_address
#    message['To'] = receiver_address
#    message['Subject'] = subject
#    message.attach(MIMEText(mail_content, 'plain'))
#    s = smtplib.SMTP(smtp_address, int(smtp_port))
#    s.starttls()
#    s.login(sender_address, sender_password)
#    text = message.as_string()  
#    s.sendmail(sender_address, receiver_address, text)
#    s.quit() 

def return_clients():
    query = "SELECT id, pfsense_name, hostname, address FROM pfsense_instances"
    results = query_db(query)
    clients = []
    for row in results:
        client = [row[0], row[1], row[2], row[3]]
        clients = clients + [client,]
    return(clients)

#Function returns a standard format logs dataframe
def create_logs_df():
    df = pd.DataFrame(columns=["datetime", "rule number", "interface", "reason", "action", "direction", "IP Version", "Protocol", "Source IP", "Source Port", "Destination IP", "Destination Port", "Daily ML Check", "Weekly ML Check", "Combined ML Check"])
    return(df)

#Adds tuple values as row to standardized logs dataframe
def append_logs_df(tup, df):
    df = df.append(pd.Series([tup[0].strftime("%Y-%m-%d %H:%M:%S"), tup[1], tup[2], tup[3], tup[4], tup[5], tup[6], tup[7], tup[8], tup[9], tup[10], tup[11], tup[12], tup[13], tup[14]], index=df.columns), ignore_index=True)
    return(df)

def create_open_vpn_login_df():
    df = pd.DataFrame(columns=["VPN User", "Last Logon Date", "Last Logon Instance"])
    return(df)

#Adds tuple values as row to standardized logs dataframe
def append_open_vpn_login_df(tup, df):
    df = df.append(pd.Series([tup[0], tup[1], tup[2]], index=df.columns), ignore_index=True)
    return(df)

#----------------------------------------------------
#PRIMARY FUNCTIONS
#----------------------------------------------------
def combined_errors_report():
    final_results = []
    clients = return_clients()
    now = datetime.datetime.now()
    target = (now - datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    now = now.strftime("%Y-%m-%d %H:%M:%S")
    combined_error_query = """SELECT 
record_time,
rule_number,
pfsense_real_interface.interface,
pfsense_reason.reason,
pfsense_act.act,
pfsense_direction.direction,
ip_version,
pfsense_protocol.protocol,
pfsense_source_ip.ip,
source_port,
pfsense_destination_ip.ip,
destination_port,
previous_day_ml_check,
previous_week_ml_check,
combined_ml_check
FROM pfsense_logs
LEFT JOIN pfsense_real_interface ON pfsense_logs.real_interface = pfsense_real_interface.id
LEFT JOIN pfsense_reason ON pfsense_logs.reason = pfsense_reason.id
LEFT JOIN pfsense_act ON pfsense_logs.act = pfsense_act.id
LEFT JOIN pfsense_direction ON pfsense_logs.direction = pfsense_direction.id
LEFT JOIN pfsense_protocol ON pfsense_logs.protocol = pfsense_protocol.id
LEFT JOIN pfsense_ip AS pfsense_source_ip ON pfsense_logs.source_ip = pfsense_source_ip.id
LEFT JOIN pfsense_ip AS pfsense_destination_ip ON pfsense_logs.destination_ip = pfsense_destination_ip.id
WHERE pfsense_logs.pfsense_instance = {} AND record_time < '{}' AND record_time > '{}' AND combined_ml_check = -1
ORDER BY pfsense_logs.record_time DESC"""
    total_log_query = """SELECT COUNT(*) FROM pfsense_logs
    WHERE pfsense_logs.pfsense_instance = {} AND record_time < '{}' AND record_time > '{}' 
    ORDER BY pfsense_logs.record_time DESC"""
    for client in clients:
        df = create_logs_df()
        client_id = str(client[0])
        results = query_db(combined_error_query.format(client_id, now, target))
        total_errors = len(results)
        for row in results:
            df = append_logs_df(row, df)
        try:
            total_logs = int(query_db(total_log_query.format(client_id, now, target))[0][0])
            percent_error = int((total_errors / total_logs) * 100)
        except:
            total_logs = 0
            percent_error = 0
        final_results = final_results + [[client, df, percent_error, total_logs]]
    return(final_results)

def combined_errors_report_email(client, path, percent_error, log_count):
    recievers_query = """SELECT 
    reciever_name, 
    receiver_address 
    FROM combined_reports_recievers 
    WHERE instance_id = {}
    """
    recievers = query_db(recievers_query.format(str(client[0])))
    message = """Hi {},\n
Please see attached the daily report of combined machine learning errors for {}.\n
{} of the {} log entries stored today were flagged by the machine learning algorithm.\n
-PfSense Dashboard Reporting"""
    subject = "{} Combined Reports"
    for reciever in recievers:
        email_attachment(message.format(reciever[0], client[1], str(percent_error) + "%", str(log_count)), reciever[1], subject.format(client[1]), path)

def run_combined_errors_report():
    reports = combined_errors_report()
    for report_set in reports:
        client = report_set[0]
        df = report_set[1]
        percent_error = report_set[2]
        total_logs = report_set[3]
        path = os.path.join(reports_dir + "/" + client[1] + ".csv")
        df.to_csv(path, index=False)
        combined_errors_report_email(client, path, percent_error, total_logs)

def openvpn_usage_report():
    open_vpn_user_query = "SELECT id, user_name FROM vpn_user"
    last_logon_query = """SELECT record_time, pfsense_instance FROM open_vpn_access_log WHERE vpn_user = {} ORDER BY record_time DESC LIMIT 1"""
    instance_query = """SELECT pfsense_name FROM pfsense_instances WHERE id = {}"""
    open_vpn_users = query_db(open_vpn_user_query)
    now = datetime.datetime.now()
    day_plus_since_logon = []
    not_logged = 0
    logged = 0
    for open_vpn_user in open_vpn_users:
        last_logon, instance = query_db(last_logon_query.format(str(open_vpn_user[0])))[0]
        delta = now - last_logon
        if(delta.days > 1):
            not_logged = not_logged + 1
            instance_name = query_db(instance_query.format(str(instance)))[0][0]
            day_plus_since_logon = day_plus_since_logon + [[open_vpn_user[1], last_logon.strftime("%Y-%m-%d %H:%M:%S"), instance_name]]
        else:
            logged = logged + 1
    return(logged, not_logged, day_plus_since_logon)

def open_vpn_report_email(path, logged_in, not_logged_in):
    try:
        recievers_query = """SELECT 
        reciever_name, 
        reciever_address 
        FROM open_vpn_report_recievers 
        """
        recievers = query_db(recievers_query)
        message = """Hi {},\n
    {} users have logged in to the Open VPN server today, with {} users not having logged in for a day or more.\n
    Please see the CSV report attached of which users have not logged in for a day or more, and their last login date\n
    -PfSense Dashboard Reporting"""
        subject = "Daily OpenVPN Report"
        for reciever in recievers:
            email_attachment(message.format(reciever[0], str(logged_in), str(not_logged_in)), reciever[1], subject, path)
    except:
        pass

def run_open_vpn_usage_report():
    logged, not_logged, day_plus_since_logon = openvpn_usage_report()
    day_since_logon_df = create_open_vpn_login_df()
    for entry in day_plus_since_logon:
        day_since_logon_df = append_open_vpn_login_df(entry, day_since_logon_df)
    path = os.path.join(reports_dir + "/open_vpn_usage_report.csv")
    day_since_logon_df.to_csv(path, index=False)
    open_vpn_report_email(path, logged, not_logged)
    

#----------------------------------------------------
#MAIN LOOP
#----------------------------------------------------
loop = True
run_state = 0
while(loop == True):
    if(int(datetime.datetime.now().strftime("%H")) == int(os.environ["REPORTING_HOUR"])):
        if(run_state == 0):
            logging.warning("Running Combined Errors Reports")
            run_combined_errors_report()
            logging.warning("Running OpenVPN Usage Report")
            run_open_vpn_usage_report()
            run_state = 1
    elif(int(datetime.datetime.now().strftime("%H")) != int(os.environ["REPORTING_HOUR"]) and run_state == 1):
        run_state = 0
