import threading
from FASToryEvents_EM import app
from FASToryEvents_EM import UtilityFunctions as helper
from FASToryEvents_EM import configurations as CONFIG
from FASToryEvents_EM.dbModels import EnergyMeasurements, WorkstationInfo,MeasurementsForDemo



if __name__ == '__main__':
    # query = MeasurementsForDemo.query.all()
    # fileName='forDemo.csv'
    # helper.SQL_queryToCsv(fileName,query)
    # mqtt = MqqtClient(CONFIG.NAME,CONFIG.MQTT_CLIENT_ID)
    # mqtt.connect()
    
    #helper.createModels()    
    # Workstation Objects
    # start_workstations=threading.Thread(target=helper.Workstations)
    # start_workstations.daemon=True
    # start_workstations.start()
    #event subscriptions for orchestrator
    # orc_subscriptions=threading.Thread(target=helper.EventSubscriptions)
    # orc_subscriptions.daemon=True
    # orc_subscriptions.start()
    #time.sleep(5)
    #helper.get_local_ip()
    helper.createModels()
    app.run(host='0.0.0.0', port=CONFIG.appLocPort,debug=False)#,use_reloader=False,debug=True



