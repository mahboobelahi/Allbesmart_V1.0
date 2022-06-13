from datetime import datetime
from FASToryEvents_EM import db

class WorkstationInfo(db.Model):
    __tablename__ = 'workstationinfo'
    id = db.Column(db.Integer, primary_key=True)
    WorkCellName = db.Column(db.String(255), unique=True, nullable=False)
    WorkCellID = db.Column(db.Integer, unique=True, default=0,nullable=False)
    RobotMake = db.Column(db.String(10),nullable=False)
    RobotType = db.Column(db.String(10),nullable=False)
    DAQ_ExternalID = db.Column(db.String(10),nullable=False,unique=True)
    DAQ_SourceID = db.Column(db.Integer)
    HasZone4 = db.Column(db.Boolean)
    HasEM_Module = db.Column(db.Boolean)
    WorkCellIP = db.Column(db.String(255), unique=True, nullable=False)
    #WorkCellPort = db.Column(db.Integer)
    EM_service_url = db.Column(db.String(255), unique=True, nullable=False)
    CNV_service_url = db.Column(db.String(255), unique=True, nullable=False)
    EM_child= db.relationship('EnergyMeasurements',backref='WorkstationInfo',lazy=True)#,uselist=False
    DM_child= db.relationship('MeasurementsForDemo',backref='WorkstationInfo',lazy=True)#,uselist=False
    LineEvents= db.relationship('FASToryEvents',backref='RT_Events',lazy=True)#,uselist=False
    Capabilities= db.Column(db.JSON, nullable=True)
    Error_Capabilities= db.Column(db.JSON, nullable=True)
    
    
    def __repr__(self):
        return f"Workstation('{self.DAQ_ExternalID}')"
    
    # @property
    # def serialize(self):
    #    """Return object data in easily serializable format"""
    #    return {
           
    #        'SenderID': self.SenderID,
    #        # This is an example how to deal with Many2Many relations
    #        'event'  : self.Events.get("event"),
    #        'timestamp' : self.dump_datetime(self.timestamp)
    #    }
# only for PR
class EnergyMeasurements(db.Model):
    __tablename__ = 'energymeasurements'
    id = db.Column(db.Integer, primary_key=True)
    WorkCellID = db.Column(db.Integer)
    line_Frequency = db.Column('Frequency(Hz)',db.Float)
    RmsVoltage = db.Column(db.Float)
    RmsCurrent = db.Column(db.Float)
    Power = db.Column('Power(W)',db.Float)
    Nominal_Power = db.Column(db.Float)
    BeltTension = db.Column('%BeltTension',db.Integer)
    ActiveZones = db.Column(db.String(15))
    LoadCombination = db.Column(db.Integer)
    Load = db.Column(db.Integer)
    NormalizedPower = db.Column('NormalizedPower',db.Float)
    NormalizedLoad = db.Column('NormalizedLoad',db.Float)
    TrueClass = db.Column(db.Integer)
    PredictedClass = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now)
    Fkey = db.Column(db.Integer, db.ForeignKey('workstationinfo.id'),nullable=False)
    #DAQ_ExID = db.Column(db.String(10), db.ForeignKey('WorkstationInfo.DAQ_ExternalID'),nullable=False)
    def __repr__(self):
        return f"Workstation('ID:{self.WorkCellID}', 'Power:{self.Power}', 'Load:{self.Load}')"
    
# only for demo
class MeasurementsForDemo(db.Model):
    __tablename__ = 'measurementsfordemo'
    id = db.Column(db.Integer, primary_key=True)
    WorkCellID = db.Column(db.Integer)
    RmsVoltage = db.Column(db.Float)
    RmsCurrent = db.Column(db.Float)
    Power = db.Column('Power(W)',db.Float)
    Nominal_Power = db.Column(db.Float)
    ActiveZones = db.Column(db.String(15))
    Load = db.Column(db.Integer)
    line_Frequency = db.Column('Frequency(Hz)',db.Float)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now)
    Fkey = db.Column(db.Integer, db.ForeignKey('workstationinfo.id'),nullable=False)
    #DAQ_ExID = db.Column(db.String(10), db.ForeignKey('WorkstationInfo.DAQ_ExternalID'),nullable=False)
    def __repr__(self):
        return f"Workstation('ID:{self.WorkCellID}', 'Power:{self.Power}', 'Load:{self.Load}')"
    
    def dump_datetime(self,value):
        """Deserialize datetime object into string form for JSON processing."""
        if value is None:
            return None
        return [value.strftime("%Y-%m-%d"), value.strftime("%H:%M:%S")]
    
    @property
    def getMeasuremnts(self):
       """Return object data in easily serializable format"""
       return {
           "id":self.id,"current":self.RmsCurrent, "voltage":self.RmsVoltage, "power":self.Power,
           "NominalPower":self.Nominal_Power,"activeZones":self.ActiveZones, "load":self.Load,
           "frquency":self.line_Frequency, "timestamp":self.dump_datetime(self.timestamp)
       }

# Allbesmart---->FASToryEvents
class FASToryEvents(db.Model):
    __tablename__ = 'fastoryevents'
    id = db.Column(db.Integer, primary_key=True)
    SenderID = db.Column(db.String(15))
    Events= db.Column(db.JSON, nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now)
    Fkey = db.Column(db.Integer, db.ForeignKey('workstationinfo.id'),nullable=False)
    
    def __repr__(self):
        return f"('Events:{self.SenderID}')"
    
    def dump_datetime(self,value):
        """Deserialize datetime object into string form for JSON processing."""
        if value is None:
            return None
        return [value.strftime("%Y-%m-%d"), value.strftime("%H:%M:%S")]
    @property
    def serialize(self):
       """Return object data in easily serializable format"""
       return {
           
           'SenderID': self.SenderID,
           # This is an example how to deal with Many2Many relations
           'event'  : self.Events.get("event"),
           'timestamp' : self.dump_datetime(self.timestamp)
       }
    
    @property
    def data(self):
       """Return object data in easily serializable format"""
       return [self.SenderID,self.Events.get('event').get('id'),
                self.Events.get('event').get('payload').get('palletId'),
                self.Events.get('event').get('payload').get('Recipe'),
                self.Events.get('event').get('payload').get('PenColor'),
                self.dump_datetime(self.timestamp)]
