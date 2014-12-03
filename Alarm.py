import time
from datetime import datetime
from dateutil.relativedelta import relativedelta	# Need package python-dateutil

# The alarm class
class Alarm(object):
	# Constructor
	# self: duh
	# name: The name of the alarm (string)
	# time_tuple: Cron-like time specifier (5-tuple of strings)
	#               0: minute (0-59)
	#               1: hour (0-23)
	#               2: day of month (1-31)
	#               3: month of year (1-12)
	#               4: day of week (0-6, 0=Monday, 6=Sunday) (supercedes 2)
	def __init__(self, name, time_tuple, once = False):
		self.name = name
		# Parse the time tuple
		if len(time_tuple) == 5:
			# All values must be strings
			time_tuple = [str(t) for t in time_tuple]
			# *,*,*,*,* is not a valid time tuple
			if '*' in time_tuple[0] and '*' in time_tuple[1] and '*' in time_tuple[2] and '*' in time_tuple[3] and '*' in time_tuple[4]:
				raise ValueError('Time tuple must specify at least one time.')
			# All lower-order values must be specified (tuple must be "monotonic")
			# E.g. *, 10, *, *, * is invalid because the hours are specified but the minutes aren't
			saw_star = False
			for v in time_tuple:
				# Can't have a value if we've already seen a * UNLESS it's specifying the day of the week
				if not '*' in v and saw_star:
					if not (v == time_tuple[3] and '*' not in time_tuple[4]) and not v == time_tuple[4]:
						raise ValueError('All values with higher precision than the first specified value must also be specified.')
				elif '*' in v:
					saw_star = True
			# Remove spaces and split on commas
			times = [t.replace(' ','').split(',') for t in time_tuple]
			# Expand ranges
			times = [expand_ranges(t) for t in times]
			# Remove duplicates
			times = [list(set(t)) for t in times]
			# Sort the lists
			times = [sorted([wild_int(v) for v in t]) for t in times]
			# Use a tuple rather than a list for immutability
			self.time = tuple(times)
		else:
			raise ValueError('Time tuple must have exactly 5 elements')
		self.next_run = datetime(1970,1,1,0,0,0)
		self.calculate_next()
		self.once = once

	# Calculate the next time this alarm will run
	# Updates internal next run variable to the next time this alarm will run (datetime object)
	def calculate_next(self):
		next_time = datetime.now()
		# Do we even need to update the next run time? Only if it's in the past.
		if self.next_run < next_time:
			# Round up to the next minute
			next_time += relativedelta(microseconds=1e6-next_time.microsecond)
			next_time += relativedelta(seconds=60-next_time.second)
			# Calculate minutes
			nearest_minute = closest_time(self.time[0], next_time.minute)
			if next_time.minute > nearest_minute:
				# Add an hour
				next_time += relativedelta(hours=1)
			minutes = nearest_minute - next_time.minute
			next_time += relativedelta(minutes=minutes)
			# Calculate hours
			nearest_hour = closest_time(self.time[1], next_time.hour)
			if nearest_hour >= 0:
				if next_time.hour > nearest_hour:
					# Add a day
					next_time += relativedelta(days=1)
				hours = nearest_hour - next_time.hour
				next_time += relativedelta(hours=hours)
			# Day of week and day of month are mutually exclusive. Day of week takes precedence
			# Calculate day of month
			nearest_dow = closest_time(self.time[4], next_time.date().weekday())
			nearest_day = closest_time(self.time[2], next_time.day)
			if nearest_dow >= 0:
				# Calculate when the next x-day is
				next_time_day = next_time.date().weekday()
				if next_time_day > nearest_dow:
					# Add a week
					next_time += relativedelta(weeks=1)
				days = nearest_dow - next_time_day
				next_time += relativedelta(days=days)
			elif nearest_day >= 0:
				if next_time.day > nearest_day:
					# Add a month
					next_time += relativedelta(months=1)
				days = nearest_day - next_time.day
				next_time += relativedelta(days=days)
			# Calculate month
			nearest_month = closest_time(self.time[3], next_time.month)
			if nearest_month >= 0:
				if next_time.month > nearest_month:
					# Add a year
					next_time += relativedelta(years=1)
				months = (nearest_month - next_time.month)
				next_time += relativedelta(months=months)

			self.next_run = next_time

	# How long until this alarm is triggered
	# Return the amount of time (in seconds) until the next alarm (int)
	def wait_time(self):
		delta = self.next_run - datetime.now()
		return delta.total_seconds()
		
	# Compare two alarms
	def __cmp__(self, other):
		return cmp(self.next_run, other.next_run)

# Find the time in a list that's clostest to the given time
def closest_time(values, target):
	nearest = values[0]
	# Search through the list if it has more than one element and the last chance hasn't passed already
	if len(values) > 1 and max(values) >= target:
		for t in values:
			if nearest < target or nearest - target > t - target and t > target:
				nearest = t
	return nearest

# Expand a (closed) range to explicitly name its values (string -> [string])
def expand_ranges(values):
	new_values = values
	for i in xrange(0,len(values)):
		if '-' in values[i] and values[i] != '-1':
			boundaries = values[i].split('-')
			if len(boundaries) != 2:
				raise ValueError('Range must have exactly two endpoints')
			lower = int(boundaries[0])
			upper = int(boundaries[1])
			if upper < lower:
				raise ValueError('Range upper bound must be greater than lower bound.')
			del new_values[i]
			new_values += [str(r) for r in range(lower, upper+1)]
	return new_values

# Wrapper for int() that treats '*' as -1
def wild_int(value):
	if '*' in value:
		return -1
	return int(value)
