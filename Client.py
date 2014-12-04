# The alarm client class
class Client(object):
	# Constructor
	def __init__(self, ip, port):
		self.ip = ip
		self.port = port

	# Test equality
	def __eq__(self, other)
		return self.ip == other.ip and self.port == other.port

	# Make a nice string out of the IP and port number
	def __str__(self):
		return self.ip + ':' + str(self.port)

