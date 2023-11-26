FROM alpine:latest

RUN apk update

RUN apk add python3

RUN apk add py-pip

COPY ./requirements.txt /requirements.txt

COPY ./setup.py /setup.py

COPY . /

WORKDIR /

RUN python3 setup.py install

ENV SEND_ADDRESS = "Placeholder"

ENV SEND_PASSWORD = "Placeholder"

ENV SMTP_ADDRESS = "Placeholder"

ENV SMTP_PORT = "Placeholder"

ENV DB_IP = "Placeholder"

ENV DB_USER = "Placeholder"

ENV DB_PASS = "Placeholder"

ENV DB_SCHEMA = "Placeholder"

ENV DB_PORT = "Placeholder"

CMD [ "PfSense_Dashboard-Data_Reporting_Server" ]