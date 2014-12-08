# Commands for the alarm clock daemon
# Valid commands are:
#	A <NAME>  -- Triggers the alarm called NAME if it exists
#	B <NAME>  -- Subscribe client to alarm NAME
#	S <NAME>  -- Alarm NAME successfully triggered OR subscription to NAME registered
#	F <NAME>  -- Alarm NAME failed
#	FB <NAME> -- Subscription to NAME failed because client is already subscribed to this alarm
#	FN <NAME> -- Subscription to NAME failed because it does not exist

import socket

BUFFER_SIZE = 1024

# Parse a command string into a command tuple
# Returns a tuple on success, None on failure
def parse_command(command_string):
	# Split on spaces and then process each command as needed
	cmd = command_string.split(' ')
	# Is it a valid command?
	if cmd[0] == 'A':
		# A <NAME>
		if len(cmd) == 2:
			return ('A', cmd[1])
		else:
			return None
	elif cmd[0] == 'B':
		# B <NAME>
		if len(cmd) == 2:
			return ('B', cmd[1])
		else:
			return None
	elif cmd[0] == 'S':
		# S <NAME>
		if len(cmd) == 2:
			return ('S', cmd[1])
		else:
			return None
	elif cmd[0] == 'F':
		# F <NAME>
		if len(cmd) == 2:
			return ('F', cmd[1])
		else:
			return None
	elif cmd[0] == 'FN':
		# FN <NAME>
		if len(cmd) == 2:
			return ('FN', cmd[1])
		else:
			return None
	elif cmd[0] == 'FB':
		if len(cmd) == 2:
			return ('FB', cmd[1])
		else:
			return None
	else:
		return None

# Create a command string from a command tuple
# Returns a string on success, None on failure
def create_command_string(command):
	# Create the string
	if command[0] == 'A':
		if len(command) == 2:
			return 'A ' + command[1]
		else:
			return None
	elif command[0] == 'B':
		if len(command) == 2:
			return 'B ' + command[1:].join(' ')
		else:
			return None
	elif command[0] == 'S':
		if len(command) == 2:
			return 'S ' + command[1]
		else:
			return None
	elif command[0] == 'F':
		if len(command) == 2:
			return 'F ' + command[1]
		else:
			return None
	elif command[0] == 'FN':
		if len(command) == 2:
			return 'FN ' + command[1]
		else:
			return None
	elif command[0] == 'FB':
		if len(command) == 2:
			return 'FB ' + command[1]
		else:
			return None
	else:
		return None

# Send an alarm command to a client
# Returns True on success and False on failure
def send_alarm(sock, alarm_name, client_ip, client_port):
	# Try to open a connection to the client
	try:
		sock.connect((client_ip, client_port))
	except socket.error:
		return False
	# Create a command string
	command_str = create_command_string(('A', alarm_name))
	# Send the command string
	sock.send(command_str)
	# Wait for a response
	response = parse_command(sock.recv(BUFFER_SIZE))
	# Return true on success, false on failure or error
	if response:
		if response[0] == 'S':
			return True
		else:
			return False
	else:
		return False

