from collections import defaultdict
from flask import Flask, jsonify, request, render_template
from datetime import date, datetime
import re, os,sys
from pymongo import MongoClient
from ML.clusters import other_possible_symptoms
from ML.classification_algo import calc_prob
import base64
sys.path.append(os.path.join(sys.path[0]+'/ML'))
from flask_cors import CORS,cross_origin

app = Flask(__name__)
app.config['DEBUG']= True
app.config['CORS_HEADERS'] = 'Content-Type'
CORS(app, resources=r'/api/*')

client=MongoClient("mongodb+srv://pulse-squad:pulse-squad@pulse.dlply.mongodb.net/Project1?retryWrites=true&w=majority")
db=client.Project1
users=db['Users']
hospitals=db['Hospitals']
doctors=db['Doctors']


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
@cross_origin()
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


#      ********************************************* subiasis IOT ******************************************************************************#
@app.route('/home/extra/dravail',methods=['POST'])
def Available():
    content=request.get_json()
   
    hosp_id=content['hospital_id']
    rf_id=content['rfid_tag']
    if hosp_id==None:
        return jsonify({'status':300,"Message":" NO Data Packet Recived"})
    return jsonify({'status':200,"Message":"Data Packet Recived"})

current_users=defaultdict(list)
# *************************************************************** Examine Protocols ***************************************************************#
@app.route('/home/user/Examine',methods=['POST'])
@cross_origin(origin='localhost',headers=['Content- Type','Authorization'])
def Examine():
    
    content=request.get_json()
    
    user=content['username']
    content.pop('username')
    print(content)
    print(current_users)
    if current_users.get(user,None)==None:
        current_users[user]=[[],[],[],False]
        # cureent_user[user][0] -> symtoms input total
        # cureent_user[user][1] -> Possible symtoms given
        # cureent_user[user][2] -> Main symtoms given
        #cureent_user[user][3] -> Questions symtoms given
        if len(content['symptoms'])<2:return jsonify({"status":300,"Message":"Provide a Minimum of 2 sysmptoms","content":current_users})
        symptoms=content['symptoms']
        current_users[user][0].extend(symptoms)
        current_users[user][1]=other_possible_symptoms(symptoms)
        current_users[user][2].extend(symptoms)
        ret_json={"status":200,"symptoms":[]}
        for x in current_users[user][1][:5]:
            ret_json["symptoms"].append(x)
        current_users[user][1]=current_users[user][1][5:]
        return jsonify(ret_json)
    else:
        if len(current_users[user][1])>10:
            current_users[user][0].extend(content['symptoms'])
            ret_json={"status":200,"symptoms":[]}
            for x in current_users[user][1][:5]:
                ret_json["symptoms"].append(x)
            current_users[user][1]=current_users[user][1][5:]
            return jsonify(ret_json)
        else:
            if current_users[user][3]==False:
                current_users[user][2].extend(current_users[user][0])
                current_users[user][3]=True
                current_users[user][0] = list(set(current_users[user][1]) & set(other_possible_symptoms(current_users[user][0])))
                if current_users[user][1]:
                    ret_json={"status":200,"symptoms":[current_users[user][1][0]]}
                    return ret_json
            else:
                
                if len(content['symptoms'])==1:
                    current_users[user][2].extend(content['symptoms'])
                    current_users[user][1] = list(set(current_users[user][1]) & set(other_possible_symptoms([current_users[user][1].pop(0)])))
                else:
                    current_users[user][1].pop(0)
                if current_users[user][1]:
                    ret_json={"status":200,"symptoms":[current_users[user][1][0]]}
                    return ret_json
            ret_json={}
            predicted_diseases, probabilities = calc_prob(current_users[user][2])
            print(predicted_diseases, probabilities)
            ret_json={'predicted_diseases':predicted_diseases.tolist(),'probabilities':probabilities.tolist(),'status':200}
            current_users.pop(user)
            return jsonify(ret_json)


# @app.route('/home/user/Examine/Ques',methods=['POST'])
# @cross_origin()
# def Question():
#     content=request.get_json()
#     user=content['username']
#     content.pop('username')
#     # Answer of the Question return is nessasary 

#     answer=content['answer']
    # if answer== True:
    #     current_users[user][2].append(current_users[user][1][0])
    #     current_users[user][1] = list(set(current_users[user][1]) & set(other_possible_symptoms([current_users[user][1].pop(0)])))
    # else:
    #     current_users[user][1].pop(0)
#     return jsonify({"status":200,"Message":"Query was Successful","Type":"Question_Answer"})


# *************************************************************** Examine Protocols ***************************************************************#
if __name__=="__main__":
    app.run()
