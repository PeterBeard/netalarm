import Commands
import ConfigParser
import Log
import signal
import socket
import subprocess
import sys
import time
import thread

CLIENT_NAME = 'uglyclient'

BUFFER_SIZE = 1024

CONF_FILE = 'clientsettings.conf'

# Handle SIGINT
def handle_sigint(signal, frame):
	Log.debug('Caught SIGINT, cleaning up...')
	Log.debug('Done.')
	sys.exit(0)

# Get settings from file and return a dictionary of settings
def parse_config_file(filename):
	# Use ConfigParser to handle the actual parsing of the file
	p = ConfigParser.RawConfigParser()
	p.read(filename)
	# Build the dictionary
	settings = {}

	# IP address and port to use
	settings['address'] = p.get('Global', 'address')
	settings['port'] = int(p.get('Global', 'port'))
	# Port less than 1024 is probably very unwise
	if settings['port'] < 1024:
		Log.warn('TCP port is less than 1024 (%i)' % settings['port'])
	# Server IP address and port
	settings['server_address'] = p.get('Global','server_address')
	settings['server_port'] = int(p.get('Global','server_port'))
	# Location of the alarm file
	settings['alarm_file'] = p.get('Global', 'alarmfile')

	return settings

# Load alarms to listen for and their corresponding actions
def load_alarms(filename):
	# Dictionary from alarm names -> commands
	l = {}
	# Parse the file a line at a time (comment lines start with #)
	fh = open(filename, 'r')
	for line in fh:
		if len(line.strip()) > 0 and line[0] != '#':
			# Split on spaces or tabs
			split_chars = [' ', '\t']
			found_split = False
			values = ['', []]
			for char in line.strip():
				if char not in split_chars:
					# Characters before the first split are part of the name, characters after
					# the split are part of the command
					if not found_split:
						values[0] += char
					else:
						values[1][-1] += char
				else:
					found_split = True
					if len(values[1]) == 0 or len(values[1][-1]) > 0:
						values[1].append('')
			# First value is the alarm name, second is the command
			if values[0] not in l:
				l[values[0]] = values[1]
				Log.debug('Loaded alarm "%s" => "%s"' % (values[0], ' '.join(values[1])))
			else:
				Log.warning('Multiple definitions for alarm "%s"; using first definition only.', values[0])
	fh.close()
	return l

# Listen for connections from the server and handle them
def listen(settings):
	# Create a socket and listen for packets
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.bind((settings['address'], settings['port']))
	sock.listen(1)
	Log.debug('Listening on port %i' % settings['port'])
	# This is our main listening thread
	while True:
		# Accept incoming connection
		connection, address = sock.accept()
		server = address[0] + ':' + str(address[1])
		Log.debug('Connection from %s' % server)
		# Receive data
		command_string = connection.recv(BUFFER_SIZE)
		# Print the command
		Log.debug('Received command %s from %s.' % (command_string, server))
		# Parse the command
		command = Commands.parse_command(command_string)
		response = 'E general'
		if command:
			response = Commands.create_command_string(('F', command[1]))
			# Handle the alarm
			if command[0] == 'A':
				Log.debug('Alarm %s triggered.', command[1])
				result = dispatch_alarm(command[1])
				# Success
				if result:
					response = Commands.create_command_string(('S', command[1]))
			# Invalid command
			else:
				Log.error('Invalid command "%s" from server.', command[0])
		# Invalid command
		else:
			Log.error('Invalid command from server.')
		connection.send(response)
		# Close the connection from the server
		connection.close()
	# Close the socket
	sock.close()

# Execute the command associated with this alarm and return success or failure
def dispatch_alarm(alarm_name):
	# TODO: This probably doesn't need to be a global
	global alarms
	# See if this alarm is defined
	if alarm_name in alarms:
		command = alarms[alarm_name]
		Log.debug('Alarm "%s" triggered, running command "%s"' % (alarm_name, ' '.join(command)))
		# Try to run the command in the background
		try:
			pid = subprocess.Popen(command)
		except OSError, e:
			Log.error('Command "%s" failed: %s' % (' '.join(command), str(e)))
			return False
		Log.debug('Successfully ran command "%s"' % ' '.join(command))
		return True
	# No such alarm
	else:
		Log.error('Alarm "%s" not found.' % alarm_name)
		return False

# Subscribe to all of the alarms loaded from the alarm file
# Return True on success, False on failure
def subscribe_to_alarms(alarms, settings):
	# Did we subscribe to even one alarm?
	success = False
	# Connect to the server
	t = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	t.settimeout(RESPONSE_TIMEOUT)
	t.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	t.bind((settings['address'], settings['port']))
	t.connect((settings['server_address'], settings['server_port']))

	# Ask the server to subscribe us for each alarm
	for alarm in alarms:
		command_string = Commands.create_command_string(('B', alarm))
		t.send(command_string)
		Log.debug('Subscription request for alarm "%s" sent.' % alarm)
		# Receive data
		command_string = t.recv(BUFFER_SIZE)
		# Print the command
		Log.debug('Got response "%s"' % command_string)
		# Parse the command
		command = Commands.parse_command(command_string)

		if command[0] == 'FB':
			Log.debug('Already subscribed to alarm "%s".' % alarm)
			success = True
		elif command[0] == 'S':
			Log.debug('Successfully subscribed to alarm "%s".' % alarm)
			success = True
		elif command[0] == 'FN':
			Log.error('Server says alarm "%s" does not exist.' % alarm)
		else:
			Log.error('Unable to parse response from server.')

	t.close()
	return success

# Add handler for SIGINT
signal.signal(signal.SIGINT, handle_sigint)

# How long to wait for the server to respond (s)
RESPONSE_TIMEOUT = 5

# Get settings from file
settings = parse_config_file(CONF_FILE)

# Load alarms from the file
alarms = load_alarms(settings['alarm_file'])

# Subscribe to all of our alarms
success = subscribe_to_alarms(alarms, settings)

# Couldn't subscribe to alarms; quit
if not success:
	Log.error('Failed to subscribe to any alarms; quitting.')
	sys.exit(1)

# Listen
listen(settings)

