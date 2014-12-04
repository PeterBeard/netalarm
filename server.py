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

BUFFER_SIZE = 128
#CONF_FILE = '/etc/netalarm/settings.conf'
CONF_FILE = 'settings.conf'

# Handle SIGINT
def handle_sigint(signal, frame):
	Log.debug('Caught SIGINT, cleaning up...')
	Log.debug('Done.')
	sys.exit(0)

# Load alarms from a file
def load_alarms(filename):
	q = AlarmQueue.AlarmQueue()
	# Open the file and parse each non-comment line
	fh = open(filename, 'r')
	for line in fh:
		if len(line.strip()) > 0 and line[0] != '#':
			q.enqueue(Alarm.parse_alarm_string(line))
	fh.close()
	return q
	

# Check the alarm file for new alarms
def update_alarm_queue(queue, alarm_file):
	pass

# Main listening thread
def listening_thread(address, port):
	# Main listening thread
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind((address, port))
	s.listen(1)
	Log.debug('Listening on %s:%i' % (address, port))

	while True:
		# Accept incoming connection
		connection, in_address = s.accept()
		# We'll always refer to the client by ip and port, so this saves some space
		client = in_address[0] + ':' + in_address[1]
		Log.debug('Connection from client %s' % client)
		# Receive data
		command_string = ''
		while True:
			data = connection.recv(BUFFER_SIZE)
			if not data:
				break
			command_string += data
		# Print the command string
		Log.debug('Received command %s from %s' % (command_string, client))
		# Close the connection from the server
		connection.close()
		# Parse the command
		command = Commands.parse_command(command_string)
		if command:
			if command[0] == 'S':
				Log.debug('Alarm %s succeeded on client %s' % (command[1], client))
			elif command[0] == 'F':
				Log.debug('Alarm %s failed on client %s' % (command[1], client))
			else:
				Log.error('Invalid command: %s from %s' % (command[0], client))
		else:
			Log.error('Empty command from %s' % client)
		
	s.close()

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
alarms = load_alarms(settings['alarm_file'])
# This alarm runs every so often to make sure the queue gets updated with new alarms
alarms.enqueue(Alarm.Alarm('queue_update', (settings['update_interval'],-1,-1,-1,-1)))

# Add handler for SIGINT
signal.signal(signal.SIGINT, handle_sigint)

# Start listening
lthread = thread.start_new_thread(listening_thread, (settings['address'], settings['port']))

# Create a client
good_client = Client.Client('127.0.0.1', 26401, 'goodclient')
bad_client = Client.Client('127.0.0.1', 26402, 'badclient')

# Create a hashtable of subscriptions
subscriptions = {}
subscriptions[alarms.events[0]] = [good_client, bad_client]

# Create a socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Alarm loop
while True:
	# When is the next alarm?
	alarm = alarms.peek()
	wait = alarm.wait_time()
	# If the wait is long (like, several hours long), wake up periodically to see if there's something fresher on the queue
	while wait > settings['update_interval'] * 60:
		Log.debug('Nothing in the queue for another %i seconds. Sleeping for %i minutes before checking again.' % (wait, settings['update_interval']))
		time.sleep(settings['update_interval'] * 60)
		wait = alarm.wait_time()

	Log.debug('Next alarm in %i seconds. Sleeping until then.' % wait)
	# If two alarms occur at the same time, wait will be zero or negative.
	# No point in sleeping if that's the case.
	if wait > 0:
		time.sleep(wait)
	# Remove the alarm from the queue
	alarm = alarms.pop()
	# If anybody cares about this alarm, alert them
	if alarm in subscriptions:
		clients = subscriptions[alarm]
		# Notify all subscribed clients
		for client in clients:
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			cmd_success = False
			try:
				cmd_success = Commands.send_alarm(s, alarm.name, client.ip, client.port)
				if not cmd_success:
					Log.debug('Error sending command to client at %s:%i' % (client.ip, client.port))
			except socket.error:
				Log.debug('Failed to connect to client at %s' % client.ip)
			s.close()
	# Sleep for 1 second to prevent the alarm from firing again
	time.sleep(1)
	# Stick the alarm back in the queue if it repeats
	if not alarm.once:
		alarms.enqueue(alarm)

