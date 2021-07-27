# PfSense_Dashboard-Reporting_Server

Email reporting server component of the PfSense Monitoring dashboard, formatted as a docker container it interacts with the underlying database for the PfSense dashboard and sends presets reports to selected users at a preset interval  
  
## ENV Variables  
DB_IP = IP that MySQL is accessible on  
DB_USER = User credential for DB access  
DB_PASS = Password for DB access  
DB_SCHEMA = Name of target Schema in DB  
DB_PORT = Port that DB is accessible on  
SEND_ADDRESS = Email address reports are to be sent from
SEND_PASSWORD = Password for SMTP access to this email account
SMTP_ADDRESS = Address for SMTP access to the reporting email account
SMTP_PORT = Specific port for SMTP requests to the above address
REPORTING_HOUR = Hour in 24hr format at which daily reports should be run (i.e 9 or 21)

## Container Volumes
The container will need a volume attached to it to store the csv exports included in reports mapped to /var/reports.
  
## Network Requirements
Container needs to be able to access the underlying database for the PfSense dashboard, and the SMTP address of the report sending address.
  
## Client Configuration
User details for those who are to be sent specific reports are set in the underlying database, or via the dashboard frontend
