#----------------------------------------------------
#INITIALISATION
#----------------------------------------------------
import os
import datetime
import logging
import time

from reporting_server.lib import db_handler, email_handler, df_handler

logging.warning("Program Started")

reports_dir = "/var/reports"

#----------------------------------------------------
#PRIMARY FUNCTIONS
#----------------------------------------------------
def combined_errors_report():
    final_results = []
    clients = db_handler.return_clients()
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
        df = df_handler.create_logs_df()
        client_id = str(client[0])
        results = db_handler.query_db(combined_error_query.format(client_id, now, target))
        total_errors = len(results)
        for row in results:
            df = df_handler.append_logs_df(row, df)
        try:
            total_logs = int(db_handler.query_db(total_log_query.format(client_id, now, target))[0][0])
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
    recievers = db_handler.query_db(recievers_query.format(str(client[0])))
    message = """Hi {},\n
Please see attached the daily report of combined machine learning errors for {}.\n
{} of the {} log entries stored today were flagged by the machine learning algorithm.\n
-PfSense Dashboard Reporting"""
    subject = "{} Combined Reports"
    for reciever in recievers:
        email_handler.email_attachment(message.format(reciever[0], client[1], str(percent_error) + "%", str(log_count)), reciever[1], subject.format(client[1]), path)

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
    open_vpn_users = db_handler.query_db(open_vpn_user_query)
    now = datetime.datetime.now()
    day_plus_since_logon = []
    not_logged = 0
    logged = 0
    for open_vpn_user in open_vpn_users:
        try:
            last_logon, instance = db_handler.query_db(last_logon_query.format(str(open_vpn_user[0])))[0]
            delta = now - last_logon
            if(delta.days > 1):
                not_logged = not_logged + 1
                instance_name = db_handler.query_db(instance_query.format(str(instance)))[0][0]
                day_plus_since_logon = day_plus_since_logon + [[open_vpn_user[1], last_logon.strftime("%Y-%m-%d %H:%M:%S"), instance_name]]
            else:
                logged = logged + 1
        except:
            pass
    return(logged, not_logged, day_plus_since_logon)

def open_vpn_report_email(path, logged_in, not_logged_in):
    try:
        recievers_query = """SELECT 
        reciever_name, 
        reciever_address 
        FROM open_vpn_report_recievers 
        """
        recievers = db_handler.query_db(recievers_query)
        message = """Hi {},\n
    {} users have logged in to the Open VPN server today, with {} users not having logged in for a day or more.\n
    Please see the CSV report attached of which users have not logged in for a day or more, and their last login date\n
    -PfSense Dashboard Reporting"""
        subject = "Daily OpenVPN Report"
        for reciever in recievers:
            email_handler.email_attachment(message.format(reciever[0], str(logged_in), str(not_logged_in)), reciever[1], subject, path)
    except:
        pass

def run_open_vpn_usage_report():
    try:
        logged, not_logged, day_plus_since_logon = openvpn_usage_report()
        day_since_logon_df = df_handler.create_open_vpn_login_df()
        for entry in day_plus_since_logon:
            day_since_logon_df = df_handler.append_open_vpn_login_df(entry, day_since_logon_df)
        path = os.path.join(reports_dir + "/open_vpn_usage_report.csv")
        day_since_logon_df.to_csv(path, index=False)
        open_vpn_report_email(path, logged, not_logged)
    except:
        pass
    

#----------------------------------------------------
#MAIN LOOP
#----------------------------------------------------
def main():
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

if __name__ == '__main__':
    main()
