import Commands
import Log

import socket
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

# Network client -- just a wrapper around a thread and a socket
class NetClient(threading.Thread):
	# Constructor
	def __init__(self, ip, port, socket):
		super(NetClient, self).__init__()
		self.ip = ip
		self.port = port
		self.socket = socket
		self.buffer_size = 1024

	# Send a command string to the client
	def send(self, command_string):
		# Send the command string
		self.socket.send(command_string)

	# Receive a command object from the client
	def receive(self):
		return Commands.parse_command(self.socket.recv(self.buffer_size))

	# Close the socket
	def close(self):
		self.socket.close()

	# Run the client -- just closes the socket since there's no logic inside this object
	def run(self):
		self.close()
		
	# Test equality
	def __eq__(self, other):
		return self.ip == other.ip and self.port == other.port

	# Make a nice string out of the IP and port number
	def __str__(self):
		return self.ip + ':' + str(self.port)

# Incoming client connection (receive then send)
class IncomingClient(NetClient):
	# Constructor
	def __init__(self, ip, port, socket, command_handler):
		super(IncomingClient, self).__init__(ip, port, socket)
		self.command_handler = command_handler

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

# Outgoing client connection (send then receive)
class OutgoingClient(NetClient):
	# Constructor
	def __init__(self, ip, port, command_handler):
		# Create a socket
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		# Initialize the object
		super(OutgoingClient, self).__init__(ip, port, s)
		self.command_to_send = None
		self.command_handler = command_handler
		
	# Get the command to send to the client and start the thread
	def send_command(self, command_string):
		self.command_to_send = command_string
		self.start()

	# Send a command to the client and return the response
	def run(self):
		if not self.command_to_send:
			Log.error('Command not set prior to send')
			return 1
		# Connect to the client
		try:
			self.socket.connect((self.ip, self.port))
		except socket.error:
			return 1
		# Send the command to the client
		self.send(self.command_to_send)
		# Receive the client's response and do something with it
		response = self.receive()
		self.close()
		self.command_handler(self, response)

