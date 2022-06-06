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
    #helper.createModels()
    #time.sleep(5)
    #helper.get_local_ip()
    helper.createModels()
    app.run(host=helper.get_local_ip(), port=CONFIG.appLocPort,use_reloader=False,debug=True)#,use_reloader=False,debug=True



