from flask import Flask,jsonify,request,Response
import re
import datetime
import sqlite3
from sqlalchemy.dialects.sqlite import TIMESTAMP
from requests import post,get
from sqlalchemy import and_,Column,Integer,String,DateTime
from  flask_sqlalchemy import SQLAlchemy
app = Flask(__name__)

c=0
@app.route('/api/v1/users',methods=["PUT"])
def add_user():
                global c
                c+=1
                data = request.get_json()
                if re.match(r'[a-fA-F0-9]{40}$',data["password"]):
                        r = post('http://52.202.194.159:80/api/v1/db/read',json={"api":"add","usn":data["username"]})
                        if r.status_code == 201:
                                data["api"] = "add"
                                r1=post('http://52.202.194.159:80/api/v1/db/write',json = data)
                                if(r1.status_code==200):
                                        return jsonify({}),201
                                else:
                                        return jsonify({}),400
                        else:
                                return jsonify({}),400
                else:

                        return jsonify({}),400

@app.route('/api/v1/users/<username>',methods = ["DELETE"])
def remove_user(username):
                global c
                c+=1
                r = post('http://52.202.194.159:80/api/v1/db/read',json = {"api":"remove","column":username})
                if r.status_code == 400:
                        return jsonify({}),400
                elif r.status_code == 200:
                        post('http://52.202.194.159:80/api/v1/db/write',json = {"api":"remove","column":username})
                        return jsonify({}),200
@app.route('/api/v1/users',methods=['GET'])
def list_all_users():
                global c
                c+=1
                r = post('http://52.202.194.159:80/api/v1/db/read',json ={"api":"list_users"})
                if r.status_code == 200:
                        return jsonify(r.json()),200
                elif r.status_code == 204:
                        return jsonify({}),204
                else:
                        return jsonify({}),400

@app.errorhandler(405)
def handle(e):
    global c
    c+=1
    post('http://52.202.194.159:80/api/v1/db/read',json = {})
    return jsonify({}),405

@app.route('/api/v1/_count',methods = ["GET"])
def count_req():
        return jsonify([c]),200

@app.route('/api/v1/_count',methods = ["DELETE"])
def reset_count():
        global c
        c=0
        return Response(status=200)

if __name__ == '__main__':
        app.run(debug=True,host="0.0.0.0",port="80")