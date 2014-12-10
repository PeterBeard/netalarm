import AlarmQueue
import Alarm
import Commands
import ConfigParser
import Client
import Log

import os
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
	# Flush stdout
	sys.stdout.flush()
	# Exit
	sys.exit(0)

# Handle SIGABRT
def handle_sigabrt(signal, frame):
	Log.debug('Caught SIGABRT, cleaning up...')
	# Flush stdout
	sys.stdout.flush()
	# Exit
	sys.exit(0)

# Clean up what we can and quit
def clean_up_and_quit():
	global process_id
	Log.debug('Quitting.')
	# Abort the main thread
	os.kill(process_id, signal.SIGABRT)

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
	# Main listening thread
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		s.bind((address, port))
	except socket.error, e:
		# Can't bind to address; let's just quit then
		Log.error('Unable to bind to address %s:%i -- %s' % (address, port, str(e)))
		s.close()
		clean_up_and_quit()
		return

	s.listen(1)
	Log.debug('Listening on %s:%i' % (address, port))

	while True:
		# Accept incoming connection
		connection, in_address = s.accept()
		# Create a thread to handle this connection
		c = Client.IncomingClient(in_address[0], in_address[1], connection, handle_client_command)
		c.start()
		
	s.close()

# Do something intelligent with client commands and return an appropriate response
def handle_client_command(client, command):
	# Default response is just be quiet (i.e. no response)
	response = None
	# Was the command parsed successfully?
	if command:
		# Alarm succeeded
		if command[0] == 'S':
			Log.debug('Alarm %s succeeded on client %s' % (command[1], str(client)))
		# Alarm failed
		elif command[0] == 'F':
			Log.debug('Alarm %s failed on client %s' % (command[1], str(client)))
		# Client wants to subscribe to an alarm -- this requires a response
		elif command[0] == 'B':
			name = command[1]
			Log.debug('%s trying to subscribe to %s' % (str(client), name))
			response = add_subscription(client.ip, client.port, name)
			if response[0] == 'S':
				Log.debug('Subscription added.')
			elif response[:2] == 'FN':
				Log.debug('No such alarm.')
			elif response[:2] == 'FB':
				Log.debug('Already subscribed.')
			else:
				Log.debug('Unknown response sent (%s)' % response)
		# We don't know what to do with this command
		else:
			Log.error('Invalid command from %s: "%s"' % (str(client), command_string))
	else:
		Log.error('Invalid command from %s: "%s"' % (str(client), command_string))

	return response

# Record a client's response to an alarm
def handle_alarm_response(client, command):
	if command:
		if command[0] == 'S':
			Log.debug('Client at %s:%i indicates success.' % (client.ip, client.port))
		elif command[0] == 'F':
			Log.debug('Client at %s:%i indicates failure.' % (client.ip, client.port))
		else:
			Log.debug('Invalid response from client at %s:%i' % (client.ip, client.port))
	else:
		Log.debug('Unknown response from client at %s:%i.' % (client.ip, client.port))

# Add a subscription
def add_subscription(ip, port, alarm_name):
	# TODO: This is global and should probably not be
	global subscriptions, alarm_list
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

# Get our PID
process_id = os.getpid()

# Read the config file
settings = parse_config_file(CONF_FILE)

# Load alarms from file
(alarm_queue, alarm_list) = load_alarms(settings['alarm_file'])

# Add signal handlers
signal.signal(signal.SIGINT, handle_sigint)
signal.signal(signal.SIGABRT, handle_sigabrt)

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
			# Spin off a thread to talk to the client
			#t_handle = thread.start_new_thread(alert_client, (client, alarm))
			c = Client.OutgoingClient(client.ip, client.port, handle_alarm_response)
			c.send_command(Commands.create_command_string(('A', alarm.name)))
	else:
		Log.debug('No subscriptions to alarm "%s"' % alarm.name)
	# Sleep for 1 second to prevent the alarm from firing again
	time.sleep(1)
	# Stick the alarm back in the queue if it repeats
	if not alarm.once:
		alarm_queue.enqueue(alarm)

