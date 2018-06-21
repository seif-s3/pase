FROM ubuntu:latest

MAINTAINER Seif Sameh "s3.seif@gmail.com"

RUN apt-get update -y
RUN apt-get install -y python-pip python-dev build-essential

COPY ./requirements.txt /app/
COPY ./datasets /datasets
COPY ./src /app
WORKDIR /app

RUN pip install -r requirements.txt

CMD ["/bin/sh", "run_server.sh"]
