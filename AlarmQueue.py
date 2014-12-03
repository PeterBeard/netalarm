# Queue of alarm events
# The queue is ordered so that the soonest event is element 0 and the latest one is last
class AlarmQueue(object):
	# Constructor
	def __init__(self):
		self.events = []

	# Look at the next event
	def peek(self):
		return self.events[0]

	# Remove the next event from the queue and return it
	def pop(self):
		e = self.events.pop(0)
		return e

	# Remove event i from the queue
	def remove(self, i):
		del self.events[i]

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
		
