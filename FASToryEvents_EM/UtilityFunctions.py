import threading,time,requests,json,socket,csv
#from FASToryEvents_EM import Workstation as WkS
from FASToryEvents_EM.configurations import *
from FASToryEvents_EM.dbModels import EnergyMeasurements, WorkstationInfo,MeasurementsForDemo
from FASToryEvents_EM import db
from netifaces import interfaces, ifaddresses, AF_INET

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

#####accessing JWT token############
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

#####sending events from Simulatorfile############
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
                                                json={"SimEvent": event[i].get("event")})
                    #checking for token lifetime
                    print(f'[X-SD-E] ({req_A.status_code},{req_V.status_code},{req_P.status_code},{req_event.status_code},{i})')

                    time.sleep(1)
        except requests.exceptions.RequestException as err:
                print("[X-E] OOps: Something Else", err)
        except OSError:
                print("[X-E] Could not open/read file: 3-7-2017_12.json")
        except ValueError as err:  # includes simplejson.decoder.JSONDecodeError
                print('[X-SD-E]Decoding JSON has failed',err)        
        print('[X-UT] Recursion....')
        simulateData(externalId,measurements,payload,
                        access_token_time,expire_time,headers)

#workcell obj
# def Workstations():
    
#     for id in range(1,len(CONFIG.WorkStations)+1):
#         if id !=10 :# and id!=1:
#             continue
#         temp_obj = WkS.Workstation(id,CONFIG.wrkCellLocIP,
#                                     CONFIG.make[id-1],CONFIG.type[id-1],
#                                     CONFIG.wrkCellLocPort+id,
#                                     CONFIG.num_Fast,CONFIG.num)
#         #temp_obj.WkSINFO()
#         #deleting past subscription to EM service.
#         #temp_obj.invoke_EM_service()
#         #now invoke EM service for accurate results
#         temp_obj.get_access_token()
#         # send_measurements=threading.Timer(8,temp_obj.invoke_EM_service,args=("start",))
#         # send_measurements.daemon=True
#         # send_measurements.start()
#         #startring server for workstation
#         threading.Thread(target=temp_obj.runApp,daemon=True).start()
        
#         #wait a while for server initialization
#         #time.sleep(1)
#         #check device registration or register device to ZDMP-DAQ component 
#         #temp_obj.register_device()

#         #subscribe device for ASYNC data access
#         temp_obj.sub_or_Unsubscribe_DataSource(True)

#         #Db functions
#         #if you delete DB Schema then call this method. After that comment it.
#         #temp_obj.callWhenDBdestroyed()
#         #uncomment following line when base IP got changed
#         temp_obj.updateIP()



