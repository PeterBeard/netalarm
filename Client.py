import Alarm

# The alarm client class
class Client(object):
	# Constructor
	def __init__(self, ip, port, name):
		self.ip = ip
		self.port = port
		self.name = name
	
	# Add an alarm
	def add_alarm(self, alarm):
		self.alarms.append(Alarm.Alarm(alarm, ''))

	# Check to see if we have any alarms to trigger
	def triggered_alarms(self, time):
		triggered = []
		for alarm in self.alarms:
			if not alarm.triggered:
				alarm.triggered = True
				triggered.append(alarm)
		return triggered
