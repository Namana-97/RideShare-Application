from flask import Flask,jsonify,request,Response,make_response
import re
import datetime
import sqlite3
from requests import post,get
from enum import Enum
from sqlalchemy import and_,Column,Integer,String,DateTime
from  flask_sqlalchemy import SQLAlchemy
from flask_cors import cross_origin
app = Flask(__name__)


c=0


@app.route('/api/v1/rides',methods = ["GET"])
@cross_origin(origin = "3.212.76.185")
def list_all_upcoming_rides():
        global c
        c+=1
        r = post('http://52.202.194.159:80/api/v1/db/read',json = {"api":"upcoming","src":request.args.get('source'),"dest":request.args.get('destination')})
        if r.status_code == 204:
            return Response(status=204)
        elif r.status_code == 200:
            return r.text
        elif r.status_code == 400:
            return jsonify({}),400

@app.route('/api/v1/rides/<rideId>',methods = ["DELETE"])
def delete_ride(rideId):
        global c
        c+=1
        r = post('http://52.202.194.159:80/api/v1/db/read',json = {"api":"delete","column":rideId})
        if r.status_code == 200:
            post('http://52.202.194.159:80/api/v1/db/write',json = {"api":"delete","column":rideId})
            return jsonify({}),200
        else:
            return jsonify({}),400


@app.route('/api/v1/rides',methods=["POST"])
@cross_origin(origin = "3.212.76.185")
def add_ride():
        global c
        c+=1
        r = post('http://52.202.194.159:80/api/v1/db/read',json = data)
        if r.status_code == 400:
            return jsonify({}),400
        username = request.get_json()["created_by"]
        name = get("http://CCBD-721298633.us-east-1.elb.amazonaws.com/api/v1/users")
        if name.text == "0":
            return jsonify({}),400
        if username in name.text:
            s = post('http://52.202.194.159:80/api/v1/db/write',json = data)
            if s.status_code == 201:
                    return jsonify({}),201
            else:
                    return jsonify({}),400
        else:
            return jsonify({}),400

@app.route('/api/v1/rides/<rideId>',methods = ["GET"])
def list_all_the_details(rideId):
        global c
        c+=1
        r = post('http://52.202.194.159:80/api/v1/db/read',json ={"api":"list","rideid":rideId})
        if r.status_code == 200:
            return jsonify(r.json()),200
        else:
            return jsonify({}),204

@app.route('/api/v1/rides/<rideId>', methods=['POST'])
@cross_origin(origin = "3.212.76.185")
def joinride(rideId):
        global c
        c+=1
        username = request.get_json()["username"]
        name = get("http://CCBD-721298633.us-east-1.elb.amazonaws.com/api/v1/users")
        if name.text == "0":
            return jsonify({}),400
        if request.get_json()["username"] not in name.text:
            return jsonify({}),400
        if datetime.datetime.strptime(c1.timestamp,'%d-%m-%Y:%S-%M-%H') < datetime.datetime.now():
            return jsonify({}),400
        r=post('http://52.202.194.159:80/api/v1/db/read',json = {"api":"join","column1":rideId,"column2":username})
        if r.status_code == 200:
                r1 = post('http://52.202.194.159:80/api/v1/db/write',json = {"api":"join","column1":rideId,"column2":username})
                if r1.status_code == 200:
                       return Response(status=200)
                return Response(status=400)
        else:
                return Response(status=400)

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

@app.route('/api/v1/rides/count',methods=["GET"])
def ridecount():
   global c
   c+=1
   r = post('http://52.202.194.159:80/api/v1/db/read',json={"api":"count"})
   return jsonify([int(r.text)]),200

if __name__ == '__main__':
    app.run(debug=True,host="0.0.0.0",port="80")