import Commands
import random
import socket
import signal
import sys
import time
import thread

TCP_IP = '127.0.0.1'
TCP_PORT = 26402

CLIENT_NAME = 'client1'

SERVER_IP = '127.0.0.1'
SERVER_PORT = 26400

BUFFER_SIZE = 128

# Handle SIGINT
def handle_sigint(signal, frame):
	print 'Cleaning up.'
	s.close()
	sys.exit(0)

# Trigger an alarm
def trigger_alarm(alarm_name):
	return False

# Add handler for SIGINT
signal.signal(signal.SIGINT, handle_sigint)

# Create a socket and listen for packets
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(1)
print 'Listening on port', TCP_PORT


# This is our main listening loop
while True:
	# Accept incoming connection
	connection, address = s.accept()
	print 'Connection address:', address
	# Receive data
	command_string = ''
	while True:
		data = connection.recv(BUFFER_SIZE)
		if not data:
			break
		command_string += data
	# Print the command string
	print 'Received command: ' + command_string
	# Close the connection from the server
	connection.close()
	# Parse the command
	command = Commands.parse_command(command_string)
	print 'Parsed:', command
	if command:
		# If the command is an alarm, handle it
		if command[0] == 'A':
			success = trigger_alarm(command[1])
			# Tell the server we succeeded
			if success:
				response = Commands.create_command_string(('S', command[1]))
			else:
				response = Commands.create_command_string(('F', command[1]))
			# Tell the server whether the alarm fired or not
			t = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			t.connect((SERVER_IP, SERVER_PORT))
			t.send(response)
			t.close()
			print 'Sent response: ' + response
	else:
		print 'Invalid command.'
# Close the socket
s.close()

