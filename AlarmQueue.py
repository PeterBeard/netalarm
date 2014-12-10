# Queue of alarm events
# The queue is ordered so that the soonest event is element 0 and the latest one is last
class AlarmQueue(object):
	# Constructor
	def __init__(self):
		self.events = []
		self.names = []

	# Look at the next event
	def peek(self):
		return self.events[0]

	# Remove the next event from the queue and return it
	def pop(self):
		e = self.events.pop(0)
		self.reload_names()
		return e

	# Remove event i from the queue
	def remove(self, i):
		del self.events[i]
		self.reload_names()

	# Add an event to the queue
	def enqueue(self, event):
		# Calculate the next time the event will occur
		event.calculate_next()
		# Insert it in the right place
		index = 0
		if len(self.events) > 0:
			for e in self.events:
				if e <= event:
					index += 1
				else:
					break
		# Insert
		self.events.insert(index, event)
		# Regenerate names list
		self.reload_names()

	# Generate a list of names of the events in the queue
	def reload_names(self):
		# Each name only needs to be listed once; remove duplicates
		self.names = list(set([e.name for e in self.events]))

	# Make a nice string out of all the alarms in the queue - 1 per line
	def __str__(self):
		string = ''
		for e in self.events:
			string += str(e) + '\n'
		return string

	# Return the number of items in the queue
	def __len__(self):
		return len(self.events)

