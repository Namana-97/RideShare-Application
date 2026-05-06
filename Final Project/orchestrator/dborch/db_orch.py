from flask import Flask,jsonify,Response,request
import pika
import uuid
import json
from docker import APIClient,from_env
import os
from random import choice
from threading import Timer
import logging
from kazoo.client import KazooClient
from requests import post
app = Flask(__name__)

c=0
f=0

logging.basicConfig()
zk = KazooClient(hosts='zoo:2181')
zk.start()
zk.ensure_path("/slave")

def demo_func(event):
    from_env().containers.run(image=from_env().containers.get('ubuntu_master_1').commit(),command=["python","master.py","0"],network = 'ubuntu_default',links = {'ubuntu_rmq_1':'ubuntu_rmq_1','ubuntu_zoo_1':'ubuntu_zoo_1'},restart_policy={"Name":"on-failure"},detach=True)

def scale():
        global c
        if c:
          s = c//20 + 1 if c%20 else c//20
        else:
          s = 1
        conrlst = from_env().containers.list()
        conrlst.remove(from_env().containers.get("ubuntu_master_1"))
        conrlst.remove(from_env().containers.get("ubuntu_rmq_1"))
        conrlst.remove(from_env().containers.get("ubuntu_zoo_1"))
        conrlst.remove(from_env().containers.get("dborch"))
        n = len(conrlst)
        if s > n:
           img  = from_env().containers.get(choice(conrlst).name).commit()
           for i in range(s-n):
                from_env().containers.run(image=img,command=["python","slave.py","0"],network = 'ubuntu_default',links = {'ubuntu_rmq_1':'ubuntu_rmq_1'},restart_policy={"Name":"on-failure"},detach=True)
        else:
           for i in range(n-s):
                conr = choice(conrlst)
                conrlst.remove(conr)
                conr.kill()
        c=0
        Timer(120.0,scale).start()


class Client(object):
    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='rmq'))
        self.channel = self.connection.channel()
        result = self.channel.queue_declare(queue='responseQ',durable=True)
        self.callback_queue = result.method.queue
        self.channel.basic_consume(queue=self.callback_queue,on_message_callback=self.on_response,auto_ack=True)

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self, queue):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        if queue == 'writeQ':
            self.channel.basic_publish(exchange='',routing_key=queue,properties=pika.BasicProperties(reply_to=self.callback_queue,correlation_id=self.corr_id,),body=json.dumps(request.get_json()))
        else:
            self.channel.basic_publish(exchange='',routing_key=queue,properties=pika.BasicProperties(reply_to=self.callback_queue,correlation_id=self.corr_id,delivery_mode=2,),body=json.dumps(request.get_json()))
        while self.response is None:
            self.connection.process_data_events()
        self.connection.close()
        return json.loads(self.response)


@app.route('/api/v1/db/read',methods = ["POST"])
def read():
    global c
    c+=1
    if f == 0:
        Timer(120.0,scale).start()
        f=1
    if not request.get_json():
       return Response(status=405)
    cli = Client()
    r = cli.call('readQ')
    if r == 200:
       return Response(status=200)
    if r == 201:
       return Response(status=201)
    if r == 204:
       return Response(status=204)
    if r == 400:
       return Response(status=400)
    return jsonify(r)

@app.route('/api/v1/db/write',methods = ["POST"])
def write():
    cli = Client()
    r = cli.call('writeQ')
    if r == 200:
       return Response(status=200)
    if r == 201:
       return Response(status=201)
    if r == 204:
       return Response(status=204)
    if r == 400:
       return Response(status=400)
    return jsonify(r)

@app.route('/api/v1/db/clear',methods=['POST'])
def clear_db():
                r=post('http://0.0.0.0:80/api/v1/db/read',json = {"api":"clear_db"})
                if r.status_code == 200:
                        r1 = post('http://0.0.0.0:80/api/v1/db/write',json = {"api":"clear_db"}) 
                        if r1.status_code == 200:
                                return jsonify({}),200
                        return jsonify({}),400
                else:      
                        return jsonify({}),200 

@app.route('/api/v1/crash/master',methods=["POST"])
def master():
        pid = APIClient().inspect_container("ubuntu_master_1")["State"]["Pid"]
        from_env().containers.get("ubuntu_master_1").kill()
        return jsonify([pid]),200

@app.route('/api/v1/crash/slave',methods=["POST"])
def slave():
        conrlst = from_env().containers.list()
        l = list(map(lambda conr:APIClient().inspect_container(conr.name)["State"]["Pid"],from_env().containers.list()))
        l.remove(APIClient().inspect_container("ubuntu_master_1")["State"]["Pid"])
        l.remove(APIClient().inspect_container("ubuntu_rmq_1")["State"]["Pid"])
        l.remove(APIClient().inspect_container("ubuntu_zoo_1")["State"]["Pid"])
        l.remove(APIClient().inspect_container("dborch")["State"]["Pid"])
        m = max(l)
        for conr in conrlst:
           if m == APIClient().inspect_container(conr.name)["State"]["Pid"]:
              from_env().containers.list().remove(conr)
              conr.kill()
              zk.get_children("/slave/",watch=demo_func)
              break
        return jsonify([m]),200

@app.route('/api/v1/worker/list',methods=["GET"])
def worklist():
        l = sorted(list(map(lambda conr:APIClient().inspect_container(conr.name)["State"]["Pid"],from_env().containers.list())))
        l.remove(APIClient().inspect_container("dborch")["State"]["Pid"])
        l.remove(APIClient().inspect_container("ubuntu_rmq_1")["State"]["Pid"])
        l.remove(APIClient().inspect_container("ubuntu_zoo_1")["State"]["Pid"])
        return jsonify(l),200


if __name__ == '__main__':
        app.run(debug=True,host="0.0.0.0",port="80")