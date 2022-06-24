import threading,time
from FASToryEvents_EM import app
from FASToryEvents_EM import UtilityFunctions as helper
from FASToryEvents_EM import configurations as CONFIG
from FASToryEvents_EM.dbModels import EnergyMeasurements, WorkstationInfo,MeasurementsForDemo



if __name__ == '__main__':
   
    # Workstation Objects
    start_workstations=threading.Thread(target=helper.Workstations)
    start_workstations.daemon=True
    start_workstations.start()

    # #event subscriptions for orchestrator

    # time.sleep(6)
    orc_subscriptions=threading.Timer(3,helper.EventSubscriptions,args=(WorkstationInfo.query.all(),))
    orc_subscriptions.daemon=True
    orc_subscriptions.start()
    # #helper.get_local_ip()
    #helper.createModels()
    app.run(host='0.0.0.0', port=CONFIG.appLocPort,debug=False)#,use_reloader=False,debug=True



