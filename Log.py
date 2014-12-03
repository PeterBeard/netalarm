# Various logging functions
import time

# Display a debug message
def debug(message, logfile=None):
	tstring = time.strftime('%Y-%m-%d %H:%M:%S')
	debug_string = '[%s] %s' % (tstring, message)
	if not logfile:
		print debug_string
	else:
		pass

