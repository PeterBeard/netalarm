import Commands
import Log
import socket
import signal
import sys
import time
import thread

TCP_IP = '127.0.0.1'
TCP_PORT = 26403

CLIENT_NAME = 'uglyclient'

SERVER_IP = '127.0.0.1'
SERVER_PORT = 26400

BUFFER_SIZE = 1024

# Handle SIGINT
def handle_sigint(signal, frame):
	Log.debug('Caught SIGINT, cleaning up.')
	sys.exit(0)

def listen():
	# Create a socket and listen for packets
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind((TCP_IP, TCP_PORT))
	s.listen(1)
	Log.debug('Listening on port %i' % TCP_PORT)
	# This is our main listening thread
	while True:
		# Accept incoming connection
		connection, address = s.accept()
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
	s.close()

# Handle the alarm
def dispatch_alarm(alarm_name):
	return True

# Add handler for SIGINT
signal.signal(signal.SIGINT, handle_sigint)

# How long to wait for the server to respond (s)
RESPONSE_TIMEOUT = 5

# The name of the alarm we're waiting for
ALARM_NAME = 'minuteman'

# Try to subscribe to our alarm
t = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
t.settimeout(RESPONSE_TIMEOUT)
t.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
t.bind((TCP_IP, TCP_PORT))
t.connect((SERVER_IP, SERVER_PORT))
t.send('B ' + ALARM_NAME)
Log.debug('Subscription request for alarm "%s" sent.' % ALARM_NAME)
# Receive data
command_string = t.recv(BUFFER_SIZE)
t.close()
# Print the command
Log.debug('Got response "%s"' % command_string)
# Parse the command
command = Commands.parse_command(command_string)

if command[0] == 'FB':
	Log.debug('Already subscribed to alarm "%s".' % ALARM_NAME)
elif command[0] == 'S':
	Log.debug('Successfully subscribed to alarm "%s".' % ALARM_NAME)
elif command[0] == 'FN':
	Log.error('Server says alarm "%s" does not exist.' % ALARM_NAME)
	sys.exit(1)
else:
	Log.error('Unable to parse response from server.')
	sys.exit(1)

# Listen
listen()

