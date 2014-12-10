import Commands
import Log

import threading

# The alarm client class
class Client(object):
	# Constructor
	def __init__(self, ip, port):
		self.ip = ip
		self.port = port

	# Test equality
	def __eq__(self, other):
		return self.ip == other.ip and self.port == other.port

	# Make a nice string out of the IP and port number
	def __str__(self):
		return self.ip + ':' + str(self.port)

# The alarm client class
class IncomingClient(threading.Thread):
	# Constructor
	def __init__(self, ip, port, socket, command_handler):
		super(IncomingClient, self).__init__()
		self.ip = ip
		self.port = port
		self.socket = socket
		self.buffer_size = 1024
		self.command_handler = command_handler

	# Send a command string to the client
	def send(self, command_string):
		# Send the command string
		self.socket.send(command_string)

	# Receive a command object from the client
	def receive(self):
		return Commands.parse_command(self.socket.recv(self.buffer_size))

	# Receive a command from the client and send a response
	def run(self):
		# Receive from the client
		command = self.receive()
		# Send the command to the handler
		response = self.command_handler(self, command)
		# Send the response (if any) to the client
		if response:
			self.send(response)
		# Close the connection
		self.close()

	# Close the socket
	def close(self):
		self.socket.close()
		
	# Test equality
	def __eq__(self, other):
		return self.ip == other.ip and self.port == other.port

	# Make a nice string out of the IP and port number
	def __str__(self):
		return self.ip + ':' + str(self.port)
