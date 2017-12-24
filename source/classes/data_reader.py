#############################################################################################################################
# dart - Analyze and manipulate delimited data files.
# DataReader class
#
# Copyright © 2017 Ryan Weathers, All Rights Reserved.
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#############################################################################################################################

# ===========================================================================================================================
# Iterator for files that removes line endings and skips blank lines
class DataReader:
	# -----------------------------------------------------------------------------------------------------------------------
	# Initializes the object
	def __init__(self, f):
		self.f = f
	
	# -----------------------------------------------------------------------------------------------------------------------
	# Makes the class an iterator
	def __iter__(self):
		return self
	
	# -----------------------------------------------------------------------------------------------------------------------
	# Returns the next non-blank line
	def __next__(self):
		while True:
			line = self.f.readline()
			if line == "":
				raise StopIteration()
			else:
				line = line.strip("\r\n")
				if line != "": return line
