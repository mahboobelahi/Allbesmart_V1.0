
from pprint import pprint as P
from sre_constants import SUCCESS
import threading, socket, requests, json, time,datetime
from flask import  Flask, jsonify,request
from sqlalchemy import null
from FASToryEvents_EM import configurations as CONFIG
from FASToryEvents_EM .dbModels import EnergyMeasurements, WorkstationInfo,FASToryEvents,MeasurementsForDemo
from FASToryEvents_EM  import UtilityFunctions as helper
# orchestrator connector object
#EnergyMeasurements.query.filter_by(ActiveZones='1001').update(dict(LoadCombination=9))
from FASToryEvents_EM  import db
from sqlalchemy.exc import SQLAlchemyError
from flask_sqlalchemy import SQLAlchemy





# workstation class

class Workstation:
    def __init__(self, ID, wLocIP, make ,type, wLocPort,numFast,num):
        # token
        self.token = ''
        self.access_token_time = 0
        self.expire_time = 0
        self.headers = {}
        # workstation attributes
        self.count = 0
        self.stop_recording = 0
        self.LoadCombination = 0
        self.activeZones = ''
        self.classLabel = 2
        self.BeltTension = 0
        self.make = make
        self.type = type
        self.name = f'FASTory_Energy_Monitoring_E10_Module_WrkStation_{ID}'
        self.ID = ID
        self.source_ID = 0
        self.external_ID = f'{ID}4EM'
        self.url_self = f'http://{wLocIP}:{wLocPort}' #use when working in FASTory network
        #self.url_self = f'http://{self.get_local_ip()}:{wLocPort}'#130.230.190.118
        self.port = wLocPort
        self.EM = True
        # workstaion servies
        self.measurement_ADD = f'{self.url_self}/measurements'
        self.EM_service_url = f'http://192.168.{self.ID}.4/rest/services/send_all_REST'
        self.CNV_start_stop_url = f'http://192.168.{self.ID}.2/rest/services/'
        # for reat-time grphs
        self.powerlist = []
        self.power = 0
        self.voltage = 0
        self.current = 0
        # checking for Z4 and installed EM modules
        if self.ID in CONFIG.hav_no_EM:
            self.EM = False
        if ID == 1 or ID == 7:
            self.hasZone4 = False
        else:
            self.hasZone4 = True
        self.num = num #request timeout
        self.numFast = numFast
        self.stop_simulation = False

    
    # ############################################
    #  FASTory Line Event Subscription Section
    # ############################################
    
    
    def conveyor_events(self, zone_name=None,action=None):
            """
            this method subscribe a workstation to the event for all zones of conveyor
            on that workstation

            :param zone_name:int:zones on convyor
            :return: nothing
            """

            # Prepare URL and body for the environment
            if (self.ID == 1 or self.ID == 7) and zone_name == 4:
                print(f'WkC_1:_Worksation_{self.ID} has no Service for Zone4')
                pass
            else:
                try:
                    CNV_RTU_Url_s = f'http://192.168.{str(self.ID)}.2/rest/events/Z{str(zone_name)}_Changed/notifs'
                    if action == 'subscribe':
                        # application URl
                        body = {"destUrl": f'{self.url_self}/events'}
                        
                        
                        r = requests.post(CNV_RTU_Url_s, json=body)

                        
                        print(f'WkC_3:_{self.get_ID()} has subscribed event for CNV-zone:{zone_name} with request code: {r.status_code}.')
                        print(CNV_RTU_Url_s,'\n')
                    else:
                        r = requests.delete(CNV_RTU_Url_s)
                except requests.exceptions.RequestException as err:
                    print("[X-E] OOps: Something Else", err)


    def robot_events(self, event_name= None, action=None):
        """
        this method subscribe a workstation to the event for all zones of conveyor
        on that workstation

        :param event_name:string:robot services
        :return: nothing
        """
        ROB_RTU_Url_s = f'http://192.168.{str(self.ID)}.1/rest/events/{event_name}/notifs'
        if action == 'subscribe':
            body = {"destUrl": f'{self.url_self}/events'}
            r = requests.post(ROB_RTU_Url_s, json=body)
            print(f'[X] WkC:_{self.get_ID()} has subscribed {event_name} event for Robot.\n')     
        else:
            r = requests.delete(ROB_RTU_Url_s)
            print(f'[X] WkC:_{self.get_ID()} has un-subscribed {event_name} event for Robot.\n')
 
    # auto start/stop energy-measurement service
    def invoke_EM_service(self, cmd='stop'):
        if self.EM == False:
            print("Has no EM module.")
            return
        body = {
            "cmd": cmd,
            "send_measurement_ADDR": self.measurement_ADD,
            "ReceiverADDR": 'http://192.168.100.100:2000/noware'  # f'{self.url_self}/noware'
        }
        try:
            r = requests.post(url=self.EM_service_url, json=body)
            return f"Status Code: {r.status_code}, Reason: {r.reason}"
        except requests.exceptions.RequestException as err:
            print("[X-W] OOps: Something Else", err)
            return err
    
    # checks for active zones on conveyor of a particular workstation

    def get_ZoneStatus(self):
        load = 0
        ActiveZone = ''
        for i in [1, 2, 3, 4, 5]:
            req = requests.post(
                f'http://192.168.{self.ID}.2/rest/services/Z{i}', json={"destUrl": ""})
            if req.json().get('PalletID') == '-1':
                ActiveZone = ActiveZone + '0'
            else:
                ActiveZone = ActiveZone + '1'
                load = load + 1
        return (load, ActiveZone[::-1])
    #########################################
    def get_local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip

    def get_ID(self):
        return self.ID
    
    def get_external_ID(self):
        return self.external_ID
    
    def get_headers(self):
        return self.headers
    
    def get_stop_simulation(self):
        return self.stop_simulation

    def WkSINFO(self):
        print(self.__dict__)

    def has_EM(self):
        return self.EM

    def set_has_EM(self, flage):
        self.EM = flage

    def set_source_ID(self, srID):
        self.source_ID = srID

    def set_count(self, num=0):
        self.count = num

    def count_inc(self):
        self.count = self.count + 1
        return self.count

    def stop_recording_inc(self):
        self.stop_recording = self.stop_recording + 1

    def set_stop_recording(self, num=0):
        self.stop_recording = num

    def set_stop_simulations(self,flag):
        self.stop_simulation =flag

    def updatePR_parameters(self, L, AZ):
        self.load = L
        self.activeZones = AZ

    def updateClassLabel(self, CL,BT,lc):
        self.classLabel = CL
        self.BeltTension = BT
        self.LoadCombination = lc

    def update_PVC(self, p, v, c):
        self.power = p
        self.voltage = v
        self.current = c
        print(self.power)    
    ################################################    
     
    
    
    # DB section
    def callWhenDBdestroyed(self):
        # inserting info to db
        # one time call, only uncomment when db destroyed otherwise
        # do the update
        info = WorkstationInfo(
            WorkCellName=self.name,
            WorkCellID=self.ID,
            RobotMake = self.make,
            RobotType = self.type,
            DAQ_ExternalID=self.external_ID,
            DAQ_SourceID=self.source_ID,
            HasZone4=self.hasZone4,
            HasEM_Module=self.EM,
            WorkCellIP=self.url_self,
            EM_service_url=self.EM_service_url,
            CNV_service_url=self.CNV_start_stop_url,
            Capabilities = null,
            Error_Capabilities = null
        )
        db.session.add(info)
        db.session.commit()

    def updateIP(self):
        WrkIP = WorkstationInfo.query.get(self.ID)
        WrkIP.WorkCellIP = self.url_self
        # WrkIP=WorkstationInfo.query.filter(WorkstationInfo.WorkCellID==self.ID)
        # WrkIP.update({WorkstationInfo.WorkCellIP:self.url_self})
        db.session.commit()

    # ############################################
    #  Methods related to ZDMP
    # ############################################
    

    # related to DAQ
    # events/alarms/deviceControl etc

    def handleAlarms(self):
        pass

    def sendEvent(self, type, text):
        payload = {"externalId": self.get_external_ID(),
                   "type": type,
                   "text": text}
        try:
            req = requests.post(f'{CONFIG.SYNCH_URL}/sendEvent',
                                params=payload,
                                headers=self.get_headers())
            print(f'[X-W-SnDE] {req.status_code}')
            if req.status_code !=200:
                time.sleep(1)
                req = requests.post(f'{CONFIG.SYNCH_URL}/sendEvent',
                                params=payload,
                                headers=self.get_headers())
                                
        except requests.exceptions.RequestException as err:
            print("[X-W-SnDE] OOps: Something Else", err)

    def deviceControl(self):
        pass

    # registration to ZDMP-DAQ component
    def register_device(self):
        # need to set some guard condition to avoid re-registration of device
        # each device registared against a unique external ID
        try:
            req = requests.get(
                url=f'{CONFIG.ADMIN_URL}/deviceInfo?externalId={self.external_ID}',
                headers=self.headers)
            if req.status_code == 200:
                self.set_source_ID(req.json().get('id'))
                print('[X-W-RD] Device already Registered. Device details are:\n')
                # pprint(req.json())
            else:
                print('[X-W-RD] Registering the device')
                req_R = requests.post(
                    url=f'{CONFIG.ADMIN_URL}/registerDevice?externalId={self.external_ID}&name={self.name}&type=c8y_Serial',
                    headers=self.headers)
                print(f'Http Status Code: {req_R.status_code}')
                # setting souece ID of device
                self.set_source_ID(req_R.json().get('id'))
                print('[X-W-RD] Device Registered Successfully.\n')
                # pprint(req_R.json())
        except requests.exceptions.RequestException as err:
            print("[X-W-RD] OOps: Something Else", err)

    # register data source to ASYNC-DAQ service
    def sub_or_Unsubscribe_DataSource(self, subs=False):

        payload = {"externalId": self.external_ID, "topicType": 'multi'}
        try:
            if subs:
                req = requests.delete(f'{CONFIG.ASYNCH_URL}/unsubscribe',
                                   params=payload, headers=self.headers)
                self.sendEvent('DAQ-ASYNC', 'Data source have unsubscribed to previous subscriptions.....')
                print(f'[X-W-SUD] Subscribing to Data Source: {self.external_ID}....{req.status_code}')
                req = requests.post(f'{CONFIG.ASYNCH_URL}/subscribe',
                                   params=payload, headers=self.headers)
                if req.status_code == 200:
                    self.sendEvent('DAQ-ASYNC', 'Data source have subscribed to ASYNC data access...')
                    print(f'[X-W-SUD] Subscription Status: {req.status_code} {req.reason}')
                elif req.status_code == 500 or req.status_code == 408:
                    time.sleep(1)
                    req = requests.post(f'{CONFIG.ASYNCH_URL}/subscribe',
                                       params=payload, headers=self.headers)
                    if req.status_code == 200:
                        self.sendEvent('DAQ-ASYNC', 'Data source have subscribed to ASYNC data access...')
                        print(f'[X-W-SUD] Subscription Status: {req.status_code} {req.reason}')

                else:

                    print(f'[X-W-SUD] Subscription Status: {req.status_code} {req.reason}')
            else:
                req = requests.delete(f'{CONFIG.ASYNCH_URL}/unsubscribe',
                                   params=payload, headers=self.headers)

                if req.status_code == 200:
                    print(f'[X-W-SUD] Unsubscribe Status: {req.status_code} {req.reason}')
                else:
                    print(f'[X-W-SUD] Unsubscribe Status: {req.status_code} {req.reason}')

        except requests.exceptions.RequestException as err:
            print("[X-W-SUD] OOps: Something Else", err)


    def get_access_token(self):
        try:
            ACCESS_URL = "https://keycloak-zdmp.platform.zdmp.eu/auth/realms/testcompany/protocol/openid-connect/token"
            headers = {'accept': "application/json", 'content-type': "application/x-www-form-urlencoded"}
            payload = "grant_type=password&client_id=ZDMP_API_MGMT_CLIENT&username=zdmp_api_mgmt_test_user&password=ZDMP2020!"
            response = requests.post(ACCESS_URL, data=payload, headers=headers)
            if response.status_code == 200:
                self.token = response.json().get('access_token')
                self.access_token_time = int(time.time())
                self.expire_time = response.json().get('expires_in')
                self.headers = {"Authorization": f"Bearer {self.token}"}
                print(f'[X-W-Tk] ({response.status_code})')
                self.sendEvent('Token', 'Accessing Token......')
            else:
                print(f"[X-W-Tk] {response.status_code}")
        except requests.exceptions.RequestException as err:
            self.sendEvent('Token', 'Not Accessed......')
            print("[X-W-Tk] OOps: Something Else", err)            
    
    # *******************************************
    #   Flask Application
    # *******************************************  
    
    def runApp(self):

        app = Flask(__name__) 
        app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:mahboobelahi93@localhost/fastoryemdb'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db = SQLAlchemy(app)

        @app.route('/', methods=['GET'])
        def welcom():

            return '<h2>Hello from  Workstation_' + str(self.__ID) + '! Workstation_request.url :=  ' + request.url+'<h2>'


        @app.route('/conveyorEventSubscription', methods=['POST'])
        def conveyorEventSubscription():
            for zn in range(1, 5):
                self.conveyor_events(zone_name=zn,action='subscribe')
            return "ok"
        
        @app.route('/conveyorEventUnSubscription', methods=['DELETE'])
        def conveyorEventUnSubscription():
            for zn in range(1, 5):
                self.conveyor_events(zone_name=zn,action='unsubscribe')
            return "ok"      
        
        
        @app.route('/RobotEventSubscription', methods=['POST'])
        def RobotEventSubscription():
            if id ==1 or id == 7:
                pass
            else:
                self.robot_events(event_name='PenChangeEnded',action='subscribe')
                self.robot_events(event_name='PenChangeStarted',action='subscribe')
                self.robot_events(event_name='DrawStartExecution',action='subscribe')
                self.robot_events(event_name='DrawEndExecution',action='subscribe')
            return "ok"
        
        @app.route('/RobotEventUnSubscription', methods=['DELETE'])
        def RobotEventUnSubscription():
            if id ==1 or id == 7:
                pass
            else:
                self.robot_events(event_name='PenChangeEnded',action='unsubscribe')
                self.robot_events(event_name='PenChangeStarted',action='unsubscribe')
                self.robot_events(event_name='DrawStartExecution',action='unsubscribe')
                self.robot_events(event_name='DrawEndExecution',action='unsubscribe')
            return "ok"

        # @app.route('/api/powerEvents',methods=['POST'])
        # def powerEvents():
        #     event_body = request.json
        #     P(event_body)

        @app.route('/events', methods=['POST'])
        def LineEvents():

            print(f'[X-Wrk]: {request.json}')
       
            return jsonify(SUCCESS=True)

        app.run(host='0.0.0.0', port=self.port)   