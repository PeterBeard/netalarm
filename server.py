import AlarmQueue
import Alarm
import Commands
import ConfigParser
import Client
from Log import debug

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
	debug('Caught SIGINT, cleaning up...')
	debug('Done.')
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
	debug('Listening on port %i' % port)

	while True:
		# Accept incoming connection
		connection, in_address = s.accept()
		debug('Connection address: %s:%s' % (in_address[0], in_address[1]))
		# Receive data
		command_string = ''
		while True:
			data = connection.recv(BUFFER_SIZE)
			if not data:
				break
			command_string += data
		# Print the command string
		debug('Received command: %s' % command_string)
		# Close the connection from the server
		connection.close()
		# Parse the command
		command = Commands.parse_command(command_string)
		if command:
			if command[0] == 'S':
				debug('Alarm %s succeeded on client at %s' % (command[1], in_address[0]))
			elif command[0] == 'F':
				debug('Alarm %s failed on client at %s' % (command[1], in_address[0]))
			else:
				debug('Invalid command: %s' % command[0])
		else:
			debug('Invalid command.')
		
	s.close()

# Get settings from file and return a dictionary of settings
def parse_config_file(filename):
	p = ConfigParser.RawConfigParser()
	p.read(filename)
	# Build the dictionary
	settings = {}
	settings['update_interval'] = p.get('Global', 'updateperiod')
	settings['address'] = p.get('Global', 'address')
	settings['port'] = int(p.get('Global', 'port'))
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

# Create a socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Start listening
lthread = thread.start_new_thread(listening_thread, (settings['address'], settings['port']))

# Create a client
good_client = Client.Client('127.0.0.1', 26401, 'goodclient')
bad_client = Client.Client('127.0.0.1', 26402, 'badclient')

# Create a hashtable of subscriptions
subscriptions = {}

subscriptions[alarms.events[0]] = [good_client, bad_client]

# Alarm loop
while True:
	# When is the next alarm?
	alarm = alarms.peek()
	wait = alarm.wait_time()
	# If the wait is long (like, several hours long), wake up periodically to see if there's something fresher on the queue
	while wait > settings['update_interval'] * 60:
		debug('Nothing in the queue for another %i seconds. Sleeping for %i minutes before checking again.' % (wait, settings['update_interval']))
		time.sleep(settings['update_interval'] * 60)
		wait = alarm.wait_time()

	debug('Next alarm in %i seconds. Sleeping until then.' % wait)
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
					debug('Error sending command to client at %s:%i' % (client.ip, client.port))
			except socket.error:
				debug('Failed to connect to client at %s' % client.ip)
			s.close()
	# Sleep for 1 second to prevent the alarm from firing again
	time.sleep(1)
	# Stick the alarm back in the queue if it repeats
	if not alarm.once:
		alarms.enqueue(alarm)

