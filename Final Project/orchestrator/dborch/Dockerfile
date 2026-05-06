FROM python:3-buster

COPY . /dborch
WORKDIR /dborch

RUN pip install -r requirements.txt
ENV TEAM_NAME=CC_1387_1595_1702_1898
CMD python3 db_orch.py