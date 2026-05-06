FROM python:3-buster

COPY . /slave
WORKDIR /slave

RUN pip install -r requirements.txt
ENV TEAM_NAME=CC_1387_1595_1702_1898
CMD python3 slave.py 0