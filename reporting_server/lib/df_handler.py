import pandas as pd

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