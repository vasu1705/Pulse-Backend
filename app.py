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
from bson.objectid import ObjectId



app = Flask(__name__)
app.config['DEBUG']= True
app.config['CORS_HEADERS'] = 'Content-Type'
CORS(app, resources=r'/api/*')

client=MongoClient("mongodb+srv://pulse-squad:pulse-squad@pulse.dlply.mongodb.net/Project1?retryWrites=true&w=majority")
db=client.Project1
users=db['Users']
hospitals=db['Hospitals']
doctors=db['Doctors']
Cache=db['Cache']
pharmacy=db['Pharmacy']


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
@app.route('/home/extra/dravail',methods=['POST',"GET"])
@cross_origin(origin='localhost',headers=['Content- Type','Authorization'])
def Available():
    content=request.get_json()
    if content==None:
        return jsonify({'status':300,"Message":" NO Data Packet Recived"})
    hosp_id=content['doctor_id']
    print(hosp_id)
    rf_id=content['rfid_tag']
    z=doctors.find_one({"Dr_id":hosp_id})["status"]
    z="True" if z=="False" else "False"
    doctors.find_one_and_update({"Dr_id":hosp_id},{"$set":{"status":z}})
    if hosp_id==None:
        return jsonify({'status':300,"Message":" NO Data Packet Recived"})
    return jsonify({'status':200,"Message":"Data Packet Recived"})


# *************************************************************** Examine Protocols Prdictions  ***************************************************************#
import pandas as pd
pred_desc=pd.read_csv('symptom_description.csv',index_col='Disease')
pre_pre=pd.read_csv('symptom_precaution.csv',index_col='Disease')   

global current_users
current_users=defaultdict(list)
@app.route('/home/user/Examine',methods=['POST'])
@cross_origin(origin='localhost',headers=['Content- Type','Authorization'])

def Examine():
    
    content=request.get_json()
    if Cache.find_one({'cache':"current_users"})!=None:
        print("Cache found")
        current_users=Cache.find_one({'cache':"current_users"})['data']
        if len(current_users)==0:
             current_users=defaultdict(list)
    else:
        current_users=defaultdict(list)
    user=content['username']
    content.pop('username')
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
        if Cache.find_one({'cache':"current_users"})==None:
            Cache.insert_one({"cache":"current_users","data":current_users})
        else:
            Cache.update_one({"cache":"current_users"},{ "$set": { "data": current_users  }})

        return jsonify(ret_json)
    else:
        if len(current_users[user][1])>10:
            current_users[user][0].extend(content['symptoms'])
            ret_json={"status":200,"symptoms":[]}
            for x in current_users[user][1][:5]:
                ret_json["symptoms"].append(x)
            current_users[user][1]=current_users[user][1][5:]
            Cache.update_one({"cache":"current_users"},{ "$set": { "data": current_users  }})

            return jsonify(ret_json)
        else:
            if current_users[user][3]==False:
                current_users[user][2].extend(current_users[user][0])
                current_users[user][3]=True
                current_users[user][0] = list(set(current_users[user][1]) & set(other_possible_symptoms(current_users[user][0])))
                if current_users[user][1]:
                    ret_json={"status":200,"symptoms":[current_users[user][1][0]]}
                    Cache.update_one({"cache":"current_users"},{ "$set": { "data": current_users  }})

                    return ret_json
            else:
                
                if len(content['symptoms'])==1:
                    current_users[user][2].extend(content['symptoms'])
                    current_users[user][1] = list(set(current_users[user][1]) & set(other_possible_symptoms([current_users[user][1].pop(0)])))
                else:
                    current_users[user][1].pop(0)
                if current_users[user][1]:
                    ret_json={"status":200,"symptoms":[current_users[user][1][0]]}
                    Cache.update_one({"cache":"current_users"},{ "$set": { "data": current_users  }})
                    return ret_json
            ret_json={}
            predicted_diseases, probabilities = calc_prob(current_users[user][2])
            print(predicted_diseases, probabilities)

            ret_json={'predicted_diseases':predicted_diseases.tolist(),'probabilities':probabilities.tolist(),'status':200}
            ret_json['description']=(pred_desc.loc[predicted_diseases[0]]).tolist()
            ret_json['description']=ret_json['description'][0]
            ret_json['precautions']=(pre_pre.loc[predicted_diseases[0]]).tolist()
            current_users.pop(user)
            Cache.update_one({"cache":"current_users"},{ "$set": { "data": current_users  }})
            return jsonify(ret_json)



# *************************************************************** Examine Protocols ***************************************************************#
# ****************************                  **************** CRUD  Protocols *****************                            *********************#


@app.route('/home/user/hospitals',methods=["POST","GET"])
@cross_origin(origin='localhost',headers=['Content- Type','Authorization'])
def find_hospitals():
    import requests
    url1 = "https://trueway-matrix.p.rapidapi.com/CalculateDrivingMatrix"

    querystring = {"origins":"23.237696056902493, 77.40107993996217;","destinations":"23.231859715443527, 77.43622760832372;23.229375249406406, 77.43442516379237"}

    headers = {
        'x-rapidapi-key': "327f8a6b06msh8f77c136d8ca000p1f6dbajsn966200f786c5",
        'x-rapidapi-host': "trueway-matrix.p.rapidapi.com"
        }
    # response = requests.request("GET", url1, headers=headers, params=querystring)

    # print(response.text)
    content=request.get_json()
    
    speciality=None
    if content==None:
        data=list(hospitals.find({},{'_id':0}))
        for j in range(len(data)):
            data[j].pop("Hpt_cost")
            data[j].pop("Hpt_doctors")
        return jsonify({"hospitals":data,"status":200})

    elif content.get('speciality',None)!=None :
        i=0
        if content.get('origins',None)!=None:
            querystring["origins"]=str(content['origin_lati'])+', '+str(content['origin_long'])+';'
        # print(querystring)
        if len(content['speciality'])==0:
            print("Yes1 ")
            data=list(hospitals.find({},{"_id":0}))
            i=len(data)
        else:
            print("No")
            speciality=content['speciality']
            print(speciality)
            ids=[str(x.get("Hpt_id")) for x in list(doctors.find({"Dr_type":speciality,"status":"True"}))]
            data=[]
            for x in ids:
                i+=1
                data.append(hospitals.find_one({"_id":ObjectId(x)},{"_id":0}))
        distance=[]
        # print(data)
        visit=set()
        data1=[]
        for x in data:
            if x['Hpt_id'] not in visit:
                distance.append(str(x['Hpt_location'][0])+', '+str(x['Hpt_location'][1])+';')
                visit.add(x['Hpt_id'])
                data1.append(x)
        
        querystring["destinations"]=''.join(distance)
        res=requests.request("GET", url1, headers=headers, params=querystring).json()
        for j in range(len(data1)):
            data1[j]['distance']=res["distances"][0][j]
            data1[j]['durations']=res['durations'][0][j]
            data1[j].pop("Hpt_speciality")
            data1[j].pop("Hpt_cost")
            data1[j].pop("Hpt_doctors")
        data1.sort(key=lambda x:x['distance'])
        return jsonify({"hospitals":data1,"status":200})

            
    else:
        data=list(hospitals.find({'_id':0}))
        return jsonify({"hospitals":data,"status":200})


@app.route('/home/user/doctors',methods=["GET"])
@cross_origin(origin='localhost',headers=['Content- Type','Authorization'])
def get_doctors():
    doct=list(doctors.find({},{'_id':0}))
    # temp=[hospitals.find_one({"_id":ObjectId(x['Hpt_id'])}) for x in doct]
    temp={}
    doct.sort(key=lambda x:x['status'],reverse=True)
    for x in doct:
        if temp.get(x['Hpt_id'],-1)!=-1:
            x['Hpt_name']=temp[x['Hpt_id']]
        else:
            x['Hpt_name']=hospitals.find_one({"_id":ObjectId(x['Hpt_id'])})['Hpt_name']
            temp[x['Hpt_id']]=x['Hpt_name']
        # temp.append(hospitals.find_one({"_id":ObjectId(x['Hpt_id'])})['Hpt_name'])
    return jsonify({'doctors':doct,'status':200})



@app.route('/home/user/cost',methods=["GET","POST"])
@cross_origin(origin='localhost',headers=['Content- Type','Authorization'])
def calculate_cost():
    costs=list(hospitals.find({},{"_id":0,"Hpt_doctors":0,"Hpt_speciality":0}))
    
    temp=[]
    distance=[]
    for x in costs:
        if x.get("Hpt_fullbody",None)!=None:
            temp.append(x)
            temp[-1]['Hpt_fullbody']['total']=0
            for y in x["Hpt_fullbody"].values():
                temp[-1]['Hpt_fullbody']['total']+=int(y)
            temp[-1]['Hpt_fullbody']['total']=str(temp[-1]['Hpt_fullbody']['total'])
            distance.append(str(temp[-1]['Hpt_location'][0])+', '+str(temp[-1]['Hpt_location'][1])+';')


    
    import requests
    url1 = "https://trueway-matrix.p.rapidapi.com/CalculateDrivingMatrix"

    querystring = {"origins":"23.237696056902493, 77.40107993996217;","destinations":"23.231859715443527, 77.43622760832372;23.229375249406406, 77.43442516379237"}

    headers = {
        'x-rapidapi-key': "327f8a6b06msh8f77c136d8ca000p1f6dbajsn966200f786c5",
        'x-rapidapi-host': "trueway-matrix.p.rapidapi.com"
        }
    querystring["destinations"]=''.join(distance)
    res=requests.request("GET", url1, headers=headers, params=querystring).json()
    for j in range(len(temp)):
        temp[j]['distance']=res["distances"][0][j]
        temp[j]['durations']=res['durations'][0][j]
        temp[j].pop("Hpt_cost")
            
    
    return jsonify({'status':200,"filters":temp})


@app.route('/home/user/cost/filters',methods=["GET","POST"])
@cross_origin(origin='localhost',headers=['Content- Type','Authorization'])

def calculate_custom_cost():
    content=request.get_json()
    if len(content['filters'])==0:
        costs=list(hospitals.find({},{"_id":0,"Hpt_doctors":0,"Hpt_speciality":0}))
    
        temp=[]
        distance=[]
        for x in costs:
            if x.get("Hpt_fullbody",None)!=None:
                temp.append(x)
                temp[-1]['Hpt_fullbody']['total']=0
                for y in x["Hpt_fullbody"].values():
                    temp[-1]['Hpt_fullbody']['total']+=int(y)
                temp[-1]['Hpt_fullbody']['total']=str(temp[-1]['Hpt_fullbody']['total'])
                distance.append(str(temp[-1]['Hpt_location'][0])+', '+str(temp[-1]['Hpt_location'][1])+';')
                temp[-1]['Hpt_cost']=temp[-1]['Hpt_fullbody']
                temp[-1]['Hpt_length']=len(temp[-1]['Hpt_fullbody'])-1
                

        import requests
        url1 = "https://trueway-matrix.p.rapidapi.com/CalculateDrivingMatrix"

        querystring = {"origins":"23.237696056902493, 77.40107993996217;","destinations":"23.231859715443527, 77.43622760832372;23.229375249406406, 77.43442516379237"}

        headers = {
            'x-rapidapi-key': "327f8a6b06msh8f77c136d8ca000p1f6dbajsn966200f786c5",
            'x-rapidapi-host': "trueway-matrix.p.rapidapi.com"
            }
        querystring["destinations"]=''.join(distance)
        res=requests.request("GET", url1, headers=headers, params=querystring).json()
        for j in range(len(temp)):
            temp[j]['distance']=res["distances"][0][j]
            temp[j]['durations']=res['durations'][0][j]
            temp[j].pop("Hpt_fullbody")
                
        
        return jsonify({'status':200,"filters":temp})
    else:
        costs=hospitals.find({},{"_id":0,"Hpt_doctors":0,"Hpt_speciality":0})
        temp=[]
        distance=[]
        for x in costs:
            ok=True
            for y in content['filters']:
                if x['Hpt_cost'].get(y,-1)==-1:
                    ok=False
                    break
            if ok:
                temp.append(x)
                distance.append(str(temp[-1]['Hpt_location'][0])+', '+str(temp[-1]['Hpt_location'][1])+';')
                temp[-1]['Hpt_cost']['total']=0
                for y in content['filters']:
                    temp[-1]['Hpt_cost']['total']+=int(temp[-1]['Hpt_cost'][y])
                temp[-1]['Hpt_cost']['total']=str(temp[-1]['Hpt_cost']['total'])
                temp[-1]['Hpt_length']=len(content['filters'])
                
        if len(distance):
            import requests
            url1 = "https://trueway-matrix.p.rapidapi.com/CalculateDrivingMatrix"

            querystring = {"origins":"23.237696056902493, 77.40107993996217;","destinations":"23.231859715443527, 77.43622760832372;23.229375249406406, 77.43442516379237"}

            headers = {
                'x-rapidapi-key': "327f8a6b06msh8f77c136d8ca000p1f6dbajsn966200f786c5",
                'x-rapidapi-host': "trueway-matrix.p.rapidapi.com"
                }
            querystring["destinations"]=''.join(distance)
            res=requests.request("GET", url1, headers=headers, params=querystring).json()
            for j in range(len(temp)):
                temp[j]['distance']=res["distances"][0][j]
                temp[j]['durations']=res['durations'][0][j]
                if temp[j].get('Hpt_fullbody',-1)!=-1:
                    temp[j].pop("Hpt_fullbody")

        return jsonify({"status":200,"filters":temp})


@app.route('/home/user/pharmacy',methods=["GET","POST"])
@cross_origin(origin='localhost',headers=['Content- Type','Authorization'])
def get_pharmacy():
    phar=list(pharmacy.find({},{"_id":0}))
    return jsonify({"pharmacy":phar,"status":200})
# *************************************************************** CRUD  Protocols ***************************************************************#



if __name__=="__main__":
    app.run()
