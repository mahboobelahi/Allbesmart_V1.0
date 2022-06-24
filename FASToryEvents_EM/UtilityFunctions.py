from tabnanny import check
import threading,time,requests,json,socket,csv
from FASToryEvents_EM import FASToryWorkstations as WkS
from FASToryEvents_EM.configurations import *
from FASToryEvents_EM.dbModels import EnergyMeasurements, WorkstationInfo,MeasurementsForDemo
from FASToryEvents_EM import db
from netifaces import interfaces, ifaddresses, AF_INET
from sqlalchemy.ext.serializer import loads, dumps
from sqlalchemy.exc import SQLAlchemyError

#under test
def reslove_update_IP():
    for ifaceName in interfaces():
        addresses = [i['addr'] for i in ifaddresses(ifaceName).setdefault(AF_INET, [{'addr':'No IP addr'}] )]
        print(addresses)
        print ('%s: %s' % (ifaceName, ', '.join(addresses)))


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip


#creating data base modles
def createModels():
    db.create_all()
    db.session.commit()



#subscription for Orchestrator
def EventSubscriptions(result):
    body = {"destUrl": f'http://{wrkCellLocIP}:{appLocPort}/api/logCellEvents'}                               
    for workCell in result:
        #robot event subscription if possible 
        if workCell.id !=2 and workCell.id !=10 :# and id!=1:
            continue
        if workCell.ComponentStatus[0]:
            print(f'[XU-R_Subscriptions]')
            for eventID in RobotEvents:
                try:
                    
                    ROB_RTU_Url_s = f'http://192.168.{str(workCell.id)}.1/rest/events/{eventID}/notifs'
                    
                    r = requests.post(ROB_RTU_Url_s, json=body)
                    print(f'[X-U]:Robot_{workCell.id} has subscribed to {eventID} event with request code: {r.status_code}.')           
                except requests.exceptions.RequestException as err:
                        print("[X-E] OOps: Something Else", err)

        #conveyor zone event subscription if possible
        if workCell.ComponentStatus[1]:
            print(f'[XU-C_Subscriptions]')
            if workCell.HasZone4:
                for eventID in ConveyorEvents:    
                    try:
                        CNV_RTU_Url_s = f'http://192.168.{str(workCell.id)}.2/rest/events/{eventID}/notifs' 
                        r = requests.post(CNV_RTU_Url_s, json=body)
                        print(f'[X-U]:CNV_{workCell.id} has subscribed:{eventID} event with request code: {r.status_code}.')
                    except requests.exceptions.RequestException as err:
                        print("[X-E] OOps: Something Else", err)
            else:
                for eventID in ConveyorEvents[:3]:    
                    try:
                        CNV_RTU_Url_s = f'http://192.168.{str(workCell.id)}.2/rest/events/{eventID}/notifs' 
                        # application URl
                        body = {"destUrl": f'http://{wrkCellLocIP}:{appLocPort}/api/logCellEvents'}              
                        #print(body)
                        r = requests.post(CNV_RTU_Url_s, json=body)
                        print(f'[X-U]:CNV_ has subscribed:{eventID} event with request code: {r.status_code}.')
                    except requests.exceptions.RequestException as err:
                        print("[X-E] OOps: Something Else", err) 

            if workCell.HasEM_Module:
                try:
                    E10_Url = f'http://192.168.{str(workCell.id)}.4/rest/events/send_rest/notifs' 
                    r = requests.post(E10_Url, json= {"destUrl": "http://192.168.189.101:2000/api/powerEvents"})
                    print(f'[XFW]:WorkCell_{workCell.id}has subscribed: E10 event with request code: {r.status_code}.')
                except requests.exceptions.RequestException as err:
                    print("[X-E] OOps: Something Else", err) 

#Unsubscription for Orchestrator
def EventUnSubscriptions(result):

    for workCell in result:
        #robot event Unsubscription if possible 
        if workCell.ComponentStatus[0]:
            print(f'[XU-R_UnSubscriptions]')
            for eventID in RobotEvents:
                try:
                    ROB_RTU_Url_s = f'http://192.168.{str(workCell.id)}.1/rest/events/{eventID}/notifs'
                    r = requests.delete(ROB_RTU_Url_s)
                    print(f'[X-U]:Robot_{workCell.id} has Unsubscribed to {eventID} event with request code: {r.status_code}.')           
                except requests.exceptions.RequestException as err:
                        print("[X-E] OOps: Something Else", err)

        #conveyor zone event Unsubscription if possible
        if workCell.ComponentStatus[1]:
            print(f'[XU-C_UnSubscriptions]')
            if workCell.HasZone4:
                for eventID in ConveyorEvents:    
                    try:
                        CNV_RTU_Url_s = f'http://192.168.{str(workCell.id)}.2/rest/events/{eventID}/notifs' 
                        r = requests.delete(CNV_RTU_Url_s)
                        print(f'[X-U]:CNV_{workCell.id} has Unsubscribed:{eventID} event with request code: {r.status_code}.')
                    except requests.exceptions.RequestException as err:
                        print("[X-E] OOps: Something Else", err)
            else:
                for eventID in ConveyorEvents[:3]:    
                    try:
                        CNV_RTU_Url_s = f'http://192.168.{str(workCell.id)}.2/rest/events/{eventID}/notifs' 
                        # application URl
                        body = {"destUrl": f'http://{wrkCellLocIP}:{appLocPort}/api/logCellEvents'}              
                        r = requests.delete(CNV_RTU_Url_s)
                        print(f'[X-U]:CNV_{workCell.id} has Unsubscribed:{eventID} event with request code: {r.status_code}.')
                    except requests.exceptions.RequestException as err:
                        print("[X-E] OOps: Something Else", err) 
            
            if workCell.HasEM_Module:
                try:
                    E10_Url = f'http://192.168.{str(workCell.id)}.4/rest/events/send_rest/notifs' 
                    r = requests.delete(E10_Url)
                    #print(f'[XFW]:WorkCell_{workCell.id}has subscribed:{eventID} event with request code: {r.status_code}.')
                except requests.exceptions.RequestException as err:
                    print("[X-E] OOps: Something Else", err) 

#accessing JWT token
def get_access_token():
        try:
            response = requests.post(ACCESS_URL, data=payload, headers=headers)
            if response.status_code == 200:
                token = response.json().get('access_token')
                access_token_time = int(time.time())
                expire_time = response.json().get('expires_in')
                DAQ_header  = {"Authorization": f"Bearer {token}"}
                print(f'[X-W-Tk] ({response.status_code})')
                #sendEvent('Token', 'Accessing Token......')
            else:
                print(f"[X-W-Tk] {response.status_code}")
        except requests.exceptions.RequestException as err:
            #sendEvent('Token', 'Not Accessed......')
            print("[X-W-Tk] OOps: Something Else", err)
        return (access_token_time,expire_time,DAQ_header)

#download record as csv
def downloadAsCSV(fileName=None, result=None,recordType=None):
    try:
        if recordType =="measurements":
            with open(fileName,'w', newline='') as csvFile:
            
                csvWriter = csv.writer(csvFile, delimiter=',')
                csvWriter.writerow(
                    [
                        "WorkCellID", "Frequency(Hz)","RmsVoltage(V)", "RmsCurrent(A)", "Power(W)", "NominalPower",
                         "ActiveZones", "Load", "Timestamp"
                    ]
                )
                for record in result.DM_child:
                    csvWriter.writerow([
                        record.WorkCellID, record.line_Frequency,record.RmsVoltage, record.RmsCurrent, record.Power,
                        record.Nominal_Power,record.ActiveZones,  record.Load, record.timestamp
                    ])
        if recordType == "events":
            with open(fileName,'w', newline='') as csvFile:
            
                csvWriter = csv.writer(csvFile, delimiter=',')
                csvWriter.writerow([ "SenderID", "EventID",
                                    "PalletID","Recipe","Color", "timestamp"])
                for record in result.LineEvents:
                    csvWriter.writerow(record.data)
    except IOError as e:
         print ("[X-UTD] :",e)
    # if not result:
    #     raise ValueError('No data available')

def downloadAsJSON(fileName=None, result=None, recordType=None):
    try:
        if recordType == "events":
            temp =[]
            with open(fileName, 'w') as outfile:
                for record in result.LineEvents:
                    #print(record.serialize)
                    temp.append(record.serialize)
                json.dump(temp, outfile)
        if recordType == "measurements":
            #modify the return data structure by adding get dta property
            temp = {'WorkCellID':result.WorkCellID,'RmsVoltage':[], 'RmsCurrent':[],
                    'Power':[],'Nominal_Power':[], 'ActiveZones':[], 'Load':[],
                    'Frequency':[]} #,'timestamp':''
                    
            #column names
            #print(result.DM_child[0].__table__.columns.keys())
            for record in result.DM_child:
                temp['RmsVoltage'].append(record.RmsVoltage)
                temp['RmsCurrent'].append(record.RmsCurrent)
                temp['Power'].append(record.Power)
                temp['Nominal_Power'].append(record.Nominal_Power)
                temp['ActiveZones'].append(record.ActiveZones)
                temp['Load'].append(record.Load)
                temp['Frequency'].append(record.line_Frequency)
                #temp['timestamp'].append('timestamp')
            with open(fileName, 'w') as outfile:
                json.dump(temp, outfile)

    except IOError as e:
         print ("[X-UTD] :",e)


def dump_datetime(value):
        """Deserialize datetime object into string form for JSON processing."""
        if value is None:
            return None
        return [value.strftime("%Y-%m-%d"), value.strftime("%H:%M:%S")]

def parseCommand(message):
    try:
        body={"destUrl" : ""}
        payload=json.loads(message.payload)
        if payload.get('data'):
            payload= payload.get('data')
        
        #db will handles
        exID = int(payload.get("external_ID").split('4')[0])
        result = WorkstationInfo.query.get(exID)
        if payload.get("send_power_measurements") and result.HasEM_Module:
            cmd = payload.get("send_power_measurements")
            if cmd =="start":
                # check previous EM subscriptions
                req = requests.get(f'http://192.168.{result.id}.4/rest/events/send_rest/notifs')
                print(req.json().get("children"))
                if req.json().get("children"):
                    req = requests.post(result.EM_service_url,json={"destUrl": "http://192.168.100.100:2002/api/measurements"})
                    print(f'[X] {str(req.status_code)+req.reason}')
                
                else:
                    req = requests.post(f'http://192.168.{result.id}.4/rest/events/send_rest/notifs',
                                        json={"destUrl": "http://192.168.100.100:2002/api/measurements"})
                    req = requests.post(result.EM_service_url,json=body)
                    print(f'[X] {str(req.status_code)+req.reason}')
            else:
                E10_Url = f'http://192.168.{str(result.id)}.4/rest/events/send_rest/notifs'
                req = requests.delete(E10_Url)
                print(f'[X] {str(req.status_code)+req.reason}')
        
        if  result.ComponentStatus[0]:#(payload.get("change_pen") or payload.get("draw_component")) and
            
            if payload.get("calibrate_Robot"):
                req = requests.post(f'{result.Robot_service_url+payload.get("calibrate_Robot")}',json=body)
                print(f'[X] service_{payload.get("calibrate_Robot")+str(req.status_code)+req.reason}')
            
            if payload.get("change_pen"):
                #print(f'[X] {result.Robot_service_url+payload.get("change_pen")}')
                req = requests.post(f'{result.Robot_service_url+payload.get("change_pen")}',json=body)
                print(f'[X] service_{payload.get("change_pen")+str(req.status_code)+req.reason}')
            
            if payload.get("draw_component"):
                #print(f'[X] {result.Robot_service_url+payload.get("draw_component")}')
                req = requests.post(f'{result.Robot_service_url+payload.get("draw_component")}',json=body)
                print(f'[X] service_{payload.get("draw_component")+str(req.status_code)+req.reason}')

        if payload.get("move_pallet"):
            
            destinamtion = payload.get("move_pallet")
            if ((destinamtion == 'TransZone14' or destinamtion == 'TransZone45')and result.HasZone4 == False):
                req = requests.post(f'{result.CNV_service_url+payload.get("move_pallet")}',json=body)
                print(f'[X] {str(req.status_code)+req.reason}')
            else:
                req = requests.post(f'{result.CNV_service_url+payload.get("move_pallet")}',json=body)
                print(f'[X] {str(req.status_code)+req.reason}')
                
    except ValueError:
        print('[X-Routes] Decoding JSON has failed')
    except SQLAlchemyError as e:
        print(f'[X]',str(e.__dict__['orig']))
    except requests.exceptions.RequestException as err:
        print("[X] OOps:HTTP-Error", err)

# {
#     "external_ID":"104EM",
#     "send_power_measurements": "start",
#     "move_pallet":"TransZone12",
#     "change_pen" :"ChangePenRED",
#     "draw_component":"Draw1"
# }
#sending events from Simulatorfile
def simulateData(externalId,measurements,payload,
                        access_token_time,expire_time,headers):     
        try:
            with open('3-7-2017_12.json') as file: 
                event = json.load(file)  
                for i in range(0,500):
                    if int(time.time() - access_token_time) >= (expire_time - 50):
                        print(f'[X-SD] Accessing New Token.......')
                        access_token_time,expire_time,headers = get_access_token()
                    req_A = requests.post(url=f'{SYNCH_URL}/sendMeasurement?externalId={externalId}&fragment=CurrentMeasurement&value={measurements[i].RmsCurrent}&unit=A',       
                                            headers= headers)
                    req_V = requests.post(url=f'{SYNCH_URL}/sendMeasurement?externalId={externalId}&fragment=VoltageMeasurement&value={measurements[i].RmsVoltage}&unit=V',   
                                            headers=headers)
                    req_P = requests.post(url=f'{SYNCH_URL}/sendMeasurement?externalId={externalId}&fragment=PowerMeasurement&value={measurements[i].Power}&unit=W',
                                            headers=headers)
                    req_event = requests.post(  url=f'{SYNCH_URL}/sendCustomMeasurement',
                                                params=payload,headers=headers,
                                                json={"value": event[i].get("event")})
                    #checking for token lifetime
                    print(f'[X-RS] ({req_A.status_code},{req_V.status_code},{req_P.status_code},{req_event.status_code},{i})')
                    print(event[i].get("event"))
                    time.sleep(1)
        except requests.exceptions.RequestException as err:
                print("[X-E] OOps: Something Else", err)
        except OSError:
                print("[X-E] Could not open/read file: 3-7-2017_12.json")
        except ValueError as err:  # includes simplejson.decoder.JSONDecodeError
                print('[X-E]Decoding JSON has failed',err)        
        print('[X-UT] Recursion....')
        simulateData(externalId,measurements,payload,
                        access_token_time,expire_time,headers)

#workcell obj
def Workstations():
    
    for id in range(1,13):
        if id !=2 :#and id!=10 :# and id!=1:
            continue
        temp_obj = WkS.Workstation(id,wrkCellLocIP,
                                    make[id-1],type[id-1],
                                    wrkCellLocPort+id,numFast=3,num=3)
        #temp_obj.WkSINFO()

        #subscribing to conveyor Zone events
        temp_obj.LineEventsSubscription()
        #temp_obj.UnSubscribeToLineEvents()
        
        #deleting past subscription to EM service.
        #temp_obj.invoke_EM_service()
        #now invoke EM service for accurate results
        # send_measurements=threading.Timer(8,temp_obj.invoke_EM_service,args=("start",))
        # send_measurements.daemon=True
        # send_measurements.start()
        #startring server for workstation
        threading.Thread(target=temp_obj.runApp,daemon=True).start()
        temp_obj.get_access_token()
        #wait a while for server initialization
        #time.sleep(1)
        #check device registration or register device to ZDMP-DAQ component 
        #temp_obj.register_device()
        #subscribe device for ASYNC data access
        #temp_obj.sub_or_Unsubscribe_DataSource(True)

        #Db functions
        #if you delete DB Schema then call this method. After that comment it.
        #temp_obj.callWhenDBdestroyed()
        #uncomment following line when base IP got changed
        #temp_obj.updateIP()



