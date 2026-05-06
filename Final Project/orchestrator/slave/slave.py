#!/usr/bin/env python
import pika
import sys
import json
import sqlite3
import datetime
from sqlalchemy import create_engine,and_,Column,Integer,String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging
from kazoo.client import KazooClient

logging.basicConfig()
zk = KazooClient(hosts='zoo:2181')
zk.start()
zk.ensure_path("/slave")
zk.create("/slave/"+ str(random()),b"",ephemeral=True)

Base = declarative_base()

class User(Base):
    __tablename__ = "User"
    username = Column("username",String(50), primary_key=True)
    password = Column("password",String(50), primary_key=True)
class Rideshare(Base):
    __tablename__ = "Rideshare"
    rideid = Column("rideid",Integer, primary_key=True,autoincrement=True)
    created_by = Column("created_by",String(50))
    timestamp = Column("timestamp",String(50))
    source = Column("source",String(50))
    dest = Column("dest",String(50))
class Userride(Base):
   __tablename__ = "Userride"
   rid = Column("rid",Integer,primary_key=True)
   users = Column("users",String(50),primary_key=True)

engine = create_engine('sqlite:////app.db',echo=True)
Base.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine)
session = Session()
connection1 = pika.BlockingConnection(pika.ConnectionParameters(host='rmq'))
channel1 = connection1.channel()
channel1.exchange_declare(exchange='logs',exchange_type='fanout')
res = channel1.queue_declare(queue='', durable=True, exclusive=True)
channel1.queue_bind(exchange='logs',queue=res.method.queue)

def callback1(ch,method,props,body):
    response = wt(json.loads(body))
    ch.basic_publish(exchange='logs',routing_key='',body=body)
    ch.basic_publish(exchange='',routing_key=props.reply_to,properties=pika.BasicProperties(correlation_id = props.correlation_id),body=json.dumps(response))
    ch.basic_ack(delivery_tag = method.delivery_tag)

def callback3(ch,method,props,body):
    wt(json.loads(body))
    ch.basic_ack(delivery_tag = method.delivery_tag)

def wt(body):
    if body["api"] == "remove":
                session.delete(session.query(User).filter_by(username = body["column"]).one())
                session.commit()
                return 200
    if body["api"] == "add":
                session.add(User(username=body["username"],password=body["password"]))
                session.commit()
                return 200
    if body["api"] == "clear_db":
                meta = Base.metadata
                for table in reversed(meta.sorted_tables):
                        session.execute(table.delete())
                return 200
    if body["api"] == "delete":
        session.delete(session.query(Rideshare).filter_by(rideid = body["column"]).one())
        session.commit()
        return 200
    if body["api"] == "remove":
        session.delete(session.query(User).filter_by(username = body["column"]).one())
        session.commit()
        return 200
    if body["api"] == "addride":
        usn = body["created_by"]
        tmp = datetime.datetime.strptime(body["timestamp"],'%d-%m-%Y:%S-%M-%H')
        try:
            x = datetime.datetime(tmp.year,tmp.month,tmp.day,tmp.hour,tmp.minute,tmp.second)
        except:
            return 400
        src = body["source"]
        dest = body["destination"]
        session.add(Rideshare(created_by=usn,timestamp=body["timestamp"],source=src,dest=dest))
        session.commit()
        return 201
    if body["api"] == "join":
        try:
            rid=body["column1"]
            us=body["column2"]
            session.add(Userride(rid = rid,users= us))
            session.commit()
        except:
            return 400
        return 200
    if body["api"] == "add":
        session.add(User(username=body["username"],password=body["password"]))
        session.commit()
        return 200

def callback2(ch, method, props, body):
    response = rd(json.loads(body))
    ch.basic_publish(exchange='',routing_key=props.reply_to,properties=pika.BasicProperties(correlation_id = props.correlation_id),body=json.dumps(response))
    ch.basic_ack(delivery_tag = method.delivery_tag)


def rd(body):
        if body["api"] == "add":
                try:
                        u = session.query(User).filter_by(username = body["usn"]).one()
                except:
                        return 201
                return 400
        elif body["api"] == "addride":
                        s = False                                                                                                                                                               d = False
                        a = int(body["source"])
                        b = int(body["destination"])
                        if a>=0 and a<=199:
                           s = True      
                        if b>=0 and b<=199:
                           d = True      
                        if a == b:   
                           return 400    
                        if not(s and d):
                           return 400
                        return 200
        elif body["api"] == "remove":
                usn = body["column"]
                try:
                        u = session.query(User).filter_by(username = usn).one()
                except:
                        return 400
                return 200
        elif body["api"] == "list_users":
                try:
                        if not session.query(User).all():
                                return 204
                        else:
                                v = session.query(User).all()
                                l=[]
                                for i in v:
                                        l.append(i.username)
                                return l
                except:
                        return 400
        elif body["api"] == "delete":
                try:
                    u = session.query(Rideshare).filter_by(rideid = body["column"]).one()
                except:
                    return 400
                return 200
        elif body["api"] == "upcoming":
                l = []
                src = int(body["src"])
                dest = int(body["dest"])
                if src == 0 or dest == 0:
                   return jsonify({}),400
                s = False
                d = False
                if src >=0 and src<=199:
                   s = True
                if dest >=0 and dest<=199:
                   d = True                                                                                                                                                             if src == dest:                                                                                                                                                             return 400
                if not(s and d):
                   return 400
                try:
                    u = session.query(Rideshare).filter(and_(Rideshare.source == body["src"],Rideshare.dest == body["dest"])).all()
                    for i in u:
                            if datetime.datetime.strptime(i.timestamp,'%d-%m-%Y:%S-%M-%H') >= datetime.datetime.now():
                                d = {}
                                d["rideId"] = i.rideid
                                d["username"] = i.created_by
                                d["timestamp"] = i.timestamp
                                l.append(d)
                            else:
                                return 400
                    if l:
                        return l
                    return 204
                except:
                    return 204
        elif body["api"] == "list":
                rid = body["rideid"]
                try:
                    a = session.query(Rideshare).filter_by(rideid = rid).one()
                    dic={}
                    dic["rideId"]=a.rideid
                    dic["created_by"]=a.created_by
                    v = session.query(Userride).filter_by(rid = rid).all()
                    l = []
                    for i in v:
                        l.append(i.users)
                    dic["users"] = l
                    dic["timestamp"] = a.timestamp
                    dic["source"] = a.source
                    dic["destination"] = a.dest
                    return dic
                except:
                    return 204
        elif body["api"] == "join":
                try:
                    c1 = session.query(Rideshare).filter_by(rideid = body["column1"]).one()
                except:
                    return 400
                return 200
        elif body["api"]== "clear_db":
                if not (session.query(Rideshare).all() or session.query(Userride).all() or session.query(User).all()):
                    return 400
                else:
                    return 200
        elif body["api"]== "count":
                cnt = session.query(Rideshare).count()
                return cnt



def master():
  channel1.queue_declare(queue='writeQ',durable=True)
  channel1.basic_consume(queue='writeQ',on_message_callback=callback1)
  channel1.start_consuming()

def slave():
   channel1.queue_declare(queue='readQ', durable=True)
   channel1.basic_qos(prefetch_count=1)
   channel1.basic_consume(queue='readQ', on_message_callback=callback2)
   channel1.basic_consume(queue=res.method.queue,on_message_callback=callback3)
   channel1.start_consuming()


if(int(sys.argv[1])):
      master()
else:
      slave()