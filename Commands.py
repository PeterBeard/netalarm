# Commands for the alarm clock daemon
# Valid commands are:
#	ALARM <NAME> -- Triggers the alarm called NAME if it exists
#	REGISTER <KEY> <NAME> <ALARM LIST> -- Register client with name NAME and public key KEY that provides alarms in ALARM LIST
#	SUCCESS <NAME> -- Alarm NAME successfully triggered
#	FAIL <NAME> -- Alarm NAME failed

import socket

BUFFER_SIZE = 128

# Parse a command string into a command tuple
# Returns a tuple on success, None on failure
def parse_command(command_string):
	# Split on spaces and then process each command as needed
	cmd = command_string.split(' ')
	# Is it a valid command?
	if cmd[0] == 'ALARM':
		# ALARM <NAME>
		if len(cmd) == 2:
			return ('A', cmd[1])
		else:
			return None
	elif cmd[0] == 'REGISTER':
		# REGISTER <KEY> <NAME> <ALARM LIST>
		if len(cmd) == 4:
			return ('R', cmd[1], cmd[2], cmd[3])
		else:
			return None
	elif cmd[0] == 'SUCCESS':
		# SUCCESS <NAME>
		if len(cmd) == 2:
			return ('S', cmd[1])
		else:
			return None
	elif cmd[0] == 'FAIL':
		# FAIL <NAME>
		if len(cmd) == 2:
			return ('F', cmd[1])
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
			return 'ALARM ' + command[1]
		else:
			return None
	elif command[0] == 'R':
		if len(command) == 3:
			return 'REGISTER ' + command[1:].join(' ')
		else:
			return None
	elif command[0] == 'S':
		if len(command) == 2:
			return 'SUCCESS ' + command[1]
		else:
			return None
	elif command[0] == 'F':
		if len(command) == 2:
			return 'FAIL ' + command[1]
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
	sock.send(command_str)
	return True

