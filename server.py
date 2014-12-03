import AlarmQueue
import Alarm
import Commands
import Client
from Log import debug

import socket
import signal
import sys
import time
import thread

TCP_IP = '127.0.0.1'
TCP_PORT = 26400

BUFFER_SIZE = 128

# Minimum queue update period (minutes)
QUEUE_UPDATE_INTERVAL_MINUTES = 30

# Handle SIGINT
def handle_sigint(signal, frame):
	debug('Caught SIGINT, cleaning up...')
	debug('Done.')
	sys.exit(0)

# Main listening thread
def listening_thread():
	# Main listening thread
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind((TCP_IP, TCP_PORT))
	s.listen(1)
	debug('Listening on port %i' % TCP_PORT)

	while True:
		# Accept incoming connection
		connection, address = s.accept()
		debug('Connection address: %s:%s' % (address[0], address[1]))
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
				debug('Alarm %s succeeded on client at %s' % (command[1], address[0]))
			elif command[0] == 'F':
				debug('Alarm %s failed on client at %s' % (command[1], address[0]))
			else:
				debug('Invalid command: %s' % command[0])
		else:
			debug('Invalid command.')
		
	s.close()

# Add handler for SIGINT
signal.signal(signal.SIGINT, handle_sigint)

# Create a socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Start listening
lthread = thread.start_new_thread(listening_thread, ())

# Create some alarms
alarms = AlarmQueue.AlarmQueue()
# This alarm runs every so often to make sure the queue gets updated with new alarms
alarms.enqueue(Alarm.Alarm('queue_update', (QUEUE_UPDATE_INTERVAL_MINUTES,-1,-1,-1,-1)))
# Set a couple of alarms for one minute from now
now = time.localtime()
alarm1 = Alarm.Alarm('test_alarm', (now.tm_min + 1,-1,-1,-1,-1))
alarm2 = Alarm.Alarm('test_alarm_2', (now.tm_min + 1,-1,-1,-1,-1))
alarms.enqueue(alarm1)
alarms.enqueue(alarm2)

# Create a client
good_client = Client.Client('127.0.0.1', 26401, 'goodclient')
bad_client = Client.Client('127.0.0.1', 26402, 'badclient')

# Create a hashtable of subscriptions
subscriptions = {}

subscriptions[alarm1] = [good_client, bad_client]
subscriptions[alarm2] = [good_client, bad_client]

# Alarm loop
while True:
	# When is the next alarm?
	alarm = alarms.peek()
	wait = alarm.wait_time()
	# If the wait is long (like, several hours long), wake up periodically to see if there's something fresher on the queue
	while wait > QUEUE_UPDATE_INTERVAL_MINUTES * 60:
		debug('Nothing in the queue for another %i seconds. Sleeping for %i minutes before checking again.' % (wait, QUEUE_UPDATE_INTERVAL_MINUTES))
		time.sleep(QUEUE_UPDATE_INTERVAL_MINUTES * 60)
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

