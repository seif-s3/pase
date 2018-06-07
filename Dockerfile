FROM ubuntu:latest

MAINTAINER Seif Sameh "s3.seif@gmail.com"

RUN apt-get update -y
RUN apt-get install -y python-pip python-dev build-essential

COPY ./requirements.txt /pase-fuoracle/
COPY ./app /pase-fuoracle
WORKDIR /pase-fuoracle

RUN pip install -r requirements.txt

CMD ["gunicorn", "--workers=2", "--bind=0.0.0.0:8000", "app:app"]