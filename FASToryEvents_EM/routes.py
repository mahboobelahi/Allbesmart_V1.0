import csv,string
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
        #subscribe to tpoics
        mqtt.unsubscribe_all()
        # #mqtt.unsubscribe(BASE_TOPIC)
        time.sleep(1)
        for  res in result:
            if res.id==2 or res.id==10:
                mqtt.subscribe(f'T5_1-Data-Acquisition/DataSource ID: {res.DAQ_ExternalID} - MultiTopic/Measurements/cmd')
                print(f'[X-Routes] Subscribing to Topic: T5_1-Data-Acquisition/DataSource ID: {res.DAQ_ExternalID} - MultiTopic/Measurements/cmd')
                print(f'[X-Routes] {res.id}')    
    else:
        print("[X-Routes] Bad connection Returned code=",rc)

@mqtt.on_subscribe()
def handle_subscribe(client, userdata, mid, granted_qos):
    print('[X-Routes] Subscription id {} granted with qos {}.'
          .format(mid, granted_qos))   

# @mqtt.unsubscribe()
# def handle_unsubscribe(client, userdata, mid):
#     print('Unsubscribed from topic (id: {})'.format(mid))

@mqtt.on_disconnect()
def handle_disconnect():
    mqtt.unsubscribe_all()
    # mqtt.unsubscribe(BASE_TOPIC)
    mqtt.unsubscribe_all()
    print("[X-Routes] CLIENT DISCONNECTED")

#handles commands from MQTT 
##command structure#####

# {
#     "external_ID":"24EM",
#     "send_power_measurements": "start",
#     "move_pallet":"TransZone12",
#     "change_pen" :"ChangePenRED",
#     "draw_component":"Draw1",
#     "calibrate_Robot":"calibrate"
# }
@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    
    executeCommand=threading.Thread(target=helper.parseCommand, args=(message,))
    executeCommand.daemon=True
    executeCommand.start()
    

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

@app.route('/api/getMeasurements',methods=['GET'])
def getMeasurement():
    param =request.args.to_dict()
    n = param.get("n")
    externalId= param.get("externalId").split('4')[0] 
    try:
        temp=[]
        result = WorkstationInfo.query.filter_by(WorkCellID=externalId).first()
        for res in result.DM_child[-2:]:
            temp.append(res.getMeasuremnts)
        
        return jsonify(temp[::-1])
    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
    return jsonify({"code":404})
    
@app.route('/api/getEvents',methods=['GET'])
def getEvents():

    param =request.args.to_dict()
    n = param.get("n")
    externalId= param.get("externalId").split('4')[0] 
    temp = []
    try:
        result = WorkstationInfo.query.filter_by(WorkCellID=externalId).first()
        for res in result.LineEvents[-2:]:
            temp.append(res.serialize)
        return jsonify(temp[::-1])

    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
    return jsonify({"code":404})

@app.route('/api/downloadRecord',methods=['GET'])
def downloadRecord():
    param =request.args.to_dict()
    externalId= param.get("externalId")
    try:
        result = WorkstationInfo.query.filter_by(WorkCellID=externalId.split('4')[0]).first()
        
        if param.get("fileExtension") == 'csv':
            helper.downloadAsCSV(f"{param.get('fileName')}.csv",result,param.get('recordType'))
        if param.get("fileExtension") == 'json':
            
            #print(result.LineEvents[0].serialize)
            helper.downloadAsJSON(f"{param.get('fileName')}.json",result,param.get('recordType'))
    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
    return "ok"

@app.route('/api/updateComponentStatus',methods=['PUT'])
def componentStatus():
    
    if request.args.to_dict("externalId"):
        result = WorkstationInfo.query.get(request.args.to_dict().get("externalId").split('4')[0])
        result.ComponentStatus = request.json[componentStatus[result.id-1] ]
    else:
        for result in WorkstationInfo.query.all():
            print(request.json)
            result.ComponentStatus = request.json[result.id-1] 
    db.session.commit()
    return jsonify(SUCCESS=True)

@app.route('/api/updatCapabilities',methods=['PUT'])
def updatCapabilities():
    try:
        for result in WorkstationInfo.query.all():
            result.Capabilities = request.json[result.id-1] 
        db.session.commit()
        return jsonify({"code":200})

    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        print(f'[X_SQL_Err] error')
        return jsonify({"Query Status":error})

@app.route('/api/updatWorkstationCapability',methods=['PUT'])
def updatCapability():

    externalId = request.args.to_dict().get("externalId").split('4')[0] 
    result = WorkstationInfo.query.get(externalId)
    result.Capabilities = request.json
    db.session.commit()

    return jsonify({"code":200})

@app.route('/api/orcEventSubscrption',methods=['POST'])
def orcEventSubscrption():
     
    status=helper.EventSubscriptions(WorkstationInfo.query.all())
    return jsonify(status)

@app.route('/api/orcEventUnSubscrption',methods=['DELETE'])
def orcEventUnSubscrption():
    status=helper.EventUnSubscriptions(WorkstationInfo.query.all())
    return jsonify(status)

@app.route('/api/powerEvents',methods=['POST'])
def powerEvents():
    event_body = request.json
    print('[X]',[ event_body.get("CellID"),event_body.get("line_frequency"),
            event_body.get("rms_current_c"),event_body.get("rms_voltage_c"),
            event_body.get("power_factor_c"),event_body.get("power_factorlow_c"),
            event_body.get("active_power_c"),event_body.get("apparent_power_c"),event_body.get("reactive_power_c"),
            event_body.get("active_energy_c"),event_body.get("reactive_energy_c"),event_body.get("apparent_energy_c")])
    return "ok"
    
@app.route('/api/logCellEvents',methods=['POST'])
def logCellEvevnts():
    event_body = request.json
    #mapping penID to color name
    if event_body.get("payload").get("PenColor"):
        event_body["payload"]["PenColor"]= PenColors[event_body.get("payload").get("PenColor")]
    print(f'[XR-logEvent] {event_body}')
    # return "ok"
    try:
        newEvent = FASToryEvents(
                    Events= {"event":event_body},
                    SenderID = event_body.get('senderID'),
                    Fkey =  event_body.get('senderID').strip(string.ascii_letters))

        db.session.add(newEvent)
        db.session.commit()
        print(f'[X_SQ] Status: {200}')
        return jsonify({"Query Status":200})
    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        print(f'[X_SQL_Err] error')
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


