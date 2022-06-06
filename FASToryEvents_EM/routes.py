import threading,requests
from pprint import pprint as P
from FASToryEvents_EM import UtilityFunctions as helper
from FASToryEvents_EM import app,db
from FASToryEvents_EM.dbModels import MeasurementsForDemo,WorkstationInfo,FASToryEvents
from flask import request,jsonify
import json,time, datetime
from FASToryEvents_EM.configurations import *
from  flask_mqtt import Mqtt
from sqlalchemy.exc import SQLAlchemyError




mqtt = Mqtt(app)
#####MQTT Endpoints################
@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    if rc==0:
        pass
        result=WorkstationInfo.query.all()
        print("[X-Routes] connected, OK Returned code=",rc)
        # #subscribe to tpoics
        time.sleep(1)
        mqtt.unsubscribe_all()
        # #mqtt.unsubscribe(BASE_TOPIC)
        # time.sleep(1)
        for  res in result:
            if res.id==10:
                mqtt.subscribe(f'T5_1-Data-Acquisition/DataSource ID: {res.DAQ_ExternalID} - MultiTopic/Measurements/cmd')
                print(f'[X-Routes] Subscribing to Topic: T5_1-Data-Acquisition/DataSource ID: {res.DAQ_ExternalID} - MultiTopic/Measurements/cmd')
                print(f'[X-Routes] {res.id}')    
    else:
        print("[X-Routes] Bad connection Returned code=",rc)

@mqtt.on_subscribe()
def handle_subscribe(client, userdata, mid, granted_qos):
    print('[X-Routes] Subscription id {} granted with qos {}.'
          .format(mid, granted_qos))   

@mqtt.unsubscribe()
def handle_unsubscribe(client, userdata, mid):
    print('Unsubscribed from topic (id: {})'.format(mid))

@mqtt.on_disconnect()
def handle_disconnect():
    mqtt.unsubscribe_all()
    # mqtt.unsubscribe(BASE_TOPIC)
    mqtt.unsubscribe_all()
    print("[X-Routes] CLIENT DISCONNECTED")

#handles commands from MQTT 
##command structure#####
# {
#     "external_ID":"104EM",
#     "E10_Services": "start",
#     "CNV":{"cmd":"start","CNV_section":"both"}
# }
@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    try:
        payload=json.loads(message.payload).get('data')
        print(f"{type(payload)},'??',{payload}")
        print(f"[X-Routes] {type(payload)},'??',{payload.get('data')}")
        #db will handles
        exID = int(payload.get("external_ID").split('4')[0])
        result = WorkstationInfo.query.get(exID)
        E10_url=result.EM_service_url
        CNV_url = result.CNV_service_url
        url_self = result.WorkCellIP

        if payload.get("E10_Services") !=None and exID not in hav_no_EM:

            cmd = payload.get("E10_Services")
            # res=threading.Thread(target=helper.invoke_EM_service,
            #                             args=(E10_url,cmd),
            #                             daemon=True).start()
            # print('[X-Routes] ',res)
            ######For Simulation#########
            # if cmd == 'stop':
            #     requests.post(url=f'{result.WorkCellIP}/api/stop_simulations',timeout=60)
            # else:
            #     requests.post(url=f'{result.WorkCellIP}/api/start_simulations',timeout=60)
            #############################
        else:
            print(f'[X-Routes] Invalid Command!')

        if payload.get("CNV")!=None:
            if payload.get("CNV").get("cmd") !=None:
                cnv_cmd = payload.get("CNV").get("cmd")
                cnv_section = payload.get("CNV").get("CNV_section").lower()
                if exID in [7,1] and (cnv_section == 'bypass' or cnv_section == 'both'):
                    print(f'[X-Routes] Invalid Command! ')
                else:
                    
                    res= threading.Thread(target=helper.cnv_cmd,
                                                args=((cnv_cmd,cnv_section,CNV_url,url_self)),
                                                daemon=True).start()
                    print('[X-Routes] ',res)
                
    except ValueError:
        print('[X-Routes] Decoding JSON has failed')

########Flask Application Endpoints################

#Welcom Route
@app.route('/', methods = ['GET'])
def home():
    if request.method == 'GET':
        res =jsonify(
            {
                "app_name":"FASToryEvent_EM", "script":"Orchestrator",
                "Listening at":f'Listening at http://{helper.get_local_ip()}:2000/',
                "Open Call ID":"1","Open Call Patner":"Allbesmart"
            }
        )
        return  res

# DB CRUD Operations
@app.route('/createDbModel', methods=['POST'])
def createDbModel():
        helper.createModels()
        return jsonify({"res":"Model Created"})


@app.route('/api/deleteDbModel', methods=['DELETE'])
def deleteDbModel():
    FASToryEvents.__table__.drop()
    return jsonify({"res":"Model deleted"})


@app.route('/api/addLineEvent',methods=['POST'])
def addLineEvent():#external_id,num

    #########incomplete################
    try:
        newEvent = FASToryEvents(
                    Events= json.dumps(request.json.get('event')),
                    SenderID = request.json.get('event').get('senderId'),
                    Fkey = request.json.get('Fkey'))

        db.session.add(newEvent)
        db.session.commit()
        return jsonify({"Query Status":200})
    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])

        return jsonify({"Query Status":error})



#########################SimulatorData#########################

@app.route('/api/addSimEvent',methods=['POST'])
def addSimEvent():
    def insert():
        with open('3-7-2017_12.json') as file:

            for event in json.load(file):
                try:
                    newEvent = FASToryEvents(
                                Events= event,
                                SenderID = event.get('event').get('senderId'),
                                Fkey = 10)

                    db.session.add(newEvent)
                    db.session.commit()
                    print(f'[X-Orc-Sim-Insert]:')
                    P(event)
                    time.sleep(1)
                except SQLAlchemyError as e:
                    error = str(e.__dict__['orig'])

                    return {"Query Status":error}
        print('[X-Orc] Recursion....')
        insert()

    threading.Thread(target=insert,daemon=True).start()
    return jsonify({"Query Status":200})

@app.route('/api/sendSimdata',methods=['POST'])
def sendSimdata():
    print(request.args.to_dict())
    externalId= request.args.to_dict().get("externalId")
    measurements = MeasurementsForDemo.query.filter_by(WorkCellID=externalId.split('4')[0]).all()
    #events = FASToryEvents.query.filter_by(Fkey=externalId.split('4')[0]).all()[500]
    payload = { 
                "externalId": externalId,
                "fragment": "SimulatorEvents"
            }
    access_token_time,expire_time,headers = helper.get_access_token()
    simLoop = threading.Thread(target=helper.simulateData,args=(externalId,measurements,payload,
                                access_token_time,expire_time,headers))
    simLoop.daemon=True
    simLoop.start()
    return "Ok"


