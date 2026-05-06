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

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)
class Rideshare(db.Model):
    __tablename__ = 'rideshare'
    rideid = db.Column(db.Integer, primary_key=True,autoincrement=True)
    created_by = db.Column(db.String(50))
    timestamp = db.Column(db.String(50))
    source = db.Column(db.String(50))
    dest = db.Column(db.String(50))
class Userride(db.Model):
   __tablename__ = "user_ride"
   rid = db.Column(db.Integer,primary_key=True)
   users = db.Column(db.String(50),primary_key=True)
db.session.commit()
c=0

@app.route('/api/v1/db/read',methods = ["POST"])
def read():
    if request.get_json()["api"] == "delete":
        try:
            u = Rideshare.query.filter_by(rideid = request.get_json()["column"]).one()
        except:
            return jsonify({}),400
        return jsonify({}),200
    elif request.get_json()["api"] == "upcoming":
        l = []
        try:
            u = Rideshare.query.filter(and_(Rideshare.source == request.get_json()["src"],Rideshare.dest == request.get_json()["dest"])).all()
            for i in u:
                    if datetime.datetime.strptime(i.timestamp,'%d-%m-%Y:%S-%M-%H') >= datetime.datetime.now():
                        d = {}
                        d["rideId"] = i.rideid
                        d["username"] = i.created_by
                        d["timestamp"] = i.timestamp
                        l.append(d)
                    else:
                        return Response(status=400)
            if l:
                return jsonify(l),200
            return Response(status=204)
        except:
            return Response(status=204)
    elif request.get_json()["api"] == "list":
        rid = request.get_json()["rideid"]
        try:
            a = Rideshare.query.filter_by(rideid = rid).one()
            dic={}
            dic["rideId"]=a.rideid
            dic["created_by"]=a.created_by
            v = Userride.query.filter_by(rid = rid).all()
            l = []

            for i in v:
                l.append(i.users)
            dic["users"] = l
            dic["timestamp"] = a.timestamp
            dic["source"] = a.source
            dic["destination"] = a.dest
            return jsonify(dic),200
        except:
            return jsonify({}),204
    elif request.get_json()["api"] == "join":
        try:
            c1 = Rideshare.query.filter_by(rideid = request.get_json()["column1"]).one()
        except:
            return jsonify({}),400
        return jsonify({}),200
    elif request.get_json()["api"]== "clear_db":
        if not (Rideshare.query.all() or Userride.query.all()):
            return jsonify({}),400
        else:
            return jsonify({}),200
    elif request.get_json()["api"]== "count":
        cnt = Rideshare.query.count()
        return jsonify(cnt),200

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

@app.route('/api/v1/rides',methods = ["GET"])
@cross_origin(origin = "54.243.2.210")
def list_all_upcoming_rides():
        global c
        c+=1
        src = int(request.args.get('source'))
        dest = int(request.args.get('destination'))
        if src == 0 or dest == 0:
            return jsonify({}),400
        s = False
        d = False
        if src >=0 and src<=199:
            s = True
        if dest >=0 and dest<=199:
            d = True
        if src == dest:
            return jsonify({}),400
        if not(s and d):
            return jsonify({}),400
        r = post('http://0.0.0.0:80/api/v1/db/read',json = {"api":"upcoming","src":str(src),"dest":str(dest)})
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
        r = post('http://0.0.0.0:80/api/v1/db/read',json = {"api":"delete","column":rideId})
        if r.status_code == 200:
            post('http://0.0.0.0:80/api/v1/db/write',json = {"api":"delete","column":rideId})
            return jsonify({}),200
        else:
            return jsonify({}),400

@app.route('/api/v1/db/write',methods = ["POST"])
def write():
    if request.get_json()["api"] == "delete":
        db.session.delete(Rideshare.query.filter_by(rideid = request.get_json()["column"]).one())
        db.session.commit()
        return jsonify({}),200
    if request.get_json()["api"] == "remove":
        db.session.delete(User.query.filter_by(username = request.get_json()["column"]).one())
        db.session.commit()
        return jsonify({}),200
    if request.get_json()["api"] == "addride":
        usn = request.get_json()["created_by"]
        tmp = datetime.datetime.strptime(request.get_json()["timestamp"],'%d-%m-%Y:%S-%M-%H')
        try:
            x = datetime.datetime(tmp.year,tmp.month,tmp.day,tmp.hour,tmp.minute,tmp.second)
        except:
            return jsonify({}),400
        src = request.get_json()["source"]
        dest = request.get_json()["destination"]
        db.session.add(Rideshare(created_by=usn,timestamp=request.get_json()["timestamp"],source=src,dest=dest))
        db.session.commit()
        return jsonify({}),201
    if request.get_json()["api"] == "join":
        try:
            rid=request.get_json()["column1"]
            us=request.get_json()["column2"]
            db.session.add(Userride(rid = rid,users= us))
            db.session.commit()
        except:
            return jsonify({}),400
        return jsonify({}),200
    if request.get_json()["api"] == "add":
        db.session.add(User(username=request.get_json()["username"],password=request.get_json()["password"]))
        db.session.commit()
        return jsonify({}),200
    if request.get_json()["api"] == "clear_db":
        meta = db.metadata
        for table in reversed(meta.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()
        return jsonify({}),200

@app.route('/api/v1/rides',methods=["POST"])
@cross_origin(origin = "54.243.2.210")
def add_ride():
        global c
        c+=1
        data=request.get_json()
        data["api"]="addride"
        s = False
        d = False
        a = int(data["source"])
        b = int(data["destination"])
        if a>=0 and a<=199:
            s = True
        if b>=0 and b<=199:
            d = True
        if a == b:
            return jsonify({}),400
        if not(s and d) :
            return jsonify({}),400
        username = request.get_json()["created_by"]
        name = get("http://CC3-1355526159.us-east-1.elb.amazonaws.com/api/v1/users")
        if name.text == "0":
            return jsonify({}),400
        if username in name.text:
            s = post('http://0.0.0.0:80/api/v1/db/write',json = data)
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
        r = post('http://0.0.0.0:80/api/v1/db/read',json ={"api":"list","rideid":rideId})
        if r.status_code == 200:
            return jsonify(r.json()),200
        else:
            return jsonify({}),204

@app.route('/api/v1/rides/<rideId>', methods=['POST'])
@cross_origin(origin = "54.243.2.210")
def joinride(rideId):
        global c
        c+=1
        username = request.get_json()["username"]
        name = get("http://CC3-1355526159.us-east-1.elb.amazonaws.com/api/v1/users")
        if name.text == "0":
            return jsonify({}),400
        if request.get_json()["username"] not in name.text:
            return jsonify({}),400
        if datetime.datetime.strptime(c1.timestamp,'%d-%m-%Y:%S-%M-%H') < datetime.datetime.now():
            return jsonify({}),400
        r=post('http://0.0.0.0:80/api/v1/db/read',json = {"api":"join","column1":rideId,"column2":username})
        if r.status_code == 200:
                r1 = post('http://0.0.0.0:80/api/v1/db/write',json = {"api":"join","column1":rideId,"column2":username})
                if r1.status_code == 200:
                       return Response(status=200)
                return Response(status=400)
        else:
                return Response(status=400)

@app.errorhandler(405)
def handle(e):
    global c
    c+=1
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
   r = post('http://0.0.0.0:80/api/v1/db/read',json={"api":"count"})
   return jsonify([int(r.text)]),200

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True,host="0.0.0.0",port="80")