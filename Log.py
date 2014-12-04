# Various logging functions
import time

# Prepend a nice datetime string
def prepend_datetime(string):
	t = time.strftime('%Y-%m-%d %H:%M:%S')
	return '[%s] %s' % (t, string)

# Display a debug message
def debug(message, logfile=None):
	debug_string = prepend_datetime(message)
	# Log the message
	if not logfile:
		print debug_string
	else:
		pass

# Log a warning
def warn(message, logfile=None):
	warning_string = '(WARN) ' + message
	warning_string = prepend_datetime(warning_string)
	# Log the message
	if not logfile:
		print warning_string
	else:
		pass

# Log an error
def error(message, logfile=None):
	err_string = '(ERR!) ' + message
	err_string = prepend_datetime(err_string)
	# Log the message
	if not logfile:
		print err_string
	else:
		pass
