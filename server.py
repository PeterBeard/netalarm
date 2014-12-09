import AlarmQueue
import Alarm
import Commands
import ConfigParser
import Client
import Log

import socket
import signal
import sys
import time
import thread

BUFFER_SIZE = 1024
#CONF_FILE = '/etc/netalarm/settings.conf'
CONF_FILE = 'settings.conf'

# Handle SIGINT
def handle_sigint(signal, frame):
	Log.debug('Caught SIGINT, cleaning up...')
	Log.debug('Done.')
	sys.exit(0)

# Load alarms from a file
# Return an AlarmQueue object and a list of the names of the alarms loaded
def load_alarms(filename):
	q = AlarmQueue.AlarmQueue()
	l = []
	# Open the file and parse each non-comment line
	fh = open(filename, 'r')
	for line in fh:
		if len(line.strip()) > 0 and line[0] != '#':
			# Try to parse this line into an Alarm object
			try:
				a = Alarm.parse_alarm_string(line)
			except ValueError, e:
				Log.warn('Unable to parse alarm "%s": %s' % (line.strip(), str(e)))
			else:
				q.enqueue(a)
				l.append(a.name)
	fh.close()
	return (q, l)
	
# Main listening thread
def listening_thread(address, port, alarm_list):
	# TODO: This is global and should probably not be
	global subscriptions
	# Main listening thread
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind((address, port))
	s.listen(1)
	Log.debug('Listening on %s:%i' % (address, port))

	while True:
		# Accept incoming connection
		connection, in_address = s.accept()
		# We'll always refer to the client by ip and port, so this saves some space
		client = in_address[0] + ':' + str(in_address[1])
		Log.debug('Connection from client %s' % client)
		# Receive data
		command_string = connection.recv(BUFFER_SIZE)
		# Print the command string
		Log.debug('Received command %s from %s' % (command_string, client))
		# Parse the command
		command = Commands.parse_command(command_string)
		# Default response
		response = 'F general'
		if command:
			# Alarm succeeded
			if command[0] == 'S':
				Log.debug('Alarm %s succeeded on client %s' % (command[1], client))
			# Alarm failed
			elif command[0] == 'F':
				Log.debug('Alarm %s failed on client %s' % (command[1], client))
			# Client wants to subscribe to an alarm
			elif command[0] == 'B':
				name = command[1]
				Log.debug('%s trying to subscribe to %s' % (client, name))
				response = add_subscription(in_address[0], in_address[1], name, alarm_list)
				if response[0] == 'S':
					Log.debug('Subscription added.')
				elif response[:2] == 'FN':
					Log.debug('No such alarm.')
				elif response[:2] == 'FB':
					Log.debug('Already subscribed.')
				else:
					Log.debug('Unknown response sent (%s)' % response)
			else:
				Log.error('Invalid command from %s: "%s"' % (client, command_string))
		else:
			Log.error('Invalid command from %s: "%s"' % (client, command_string))
		# Respond to the client
		connection.send(response)
		connection.close()
		
	s.close()

# Add a subscription
def add_subscription(ip, port, alarm_name, alarm_list):
	# TODO: This is global and should probably not be
	global subscriptions
	# Does the alarm exist
	if alarm_name not in alarm_list:
		return Commands.create_command_string(('FN', alarm_name))
	# Try to add the subscription
	client_obj = Client.Client(ip, port)
	if alarm_name in alarm_list:
		if alarm_name in subscriptions:
			# Already subscribed
			if any(c for c in subscriptions[alarm_name] if c == client_obj):
				return Commands.create_command_string(('FB', alarm_name))
			else:
				subscriptions[alarm_name].append(client_obj)
		else:
			subscriptions[alarm_name] = [client_obj]
	# Tell the client they've been added to the list
	return Commands.create_command_string(('S', alarm_name))

# Get settings from file and return a dictionary of settings
def parse_config_file(filename):
	# Use ConfigParser to handle the actual parsing of the file
	p = ConfigParser.RawConfigParser()
	p.read(filename)
	# Build the dictionary
	settings = {}

	# Update interval
	settings['update_interval'] = int(p.get('Global', 'updateperiod'))
	# Maximum update interval is 1 hour. Obviously, it has to be positive too.
	if settings['update_interval'] > 60 or settings['update_interval'] < 1:
		Log.warn('Changed queue update interval to 60 from %s' % settings['update_interval'])
		settings['update_interval'] = 60

	# IP address and port to use
	settings['address'] = p.get('Global', 'address')
	settings['port'] = int(p.get('Global', 'port'))
	# Port less than 1024 is probably very unwise
	if settings['port'] < 1024:
		Log.warn('TCP port is less than 1024 (%i)' % settings['port'])
	# Location of the alarm file
	settings['alarm_file'] = p.get('Global', 'alarmfile')

	return settings

# Read the config file
settings = parse_config_file(CONF_FILE)

# Load alarms from file
(alarm_queue, alarm_list) = load_alarms(settings['alarm_file'])

# Add handler for SIGINT
signal.signal(signal.SIGINT, handle_sigint)

# Create a hashtable of subscriptions
subscriptions = {}

# Start listening
lthread = thread.start_new_thread(listening_thread, (settings['address'], settings['port'], alarm_list))

# Create a socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Alarm loop
while True:
	if len(alarm_queue) > 0:
		# When is the next alarm?
		alarm = alarm_queue.peek()
		wait = alarm.wait_time()
	else:
		wait = 0
	# If the wait is long (like, several hours long), wake up periodically to see if there's something fresher on the queue
	# This is also all we can do if the queue is empty
	while len(alarm_queue) == 0 or wait > settings['update_interval'] * 60:
		if len(alarm_queue) == 0:
			Log.debug('Alarm queue is empty. Re-checking in %i mins.' % settings['update_interval'])
		else:
			Log.debug('Next alarm not for %i seconds. Re-checking in %i mins.' % (wait, settings['update_interval']))
		# zzz
		time.sleep(settings['update_interval'] * 60)
		# Reload the alarm file
		(alarm_queue, alarm_list) = load_alarms(settings['alarm_file'])
		# See how long we'll have to wait now
		if len(alarm_queue) > 0:
			alarm = alarm_queue.peek()
			wait = alarm.wait_time()

	Log.debug('Next alarm in %i seconds. Sleeping until then.' % wait)
	# If two alarms occur at the same time, wait will be zero or negative.
	# No point in sleeping if that's the case.
	if wait > 0:
		time.sleep(wait)
	# Remove the alarm from the queue
	alarm = alarm_queue.pop()
	# If anybody cares about this alarm, alert them
	if alarm.name in subscriptions:
		clients = subscriptions[alarm.name]
		Log.debug('Alerting %i clients about alarm "%s"' % (len(clients), alarm.name))
		# Notify all subscribed clients
		for client in clients:
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			cmd_success = False
			try:
				cmd_success = Commands.send_alarm(s, alarm.name, client.ip, client.port)
				if not cmd_success:
					Log.debug('Error sending command to client at %s:%i' % (client.ip, client.port))
				else:
					Log.debug('Client at %s:%i indicates success.' % (client.ip, client.port))
			except socket.error:
				Log.debug('Failed to connect to client at %s:%i' % (client.ip, client.port))
			s.close()
	else:
		Log.debug('No subscriptions to alarm "%s"' % alarm.name)
	# Sleep for 1 second to prevent the alarm from firing again
	time.sleep(1)
	# Stick the alarm back in the queue if it repeats
	if not alarm.once:
		alarm_queue.enqueue(alarm)

