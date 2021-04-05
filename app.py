from flask import Flask, jsonify, request, render_template
from datetime import date, datetime
import re, os
from flask.helpers import send_file, send_from_directory
from flask_restful import Resource, Api
from pymongo import MongoClient
import base64


app = Flask(__name__)
app.config['DEBUG']= True
api = Api(app)

client=MongoClient("mongodb+srv://pulse-squad:pulse-squad@pulse.dlply.mongodb.net/Project1?retryWrites=true&w=majority")
db=client.Project1
users=db['Users']

# USER defined functions for insertion and deletions from mongodb  #

def add(item):
    name=item['username']
    password=item['password']
    if name==None:
        return False
    if password==None:
        return False

    user=users.find_one({'username':name})
    if user==None:
        password=base64.standard_b64encode(str.encode(item['password']))
        item['password']=password
        users.insert_one(item)
        return True
    else:
        print(user)
        return False

def login_check(item):
    name,password=item['username'],item['password']
    if name==None or password == None:
        return False
    user=users.find_one({"username":name})
    if user==None:
        return False
    else:
        if user['password']==base64.standard_b64encode(str.encode(item['password'])):
            return True
        else:
            return False

'''                           *********************                             '''


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/home/<name>',methods=['GET'])
def hel(name):
    now=datetime.now()
    formatted_now=now.strftime("%A, %d %B, %Y at %X")
    mat=re.match("[a-zA-Z]+",name)
    if mat:
        clean_name=mat.group(0)
    else:
        clean_name="Friend"
    content="hello there "+clean_name+"! Server Time is  "+ formatted_now
    ret={'Name':content}
    return jsonify(ret)

@app.route('/home/user/newuser', methods=['POST'])
def checkuser():
    content=request.get_json()
    print(content)
    if add(content):
        return jsonify({'Message':'Request Received User Added ','status':200})
    else:
        return jsonify ({'Message':"Cannot add User , Already  A user or Credentials Entered Are Wrong",'status':300})


@app.route('/home/user/login',methods=['GET','POST'])
def logincheck():
    content=request.get_json()
    print(content)
    if login_check(content):
        return jsonify({'Message':'User confirmed ','status':200})
    else:
        return jsonify ({'Message':"Cannot identify User , Username or Password Don't Match",'status':300})

if __name__=="__main__":
    app.run(debug=True)
