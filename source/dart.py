#! /usr/bin/python3

"""Analyze and manipulate delimited data files."""

#############################################################################################################################
# dart
#
# Copyright © 2017, 2018, 2019, 2020, 2021 Ryan Weathers, All Rights Reserved.
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
#
# Version: 0.6.0-beta (2021.04.03)
#############################################################################################################################

import os
import re
import shutil
import sys
import time
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from hydra import *

program = {
	"name"     :"dart",
	"version"  :"0.6.0-beta",
	"date"     :"04/03/2021",
	"purpose"  :"Analyze and manipulate delimited data files.",
	"url"      :"https://github.com/rweathers/dart",
	"copyright":"Copyright © 2017, 2018, 2019, 2020, 2021 Ryan Weathers, All Rights Reserved.",
	"license"  :"This program is free software: you can redistribute it and/or modify\nit under the terms of the GNU General Public License as published by\nthe Free Software Foundation, either version 3 of the License, or\n(at your option) any later version.\n\nThis program is distributed in the hope that it will be useful,\nbut WITHOUT ANY WARRANTY; without even the implied warranty of\nMERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\nGNU General Public License for more details.\n\nYou should have received a copy of the GNU General Public License\nalong with this program.  If not, see <http://www.gnu.org/licenses/>.",
	"config"   :"{path}dart.ini",
	"error"    :"{path}dart.err"
}

class Configuration(BaseConfiguration):
	"""Class for loading and validating configuration files."""
	pass

class Action(BaseAction):
	"""Base Action class."""
	
	def standardize(self):
		"""Standardize the user's inputs."""
		
		# Standardize action name
		self.inputs["action"] = self.inputs["action"].lower().replace(" ", "-")
		
		# Convert column to int and change to zero-based
		if self.inputs["action"] in ["filter", "replace-pattern", "replace-value", "split-value"]:
			try:
				self.inputs["column"] = int(self.inputs["column"]) - 1
			except ValueError as e:
				pass
			
		# Convert columns to a list of ints and change to zero-based
		if self.inputs["action"] in ["remove-columns"]:
			try:
				self.inputs["columns"] = self.inputs["columns"].replace(" ", "")
				if self.inputs["columns"] == "":
					self.inputs["columns"] = []
				else:
					columns = self.inputs["columns"].split(",")
					self.inputs["columns"] = []
					for i in range(len(columns)):
						if "-" in columns[i]:
							(x, y) = columns[i].split("-")
							for j in range(int(x)-1, int(y)): self.inputs["columns"].append(j)
						else:
							self.inputs["columns"].append(int(columns[i])-1)
					self.inputs["columns"].sort(reverse=True)
			except ValueError as e:
				self.inputs["columns"] = None
			
		# Convert lines to int
		if self.inputs["action"] in ["analyze", "head", "split-lines", "sql-import"]:
			if (self.inputs["action"] in ["analyze", "sql-import"]) and (self.inputs["lines"] == ""): self.inputs["lines"] = 0
			try:
				self.inputs["lines"] = int(self.inputs["lines"])
			except ValueError as e:
				pass
		
		# Convert wildcards to a list of filenames
		self.expand("input")
	
		# Convert \t delim to an actual tab
		if self.inputs["delim"] == "\\t": self.inputs["delim"] = "\t"
	
	def validate(self):
		"""Raise an exception if any of the user's inputs are invalid."""
		
		errors = []
		
		if self.inputs["action"] == "": errors.append("Action required.")
		
		# Validate column
		if self.inputs["action"] in ["filter", "replace-pattern", "replace-value", "split-value"]:
			try:
				if not isinstance(self.inputs["column"], int): raise Exception()
				if self.inputs["column"] < 0: raise Exception()
			except Exception as e:
				errors.append("Column must be a positive integer.")
			
		# Validate columns
		if self.inputs["action"] in ["remove-columns"]:
			try:
				if self.inputs["columns"] is None: raise Exception()
				for i in self.inputs["columns"]:
					if i < 0: raise Exception()
			except Exception as e:
				errors.append("Columns must be a comma separated list of positive integers.")
		
		# Validate lines
		if self.inputs["action"] in ["analyze", "sql-import"]:
			try:
				if not isinstance(self.inputs["lines"], int): raise Exception()
				if self.inputs["lines"] < 0: raise Exception()
			except Exception as e:
				errors.append("If supplied, lines must be a positive integer.")
		elif self.inputs["action"] in ["head", "split-lines"]:
			try:
				if not isinstance(self.inputs["lines"], int): raise Exception()
				if self.inputs["lines"] <= 0: raise Exception()
			except Exception as e:
				errors.append("Lines must be a positive integer.")
		
		if len(self.inputs["input"]) == 0: errors.append("Input file(s) required.")
		
		if (self.inputs["action"] not in ["split-lines", "split-value"]) and (self.inputs["output"] == ""): errors.append("Output file required.")
		
		if (self.inputs["action"] in ["delim-to-fixed", "fixed-to-delim"]) and (self.inputs["definition"] == ""): errors.append("Definition file required.")
		
		if self.inputs["encoding"] == "": errors.append("File encoding required.")
		
		if errors: raise Exception("\n".join(errors))
	
	def parse_data(self, record, delim=",", enclose="\"", escape="\""):
		"""Parse a delimited string into a list and return it."""
		
		ret = []
		value = ""
		i=0
		char = peek = ""
		in_field = False
		enclosed = False
		while(i < len(record)):
			# Get the current and next characters, ignore spaces if not in field
			if(in_field or (not in_field and (record[i:i+1] != " "))):
				char = record[i:i+1]
				peek = ""
				if i+1 < len(record): peek = record[i+1:i+2]
				
				# Determine what the current character is and what to do with it
				if in_field and enclosed:
					if (char == escape) and (peek == enclose):
						# Escaped enclose character
						value += peek
						i += 1
					elif char == enclose:
						# End of field
						ret.append(value.strip())
						value = ""
						in_field = False
						enclosed = False
						
						# Skip to the delim character
						while (i < len(record)) and (record[i:i+1] != delim):
							i += 1
							char = record[i:i+1]
					else:
						# Part of the field
						value += char
				elif in_field and not enclosed:
					if char == delim:
						# End of field
						ret.append(value.strip())
						value = ""
						in_field = False
						enclosed = False
					else:
						# Part of the field
						value += char
				elif not in_field:
					if char == enclose:
						# Starting an enclosed field
						in_field = True
						enclosed = True
					elif char == delim:
						# Ending an empty field
						ret.append("")
					elif char != " ":
						# Starting an unenclosed field
						value += char
						in_field = True
						enclosed = False
			i += 1
		
		# Get the last field if necessary
		if in_field or (char == delim): ret.append(value.strip())
		
		return ret
	
	def unparse_data(self, record, delim=",", enclose="\"", escape="\""):
		"""Unparse a list into a delimited string and return it."""
		
		ret = []
		if enclose == "": escape = ""
		for r in record: ret.append(enclose + str(r).replace(enclose, escape + enclose) + enclose)
		return delim.join(ret)

class AnalyzeAction(Action):
	"""Class to perform actions that analyze the full file and output something besides the original data."""
	
	def action(self):
		"""Perform the task and return a message for the user."""
		
		total_bytes = 0
		for filename in self.inputs["input"]: total_bytes += 0 if filename == "STDIN" else os.path.getsize(filename)
		
		# Define common date and time formats
		date_formats = [
			"%Y-%m-%d",
			"%m/%d/%Y", "%d-%m-%Y", "%d.%m.%Y", "%d %B %Y", "%B %d, %Y", "%d %b %Y", "%b %d, %Y", "%d-%B-%Y", "%d-%b-%Y",
			"%m/%d/%y", "%d-%m-%y", "%d.%m.%y", "%d %B %y", "%B %d, %y", "%d %b %y", "%b %d, %y", "%d-%B-%y", "%d-%b-%y"
		]
		time_formats = ["%H:%M", "%H:%M:%S", "%I:%M %p", "%I:%M:%S %p"]
		datetime_formats = []
		for d in date_formats:
			for t in time_formats:
				datetime_formats.append("{} {}".format(d, t))
		
		# Loop over input files
		b = i = f = 0
		started = time.time()
		for input_filename in self.inputs["input"]:
			linesep = None
			
			# Get/format output filename
			(name, ext) = os.path.splitext(os.path.basename(input_filename))
			output_filename = self.inputs["output"].format(f=name, e=ext)
			
			# Require input/output to be different
			if os.path.normcase(os.path.normpath(input_filename)) == os.path.normcase(os.path.normpath(output_filename)): raise Exception("Input and output files cannot be the same.")
			
			# Require each input to have its own output
			if (len(self.inputs["input"]) > 1) and (self.inputs["output"] == output_filename): raise Exception("Each file must have its own output. Use {f} and {e}.")
			
			# Analyze the input file
			fields = []
			j = 0
			f_in = self.open(input_filename, "r", self.inputs["encoding"])
			try:
				headers = self.inputs["headers"]
				l = 0
				reader = DataReader(f_in)
				for line in reader:
					b += len(line.encode(self.inputs["encoding"])) + len(reader.linesep)
					if linesep is None: linesep = reader.linesep
					
					# Parse the data
					record = self.parse_data(line, self.inputs["delim"], self.inputs["enclose"], self.inputs["escape"])
					
					# Initialize the field information
					if (l == 0):
						k = 0
						for value in record:
							field = {
								"name":value if headers else "field-{}".format(k),
								
								"length-min":None,
								"length-avg":0,
								"length-max":None,
								
								"text-min":None,
								"text-max":None,
								
								"integer":True,
								"integer-min":None,
								"integer-avg":0,
								"integer-max":None,
								
								"decimal":True,
								"decimal-min":None,
								"decimal-avg":0.0,
								"decimal-max":None,
								
								"date":True,
								"date-format":None,
								"date-min":None,
								"date-max":None,
								
								"time":True,
								"time-format":None,
								"time-min":None,
								"time-max":None,
								
								"datetime":True,
								"datetime-format":None,
								"datetime-min":None,
								"datetime-max":None,
								
								"boolean":True,
								
								"empty":0,
								"null":0,
								
								"values":{}
							}
							fields.append(field)
							k += 1
							
					# Process the record
					if not headers:
						k = 0
						for value in record:
							if value == "":
								fields[k]["empty"] += 1
							elif (value == "NULL") or (value == "\\N"):
								fields[k]["null"] += 1
							else:
								d = fields[k]
								d["length-min"] = len(value) if d["length-min"] is None else min(len(value), d["length-min"])
								d["length-avg"] += len(value)
								d["length-max"] = len(value) if d["length-max"] is None else max(len(value), d["length-max"])
								
								d["text-min"] = value if d["text-min"] is None else min(value, d["text-min"])
								d["text-max"] = value if d["text-max"] is None else max(value, d["text-max"])
								
								if d["integer"]:
									try:
										if (value != "0") and re.search("^0", value): raise Exception()
										if re.search("\.", value): raise Exception()
										
										val = int(value)
										d["integer-min"] = val if d["integer-min"] is None else int(min(val, d["integer-min"]))
										d["integer-avg"] += val
										d["integer-max"] = val if d["integer-max"] is None else int(max(val, d["integer-max"]))
									except Exception as e:
										d["integer"] = False
								
								if d["decimal"]:
									try:
										if re.search("^0[^\\.]", value): raise Exception()
										
										val = float(value)
										d["decimal-min"] = val if d["decimal-min"] is None else min(val, d["decimal-min"])
										d["decimal-avg"] += val
										d["decimal-max"] = val if d["decimal-max"] is None else max(val, d["decimal-max"])
									except Exception as e:
										d["decimal"] = False
								
								def dt_helper(key, formats):
									if d[key]:
										val = None
										formats = [d["{}-format".format(key)]] if d["{}-format".format(key)] is not None else formats
										for format in formats:
											try:
												val = datetime.strptime(value, format)
												d["{}-format".format(key)] = format
												break
											except Exception as e:
												pass
												
										if val is not None:
											if (d["{}-min".format(key)] is None) or (val < datetime.strptime(d["{}-min".format(key)], d["{}-format".format(key)])): d["{}-min".format(key)] = value
											if (d["{}-max".format(key)] is None) or (val > datetime.strptime(d["{}-max".format(key)], d["{}-format".format(key)])): d["{}-max".format(key)] = value
										else:
											d[key] = False
								
								dt_helper("date"    , date_formats)
								dt_helper("time"    , time_formats)
								dt_helper("datetime", datetime_formats)
								
								if d["boolean"]:
									try:
										if value not in ["0", "1", "Y", "N", "y", "n", "Yes", "No", "YES", "NO", "yes", "no", "T", "F", "True", "False", "TRUE", "FALSE", "true", "false"]: raise Exception()
									except Exception as e:
										d["boolean"] = False
								
								if value not in d["values"]: d["values"][value] = 0
								d["values"][value] += 1
							
							k += 1
					
					if not headers:
						j += 1
						i += 1
					
					if headers: headers = False
					
					l += 1
					
					if (self.inputs["lines"] > 0) and (j >= self.inputs["lines"]): break
					
					if self.inputs["lines"] > 0:
						self.progress("Record: {}".format(i), started, i, self.inputs["lines"] * len(self.inputs["input"]))
					else:
						self.progress("Record: {}".format(i), started, b, total_bytes)
					
				# Clean up entirely empty fields
				for field in fields:
					if (field["empty"] + field["null"]) == j:
						field["length-min"] = 0
						field["length-max"] = 0
						field["text-min"] = ""
						field["text-max"] = ""
						field["integer"] = False
						field["decimal"] = False
						field["date"] = False
						field["time"] = False
						field["datetime"] = False
						field["boolean"] = False
						
			finally:
				if f_in != sys.stdin: f_in.close()
			
			# Create output file contents
			results = ""
			if j > 0:
				if self.inputs["action"] == "analyze":
					data = [
						["Column Name"],
						["Data Type"],
						["Minimum Length"],
						["Average Length"],
						["Maximum Length"],
						["Minimum Value"],
						["Average Value"],
						["Maximum Value"],
						["Empty Values"],
						["Distinct Values"],
						["Total Values"]
					]
					
					for field in fields:
						x = 0
						
						# Column Name
						data[x].append(field["name"])
						x += 1
						
						# Data Type
						if field["boolean"]:
							data[x].append("Boolean")
						elif field["integer"]:
							data[x].append("Integer")
						elif field["decimal"]:
							data[x].append("Decimal")
						elif field["date"]:
							data[x].append("Date")
						elif field["time"]:
							data[x].append("Time")
						elif field["datetime"]:
							data[x].append("Date/Time")
						else:
							data[x].append("Text")
						x += 1
						
						# Minimum Length
						data[x].append(field["length-min"])
						x += 1
						
						# Average Length
						data[x].append(0 if (j - field["empty"] - field["null"]) == 0 else round(field["length-avg"]/(j - field["empty"] - field["null"]), 1))
						x += 1
						
						# Maximum Length
						data[x].append(field["length-max"])
						x += 1
						
						if field["integer"]:
							# Minimum Value
							data[x].append(field["integer-min"])
							x += 1
							
							# Average Value
							data[x].append("" if (j - field["empty"] - field["null"]) == 0 else round(field["integer-avg"]/(j - field["empty"] - field["null"]), 1))
							x += 1
							
							# Maximum Value
							data[x].append(field["integer-max"])
							x += 1
						elif field["decimal"]:
							# Minimum Value
							data[x].append(field["decimal-min"])
							x += 1
							
							# Average Value
							data[x].append(field["decimal-avg"]/j)
							x += 1
							
							# Maximum Value
							data[x].append(field["decimal-max"])
							x += 1
						elif field["date"]:
							# Minimum Value
							data[x].append(field["date-min"])
							x += 1
							
							# Average Value
							data[x].append("")
							x += 1
							
							# Maximum Value
							data[x].append(field["date-max"])
							x += 1
						elif field["time"]:
							# Minimum Value
							data[x].append(field["time-min"])
							x += 1
							
							# Average Value
							data[x].append("")
							x += 1
							
							# Maximum Value
							data[x].append(field["time-max"])
							x += 1
						elif field["datetime"]:
							# Minimum Value
							data[x].append(field["datetime-min"])
							x += 1
							
							# Average Value
							data[x].append("")
							x += 1
							
							# Maximum Value
							data[x].append(field["datetime-max"])
							x += 1
						else:
							# Minimum Value
							data[x].append(field["text-min"])
							x += 1
							
							# Average Value
							data[x].append("")
							x += 1
							
							# Maximum Value
							data[x].append(field["text-max"])
							x += 1
						
						# Empty Values
						data[x].append(field["empty"] + field["null"])
						x += 1
						
						# Distinct Values
						data[x].append(len(field["values"]) + int(field["empty"] > 0) + int(field["null"] > 0))
						x += 1
						
						# Total Values
						data[x].append(j)
						x += 1
					
					for record in data: results += self.unparse_data(record, self.inputs["delim"], self.inputs["enclose"], self.inputs["escape"]) + "\n"
					
				elif self.inputs["action"] == "sql-import":
					# Get table name from filename
					table_name = "tbl"
					if input_filename != "STDIN":
						table_name = name.strip().lower()
						table_name = re.sub("[ -]+", "_", table_name)
						table_name = re.sub("[^A-Za-z0-9_]+", "", table_name)
					
					# Integer storage bits
					integer_storage_bits = {"TINYINT":8, "SMALLINT":16, "MEDIUMINT":24, "INT":32, "BITINT":64}
					
					# Create column definitions
					columns = []
					for field in fields:
						column_name = field["name"].strip().lower()
						column_name = re.sub("[ -]+", "_", column_name)
						column_name = re.sub("[^A-Za-z0-9_]+", "", column_name)
						
						null = "NULL" if field["null"] > 0 else "NOT NULL"
						
						datatype = None
						if (field["boolean"]) and (sorted(list(field["values"].keys())) in [["0"], ["1"], ["0", "1"]]):
							datatype = "TINYINT UNSIGNED"
						elif (field["date"]) and (field["date-format"] == "%Y-%m-%d"):
							datatype = "DATE"
						elif (field["datetime"]) and ((field["datetime-format"] == "%Y-%m-%d %H:%M") or (field["datetime-format"] == "%Y-%m-%d %H:%M:%S")):
							datatype = "DATETIME"
						elif (field["time"]) and ((field["time-format"] == "%H:%M") or (field["time-format"] == "%H:%M:%S")):
							datatype = "TIME"
						elif (field["length-min"] > 0) and (field["length-min"] == field["length-max"]):
							datatype = "CHAR({})".format(field["length-min"])
						elif field["integer"]:
							for inttype in integer_storage_bits:
								bits = integer_storage_bits[inttype]
								extra = ""
								minval = None
								maxval = None
								if field["integer-min"] < 0:
									minval = (-2)**(bits - 1)
									maxval = (2**(bits - 1)) - 1
								else:
									extra = " UNSIGNED"
									minval = 0
									maxval = (2**bits) - 1
								if (field["integer-min"] >= minval) and (field["integer-max"] <= maxval):
									datatype = inttype + extra
									break
						elif field["decimal"]:
							datatype = "DECIMAL"
						
						if datatype is None:
							length = field["length-max"]
							if length > 1024:
								datatype = "TEXT"
							else:
								if length <= 10: length = 10
								elif length <= 25: length = 25
								elif length <= 50: length = 50
								elif length <= 100: length = 100
								elif length <= 255: length = 255
								else: length = 1024
								datatype = "VARCHAR({})".format(length)
						
						columns.append("\t`{}` {} {}".format(column_name, datatype, null))
						
					# Create full SQL
					def escape(s):
						s = s.replace("\\", "\\\\")
						s = s.replace("'", "\\'")
						s = s.replace("\t", "\\t")
						s = s.replace("\r", "\\r")
						s = s.replace("\n", "\\n")
						return s
					parts = [table_name, ",\n".join(columns), escape(os.path.abspath(input_filename)), table_name, escape(self.inputs["delim"]), escape(self.inputs["enclose"]), escape(linesep or os.linesep), " IGNORE 1 LINES" if self.inputs["headers"] else ""]
					results = "CREATE TABLE {}(\n{}\n);\n\nLOAD DATA INFILE '{}' IGNORE INTO TABLE {} FIELDS TERMINATED BY '{}' OPTIONALLY ENCLOSED BY '{}' LINES TERMINATED BY '{}'{};\n".format(*parts)
				else:
					raise Exception("Unknown action: {}".format(self.inputs["action"]))
			else:
				results = "No data found."
			
			# Output the results
			mode = "w"
			f_out = self.open(output_filename, mode, self.inputs["encoding"])
			try:
				f_out.write(results)					
			finally:
				if f_out != sys.stdout: f_out.close()
			
			f += 1
		
		return "Processed {} records sucessfully".format(i)

class BasicAction(Action):
	"""Class to perform basic actions."""
	
	def action(self):
		"""Perform the task and return a message for the user."""
		
		total_bytes = 0
		for filename in self.inputs["input"]: total_bytes += 0 if filename == "STDIN" else os.path.getsize(filename)

		# Loop over input files
		b = i = f = 0
		started = time.time()
		for input_filename in self.inputs["input"]:
			# Get/format output filename
			(name, ext) = os.path.splitext(os.path.basename(input_filename))
			output_filename = self.inputs["output"].format(f=name, e=ext)
			
			# Open the input file
			f_in = self.open(input_filename, "r", self.inputs["encoding"])
			try:
				# Open the output file
				in_place = (os.path.normcase(os.path.normpath(input_filename)) == os.path.normcase(os.path.normpath(output_filename)))
				inidvidual_outputs = (self.inputs["output"] != output_filename)
				mode = "w" if (f == 0) or inidvidual_outputs else "a"
				f_out = self.open(output_filename + (".tmp" if in_place else ""), mode, self.inputs["encoding"])
				try:
					# Process the file
					headers = self.inputs["headers"]
					j = 0
					reader = DataReader(f_in)
					for line in reader:
						b += len(line.encode(self.inputs["encoding"])) + len(reader.linesep)
						
						# Skip the header row on all files except the first one, unless each file gets its own output
						if (f == 0) or (not headers) or inidvidual_outputs:
							record = None
							if self.inputs["action"] not in ["combine", "head"]:
								# Parse the data
								record = self.parse_data(line, self.inputs["delim"], self.inputs["enclose"], self.inputs["escape"])
							
								# Column error checking
								columns = []
								if isinstance(self.inputs["columns"], list): columns = self.inputs["columns"]
								if isinstance(self.inputs["column"], int): columns.append(self.inputs["column"])
								for c in columns:
									if c > len(record):
										raise Exception("Column #{} does not exist on line {} of '{}'".format(c+1, j+1, input_filename))
							
							# Process the record
							record_changed = False
							if self.inputs["action"] == "combine":
								pass
							elif self.inputs["action"] == "filter":
								if not headers:
									match = re.search(self.inputs["pattern"], record[self.inputs["column"]])
									if not((match and not self.inputs["invert"]) or (not match and self.inputs["invert"])): line = None
							elif self.inputs["action"] == "head":
								if (j+1) > self.inputs["lines"]: break
							elif self.inputs["action"] == "remove-columns":
								if self.inputs["invert"]:
									self.inputs["columns"] = list(set(range(len(record))) - set(self.inputs["columns"]))
									self.inputs["columns"].sort(reverse=True)
									self.inputs["invert"] = False
								for k in self.inputs["columns"]: del record[k]
								record_changed = True
							elif self.inputs["action"] == "repair":
								record_changed = True
							elif self.inputs["action"] == "replace-pattern":
								if not headers: record[self.inputs["column"]] = re.sub(self.inputs["find"], self.inputs["replace"], record[self.inputs["column"]])
								record_changed = True
							elif self.inputs["action"] == "replace-value":
								if not headers: record[self.inputs["column"]] = record[self.inputs["column"]].replace(self.inputs["find"], self.inputs["replace"])
								record_changed = True
							else:
								raise Exception("Unknown action: {}".format(self.inputs["action"]))
							
							# Update the line if needed
							if record_changed: line = self.unparse_data(record, self.inputs["delim"], self.inputs["enclose"], self.inputs["escape"])
							
							# Output the line
							if line is not None: f_out.write(line + "\n")
							
							if not headers:
								j += 1
								i += 1
						
						if headers: headers = False
						
						if self.inputs["action"] == "head":
							self.progress("Record: {}".format(i), started, i, self.inputs["lines"] * len(self.inputs["input"]))
						else:
							self.progress("Record: {}".format(i), started, b, total_bytes)
				finally:
					if f_out != sys.stdout: f_out.close()
			finally:
				if f_in != sys.stdin: f_in.close()
				if in_place: shutil.move("{}.tmp".format(output_filename), output_filename)
				
			f += 1
		
		return "Processed {} records sucessfully".format(i)

class FixedAction(Action):
	"""Class to perform actions on fixed width files."""
	
	def action(self):
		"""Perform the task and return a message for the user."""
		
		total_bytes = 0
		for filename in self.inputs["input"]: total_bytes += 0 if filename == "STDIN" else os.path.getsize(filename)

		# Read in fixed definition file
		fixed_map = []
		fixed_length = 0
		with open(self.inputs["definition"], mode="r", encoding=self.inputs["encoding"]) as d:
			for line in DataReader(d):
				fixed_map.append(int(line))
				fixed_length += int(line)
		
		# Loop over input files
		b = i = f = 0
		started = time.time()
		for input_filename in self.inputs["input"]:
			# Get/format output filename
			(name, ext) = os.path.splitext(os.path.basename(input_filename))
			output_filename = self.inputs["output"].format(f=name, e=ext)
			
			# Open the input file
			f_in = self.open(input_filename, "r", self.inputs["encoding"])
			try:
				# Open the output file
				in_place = (os.path.normcase(os.path.normpath(input_filename)) == os.path.normcase(os.path.normpath(output_filename)))
				inidvidual_outputs = (self.inputs["output"] != output_filename)
				mode = "w" if (f == 0) or inidvidual_outputs else "a"
				f_out = self.open(output_filename + (".tmp" if in_place else ""), mode, self.inputs["encoding"])
				try:
					# Process the file
					headers = self.inputs["headers"]
					j = 0
					reader = DataReader(f_in)
					for line in reader:
						b += len(line.encode(self.inputs["encoding"])) + len(reader.linesep)
						
						# Skip the header row on all files except the first one, unless each file gets its own output
						if (f == 0) or (not headers) or inidvidual_outputs:
							# Convert the data
							if self.inputs["action"] == "delim-to-fixed":
								record = self.parse_data(line, self.inputs["delim"], self.inputs["enclose"], self.inputs["escape"])
								f_out.write(self.unparse_fixed(record, fixed_map, fixed_length) + "\n")
							elif self.inputs["action"] == "fixed-to-delim":
								record = self.parse_fixed(line, fixed_map, fixed_length, j)
								f_out.write(self.unparse_data(record, self.inputs["delim"], self.inputs["enclose"], self.inputs["escape"]) + "\n")
							else:
								raise Exception("Unknown action: {}".format(self.inputs["action"]))
							
							if not headers:
								j += 1
								i += 1
						
						if headers: headers = False
						
						self.progress("Record: {}".format(i), started, b, total_bytes)
				finally:
					if f_out != sys.stdout: f_out.close()
			finally:
				if f_in != sys.stdin: f_in.close()
				if in_place: shutil.move("{}.tmp".format(output_filename), output_filename)
				
			f += 1
		
		return "Processed {} records sucessfully".format(i)
		
	def parse_fixed(self, line, fixed_map, fixed_length, i):
		"""Parse a fixed-length string into a list and return the result."""
		
		if len(line) != fixed_length: raise Exception("Line #{} is not the required {} characters long. It is {} characters long.".format(i+1, fixed_length, len(line)))
		
		record = []
		position = 0
		for m in fixed_map:
			record.append(line[position:(position + m)].strip())
			position += m

		return record
	
	def unparse_fixed(self, record, fixed_map, fixed_length):
		"""Unparse a list into a fixed-length string and return the result."""
		
		line = ""
		i = 0
		for column in record:
			line += column.ljust(fixed_map[i])[0:fixed_map[i]]
			i += 1
		
		return line

class SplitAction(Action):
	"""Class to perform actions that have multiple output files per input file."""
	
	def action(self):
		"""Perform the task and return a message for the user."""
		
		total_bytes = 0
		for filename in self.inputs["input"]: total_bytes += 0 if filename == "STDIN" else os.path.getsize(filename)

		# Loop over input files
		b = i = f = 0
		started = time.time()
		for input_filename in self.inputs["input"]:
			# Process the file
			f_out = None
			output_filename_current = None
			output_filenames = []
			f_in = self.open(input_filename, "r", self.inputs["encoding"])
			try:
				headers = self.inputs["headers"]
				header_line = None
				j = 0
				reader = DataReader(f_in)
				for line in reader:
					b += len(line.encode(self.inputs["encoding"])) + len(reader.linesep)
					
					record = None
					if self.inputs["action"] not in ["split-lines"]:
						# Parse the data
						record = self.parse_data(line, self.inputs["delim"], self.inputs["enclose"], self.inputs["escape"])
						
						# Column error checking
						c = self.inputs["column"]
						if isinstance(c, int) and (c > len(record)):
							raise Exception("Column #{} does not exist on line {} of '{}'".format(c+1, j+1, input_filename))
					
					# Save the header
					if headers and (j == 0): header_line = line
					
					if not headers:
						# Determine output filename
						output_filename_record = None
						dirname = os.path.dirname(input_filename)
						if dirname != "": dirname += os.sep
						(name, ext) = os.path.splitext(os.path.basename(input_filename))
						if self.inputs["action"] == "split-lines":
							output_filename_record = dirname + name + "-" + str((j//self.inputs["lines"]) + 1) + ext
						elif self.inputs["action"] == "split-value":
							tmp = re.sub("[^A-Za-z0-9 _-]+", "", record[self.inputs["column"]])
							if tmp == "": tmp = "BLANK"
							output_filename_record = dirname + name + "-" + tmp + ext
						else:
							raise Exception("Unknown action: {}".format(self.inputs["action"]))
						
						# Open the output file if needed
						if (output_filename_current is None) or (output_filename_current != output_filename_record):
							# Close previous file if needed
							if output_filename_current is not None: f_out.close()
							
							# Open output file
							output_filename_current = output_filename_record
							mode = "a" if output_filename_current in output_filenames else "w"
							f_out = self.open(output_filename_current, mode, self.inputs["encoding"])
							if output_filename_current not in output_filenames:
								output_filenames.append(output_filename_current)
								
								# Output the header if needed
								if header_line is not None: f_out.write(header_line + "\n")
						
						# Output the line
						f_out.write(line + "\n")
						
						j += 1
						i += 1
						
						self.progress("Record: {}".format(i), started, b, total_bytes)
					else:
						headers = False
			finally:
				if f_in != sys.stdin: f_in.close()
				if f_out is not None: f_out.close()
				
			f += 1
		
		return "Processed {} records sucessfully".format(i)

class DataReader:
	"""Iterator for files that removes line endings and skips blank lines."""
	
	def __init__(self, f):
		"""Initialize the object."""
		self.f = f
		self.linesep = ""
	
	def __iter__(self):
		"""Make the class an iterator."""
		return self
	
	def __next__(self):
		"""Return the next non-blank line and store the line separator in self.linesep."""
		while True:
			line = self.f.readline()
			if line == "":
				raise StopIteration()
			else:
				if line[-2:] == "\r\n": self.linesep = "\r\n"
				elif line[-1:] == "\r": self.linesep = "\r"
				elif line[-1:] == "\n": self.linesep = "\n"
				else: self.linesep = ""
				
				line = line.strip("\r\n")
				if line != "": return line

class CLI(BaseCLI):
	"""Class for defining the command line interface."""
	
	def define_arguments(self):
		"""Define the command line arguments."""
		
		self.arguments = [
			("help"      , "h", "Show help information"                , "boolean"),
			("version"   , "V", "Show version information"             , "boolean"),
			("license"   , "l", "Show license information"             , "boolean"),
			("quiet"     , "q", "Suppress all output"                  , "boolean"),
			("verbose"   , "v", "Enable verbose output\n"              , "boolean"),
			
			("action"    , "a", "Action to perform (see below)"        , "value"),
			("column"    , "" , "Column number, starting at 1"         , "value"),
			("columns"   , "" , "Column numbers, starting at 1 (1)"    , "value"),
			("definition", "" , "Fixed width definition file (2)"      , "value"),
			("find"      , "" , "Value/pattern to find"                , "value"),
			("replace"   , "" , "Replacement value/pattern"            , "value"),
			("invert"    , "" , "Invert match"                         , "boolean"),
			("lines"     , "" , "Number of lines"                      , "value"),
			("pattern"   , "" , "Regular expression\n"                 , "value"),
			
			("input"     , "i", "Input filename(s), omit for STDIN"    , "multiple"),
			("output"    , "o", "Output filename, omit for STDOUT (3)" , "value"),
			("delim"     , "d", "Delimiter character"                  , "value"),
			("enclose"   , "e", "Enclose character"                    , "value"),
			("escape"    , "s", "Escape character"                     , "value"),
			("encoding"  , "c", "File encoding (i.e., utf-8 or cp1252)", "value"),
			("headers"   , "H", "Input contains headers"               , "boolean")
		]
		
		# Flags used: a, c, d, e, h, i, l, o, q, s, v, H, V
		
	def define_usage(self):
		"""Define the command line usage."""
		self.usage = "dart --action action [-options] -i input(s) [-o output]"
	
	def print_help(self):
		"""Print the help information to standard out."""
		
		super(CLI, self).print_help()
		
		q = "\"" if "win" in sys.platform else "'"
		continue_char = "^" if "win" in sys.platform else "\\"
		
		# Print notes
		print("(1) Separate with commas, you can also use ranges, i.e.: 1,3-5")
		print("(2) File containing the lengths of each column, one per line")
		print("(3) Use {f} (filename) and {e} (extension) for variable output filenames")
		print("    `--output {f}{e}` will update files in-place")
		print("    `--output {f}-out{e}` will create individual outputs")
		
		# Print action info
		print("")
		print("Actions:")
		
		print("  analyze - analyze a file and output a summary of its contents")
		print("    dart -a analyze -i a.csv -o b.csv --headers")
		print("    dart -a analyze -i a.csv -o b.csv --headers --lines 1000")
		print("")
		
		print("  combine - combine multiple files")
		print("    dart -a combine -i *.csv -o b.csv")
		print("")
		
		print("  delim-to-fixed - covert a delimited file to a fixed width file")
		print("    dart -a delim-to-fixed --definition fixed.def -i a.csv -o b.txt")
		print("")
		
		print("  filter - filter records based on a column's value")
		print("    dart -a filter --column 1 --pattern {q}^A{q} -i a.csv -o b.csv".format(q=q))
		print("    dart -a filter --column 1 --pattern {q}^A{q} -i a.csv -o b.csv --invert".format(q=q))
		print("")
		
		print("  fixed-to-delim - covert a fixed width file to a delimited file")
		print("    dart -a fixed-to-delim --definition fixed.def -i a.txt -o b.csv")
		print("")
		
		print("  head - output a specified number of lines from the beginning of a file")
		print("    dart -a head --lines 10 -i a.csv -o b.csv")
		print("")
		
		print("  remove-columns - remove columns")
		print("    dart -a remove-columns --columns 1,3-5 -i a.csv -o b.csv")
		print("    dart -a remove-columns --columns 1,3-5 -i a.csv -o b.csv --invert")
		print("")
		
		print("  repair - enclose and escape all fields")
		print("    dart -a repair -i a.csv -o b.csv")
		print("")
		
		print("  replace-pattern - replace a pattern in a column with another")
		print("    dart -a replace-pattern --column 1 --find {q}f(.*){q} --replace {q}b\\1{q} -i a.csv {continue_char}\n      -o b.csv".format(q=q, continue_char=continue_char))
		print("")
		
		print("  replace-value - replace a value in a column with another")
		print("    dart -a replace-value --column 1 --find foo --replace bar -i a.csv -o b.csv")
		print("")
		
		print("  split-lines - split one file into many based on number of lines")
		print("    dart -a split-lines --lines 500 -i a.csv")
		print("")
		
		print("  split-value - split one file into many based on a column's value")
		print("    dart -a split-value --column 1 -i a.csv")
		print("")
		
		print("  sql-import - create SQL CREATE TABLE and LOAD DATA statements")
		print("    dart -a sql-import -i a.csv -o b.sql --headers")
		print("    dart -a sql-import -i a.csv -o b.sql --headers --lines 1000")
		print("")
		
	def get_action(self, inputs):
		"""Return the BaseAction subclass to use."""	
		
		if inputs["action"] in ["delim-to-fixed", "fixed-to-delim"]:
			return FixedAction
		elif inputs["action"] in ["split-lines", "split-value"]:
			return SplitAction
		elif inputs["action"] in ["analyze", "sql-import"]:
			return AnalyzeAction
		else:
			return BasicAction

class GUI(BaseGUI):
	"""Class for defining the graphical user interface."""
	
	def define_icon(self):
		"""Define the icon."""		
		self.icon = "iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAIAAABMXPacAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH4QkYDzYNdYDVcwAAABl0RVh0Q29tbWVudABDcmVhdGVkIHdpdGggR0lNUFeBDhcAABHYSURBVHja7V1tUJNXFj55B2mMkIbPBQRERA1UMMuiTRV2GYqIFBEouI4yQv3aWMcdQGGQP6V/WsaPyuhYo7IWGXBcxDRSpAjIsGt0qVIakQUKGKNgoOErBUQWHdgf6SCiAue+7xsC5fzOubn3ed57zj3n3nsuZ2RkBIxYelSqzoaG7uZmnVrd29ra394+0Nk5qNMN9fe/GBwcefECADgmJiZcrqmZGVcg4Flbm9nZ8R0dBS4ulm5u1kKhhaurMQ+QY2wE9Gk0jxWK1spKTVVVu1I51NdHs0FTc3M7kcjBx8dRLHb29TV3cJgj4A3yoKSkubhYVVamvX+f1T+y9fR0DQx0Cw5eEhQ0RwA0FRXV5ec3yOWDPT0G/muuhYUwPNwjKmppSMjvjoCuxkZlVlZNTk5vS8u0f4N8JyevmBhRXJzVsmWzn4AHJSVVUmnDt98aoT8URkT4SCQGNk2GI6BeJqvMyHh88yYYtzj7+Ynj490jI2cPAU1FRYr0dOOHfhwNvikpBnAP7BLwS01NRVqacRqcKRol/7S0P3h5zUgCbqSmKr78Ema++B469OEXX8wkApqKikoOHuysr4fZItbu7kFHj7JhkZgn4HpiYuXx4zAbRZyQsP6rr4yXgLbq6kKJRHP3LsxecVi1KlQqtff2NjoCfjp//rtdu4w8tccMZBzOxszMP+7YwUhrFCOtlCYnF+zc+XtAHwBGRkYKdu4sTU42ihkwMjycv2VL3eXL8PsTj+joqEuXOBQ1bQQ81WrzoqLYjrDe4fPtRCIbDw+rZcveXbSIv3Ahz8aGKxCYLlhAzZsHAMPPnw89fTqo0w10dPQ+efLro0ddjY0ddXXtSuX/envZjtc25+cvsLWdBgJ6VKpL4eEsZY/nW1ktWbfOxd/fae1a2xUriNvR1ta23Lqlrqh4UFr6rKuLja7aenpukcuJt30ICehqbLwYGtrd1MTsYMzs7d+Ljl6+adPigADGkXpYXv7z1av/vXy5v62N2ZYtly7dWlhIlkwlIaBHpcoJDmYW/eVhYStjYw2TAquXye5duPBzQQGzHMQUFxPMAzQBT7Xa7MBABi2Pj0Syat8+OnaG2DrdPXWqSipl0BZtLyvD+gMcASPDw1n+/kx5XR+JZE1S0vRumveoVLePHGGKBmc/v7iKCtS6CEfA5c2bGVlxLg8L+8tnnzEYT9KP4f/1+eeMGCWP6OjovDxWCChNTr595Ah9N7vu8GGvmBgjXNfX5OSUJifTd9FrkpLWHT7MMAE/nT9fsHMnzZ6t3L59/fHj8y0tjTa2etbdfT0h4V52Ns12wv7xjynmKqZEQFt19TkfH5oxc6hU+qe//W1GhLg/njlTKJHQzBftrqqaio2dEgHnVq+mk+O0dncP/+abhe+/P4PSDE9++EH+ySd0tjQcVq3afefOpD+b3F9fT0ykg77bhg07FIqZhT4ALHz//R0KhduGDcQtaO7evZ6YSHcGNBUVXfzoIzpGP/zCBZjJIo+NpeMStl67NvE+2iQzoOTgQTrL/JmOPgCEX7jgQ8MfTArgRATcSE0lNoI+EslHp0/DrJCPTp8m5qCzvv5GaiqJCfqlpka6cuXv1vIwa4sk9+697WzLWwn4Z2Qk2Xketw0bthUVMT7+3paW1srKdqWys6FBp1b3t7cP6nQvBgcBwITL5QoEZnZ2AhcXa6HQTiRyFIv5Tk6M9yE3JKT5++8JFIUREX+VyRAEEPtea3f3HQoFg6HW45s3G+Ty5uLijro6lKKNh4dbcLAwPNzZz4/BMO28ry+ZWX6bN34zAd/8+c9kGbddlZWMrDiH+vqqpFJlVhYW9zcyIYqL85FITM3NGYkPMsViAkVnP79P/v3vKRFQL5PlffzxdMW6Q319ivT0yoyM5wMDDFqPeTyeOD7eNyWFPg3EcfLmK1de3/B4AwFknz8jjvfOyZMVaWnPurtZcqTzLS3909JW798/LQ75jZNgPAEPSkpy1q/HNm1mb/9pbS0d06+9f784Pv5hebkB1jOLAwKCMzJsPT3pOIOvV6wgyJvGXL8+7v7B+DiAbGti3eHDdNCvPndOKhIZBn0AeFheLhWJqs+dozOTpp5wnhjeVwjoamwkWHouDwujk98vOXDguz17RoaHDbmoHxke/m7PnpIDB4hb8IqJWR4WhtVq+PbbrsbGtxKgzMoi6MpfPvuMeBiybdv+w/Rx16nLf776SrZtG7E62cDHgfwKATU5OQQpB+KdxbyPP75/8eL0xrf3L14kW/IBgL23N0GKYhzI1Njgi+DO4pqkJOJvv/4twaGBpV4mI54HBMPvbWlpGpMpeElAXX4+wedPdqah5MCBaf/2x80DMn9g4epKMAnGQv2SgAa5HNvQqn37yNY802j3J/AHZOsiAhDGQk2NLv+xd9WXh4URnKbS3r9Pc7uVPSmUSAgOnNmuWIFdDg329DwoKXmFgObiYnToGxtLMMji+HgDrzhRa9Pi+HgCRQIoRgH/jQBVWRk29CU4x3nn5EmDRVvEMdqdkyexWu6RkWb29iiVUcBNAKBPo8FOvfeio7G9HOrrq0hLownQEEADgBqgHUAHMAgAAFwAAYAdgAuAEMCU3l9UpKWJ4uKwObv3oqN/OHECZYr7NBpzBwcKAB4rFOjod9MmrIoiPZ1Olk0LUACQDiADqAbQAAwADAMMAwwAaACqAWQA6QAFAFoaBDzr7lakpxsAED3sFAC0VlbiMiFWVtjz+0N9fZUZGeTpCoCvAaoBJvUewwDVAF8DlNDgoDIjA1soanFAwHwrK5SKHnYKADRVVSjNJevWESShyPL7WoCzALfxircBzpJOhecDAwRJSSwsetgpAGhXKlGaLv7+NBMgU52kAFkAGtIPWQOQBfCYSJegw1hY9LBTPSoVdro5rV2Lw/HmTYKdRS3AJQCau2IDAJeI5kFHXR12VwoLy1BfX49KRXU2NKDU3uHzsfEXQYwNAHLa6I9yICdSxHbbdsWKd/h8lEpnQwPV3dyM0rETiYiDDpTX1QBjoiHyyQTdxoLT3dxM6dRqlI6Nhwfq970tLVj7oyXyupP6ZC3eCmHTw1hwdGo11dvaitLBXsbErnEBoBJYEYJmsZ3HgtPb2kr1t7ejdN5dtIjA16NiXSU7BCgBhpAq2M5jwelvb6cGOjtROvyFC7F+Buf6phBtkckwQANSBdt5LDgDnZ3UoE6H0uHZ2GDNHOr3amBRsI1jO48FZ1Cno4b6+1E6XIEAO8tws55NArCNYzuPBWeov5/SHzCeupguWIAlGffRsUkAtnFs57HgvBgcpPQV4Kcu+goxqP/AjZlNArCNYzuPBWfkxQsK5mRaheKYmODWEs+fo35vwuXizCibo8U2ju08FhyOiQmF/Y+hp09Z9UsCNgnANo52qkhwTLhcytTMjFW/ZGZnh0unsEkAtnFs59FO28yMwpI80NGB++hcXFC/d2GTAGzj2M5jweEKBBTP2hqXvnjyBPV7a6EQ9XshU6U0X3d3AEKkCrbzWHB41tYUdpb9+ugRbtYjM7SmACJ2CBDhD0xgO48Fx8zOjuI7OqJ0xh1vn1Qc8VfaxOwQQNAstvNYcPiOjhTWzGGT+3wnJ2yW3BZgDdPorwHA1va08fDAXjbGgiNwcaEs3dxw6RQlOlvsFhyMVQkCYPC5LwcAgndhCLqNBcfSzY3C+pn/9fZqa2txfjU8nAC1cAAeE+jzAMKJFLHd1tbWYgv1WguFlIWrK/YYXsutW6jfO/v5Ya2Q3hBtoc0BD2AL3vjo7Q/2ij0WFlNzcwtXV4rA16srKtArkLg4AvicAeJo2CIHgDgAZ7IlE77DWFj0sFMA4ODjg9J8UFqK7ZyPRDKPR/I12wLsIfLJawD2EH37ADCPxyO494KFRQ87RbDYetbVhT1lbmpuLiY6ej/qkz8F8J5CjEYBeAN8SuR1Xy5Y4+OxZvlheTm2OLgedgoAnH19sV38+epVrIpvSgqdy9y2AGEAKQCRAN4ADgA8AAqAAuABOAB4A0QCpACEkX74eplvaembkmIAQPSw/1aq4LSXF+qKgJm9/QEN+ujUnZMnv//738G4ZcOJEwTFJI45OKAqF9h6eu6tqYHROe0aGIj6v/62NoJLpqv372ejLj2DsjgggAD9epkMWzdiFHCKOOi4R1QbJTgjg+abH+wJh6KCiS4xEEAxCvhvWCwJCuJaWOCsXkEBNiLTT71Q5irGMyuhUilBCRVtbS226jfXwmK0ZgpFJ169e+oUwTi9d+/+YAoVTQ0sHyQmeu/eTaBIAMJYqF8S4BEVhW2oSirtUalIlpXHjnlu3Wo86Htu3Rp07BiBYo9KRXCXZizULwlYGhJCUGmQuKB9ZG6uwd7snVjcIyMjc3PJdAmGz3dyGlu97xV/SFD2p0oqbauuJuv95itXpn0eeG7duvnKFTLdtupqgs9/HMgU/YzNvz7/nHj8kbm50+gPPkhMJP72iQc+DuRXCLBatkwYEYEOAgsKCAoNjfUHG8+eNfDalENRG8+eJbP7eqnJySF48kQYETHuDsH4YZMVSS5NTqZzCdt7926JUmmwGG1xQIBEqSRb8+jlWXc32VuSr8M7noAlQUEEpWb729quJyTQAcXW03P7jRsbTpxg9YGT+ZaWG06c2H7jBp2SiQBwPSGBoGSis5/fuJKJ8Mb0Ilna8l529o9nztAEaPX+/fFqtV9qKlnuegKZx+P5pabGq9X0i4b+eOYMWRXvNwI7V7oYJ4YoXQxzxbvfbvoNVLwb5srXv0kMV74e5h5weE1YesDhravvP3h5+R46RPZ/97Kzr+3dO5vQv7Z3LzH6vocOvQ19mPQVpVMeHnPPyFzbu5f4tU9rd/d9E3qvSeLPoKNHiftdJZXKiQr7GZvlofPW6qQATkLA0pAQMY0I6152dm5ICHvvAbAqz7q7c0NC6DwiJk5ImPgRMZh7ynCC9b6xPGUIAKFSKYfDIe5KZ319plhMP042mPx45kymWEwHfQ6HM8Wd1ykRYO/tvTEzk+aoCiUSeWyskZujZ93d8thY+rV9N2ZmTrGo/NyDzi/FqB901svck+aTCotPmgPAyPBwlr8/WZ7ujYHCmqQksgL4TEmPSnX7yJEqhk7KOPv5xVVUoDaXONh3sp9qtdmBgQRVxiegYdW+fQSF2GmKtrb27qlTVcwdUrL19NxeVrbAFncwlUPwUHmPSpUTHNzd1MQgHMvDwlbGxhrmnES9THbvwgVGDM6oWC5dGlNcTDCbOWQvxXc1Nl4MDWWWA72Lfi86evmmTWxsTz4sL//56tX/Xr5M382+jv7WwkJswThaBOjnwaXwcAZt0ViZb2W1ZN06F39/p7Vr6VgnbW1ty61b6oqKB6Wl2PP7U7c8W+RyYk9GToDeH+RFRTHlk98m7/D5diKRjYeH1bJl7y5axF+4kGdjwxUITBcs0NfnGX7+fOjp00GdbqCjo/fJk18fPepqbOyoq2tXKrG35gi87ub8fKzdZ4wA/boof8sWRtamM048oqOjLl2ieaCG7mkcDkVF5+URP2Y1c2VNUlJ0Xh7940x0Z8Co/HT+/He7djHVmjELh8PZmJn5xx07mGmNQcjaqqsLJRI6eVPjF4dVq0KlUgZjeA7j3+z1xMTK48dnJfrihIT1TL+AxmHDaDQVFZUcPEgnnWtsYu3uHnT06KS7K8ZCgF5upKYqvvxyFqDve+jQh198wZZHYdVt/lJTU5GWRna+yBhEGBHhn5Y2wZkGYydg1CIp0tPZjtcYj7B8U1LYsDnTQIBe6mWyyowM46fB2c9PHB9vsOtTHAOv3B+UlFRJpcZplIQRET4SyesnyGcVAXrpamxUZmXV5OQQPCHNuPCdnLxiYkRxcWTpzBlJwFj3UJef3yCXYx/TpS9cCwtheLhHVJQBDL3xEjDWNDUXF6vKyljKb4+Kraena2CgW3CwgU2NsRMwKn0azWOForWyUlNV1a5UYh+Ze11Mzc3tRCIHHx9HsdjZ19fcwcGoxssx8vRZj0rV2dDQ3dysU6t7W1v729sHOjsHdbqh/v4Xg4P6xw84JiYmXK6pmRlXIOBZW5vZ2fEdHQUuLpZubtZC4fRu+k8q/wc070oBdVCNSQAAAABJRU5ErkJggg=="
	
	def define_menu(self):
		"""Define the menu."""
		
		self.menu = {
			"File":{"Exit":self.quit},
			"Edit":{"Reset":self.reset},
			"Settings":{"Open Config File":self.open_config},
			"Help":{"Help":self.show_help, "About":self.show_about}
		}
	
	def define_help(self, help):
		"""Define the help information."""
		
		path = "C:\\example\\" if "win" in sys.platform else "/home/example/"
		
		help.insert(tk.END, "Usage\n\n", "bold")
		help.insert(tk.END, "To use this program, select an Action, enter all necessary fields and click the Submit button.\n\n", "normal")
		
		help.insert(tk.END, "Action\n\n", "italic")
		help.insert(tk.END, """ \u2022 Analyze - analyze a file and output a summary of its contents
 \u2022 Combine - combine multiple files
 \u2022 Delim to Fixed - covert a delimited file to a fixed width file
 \u2022 Filter - filter records based on a column's value
 \u2022 Fixed to Delim - covert a fixed width file to a delimited file
 \u2022 Head - output a specified number of lines from the beginning of a file
 \u2022 Remove Columns - remove columns
 \u2022 Repair - enclose and escape all fields
 \u2022 Replace Pattern - replace a pattern in a column with another
 \u2022 Replace Value - replace a value in a column with another
 \u2022 Split Lines - split one file into many based on number of lines
 \u2022 Split Value - split one file into many based on a column's value
 \u2022 SQL Import - create SQL CREATE TABLE and LOAD DATA statements

""", "normal")
		
		help.insert(tk.END, "Action Options\n\n", "italic")
		help.insert(tk.END, """ \u2022 Column - column number, starting at 1
 \u2022 Columns - column numbers, starting at 1, separate with commas, you can also use ranges, i.e.: 1,3-5
 \u2022 Definition - fixed width definition file, containing the lengths of each column, one per line
 \u2022 Find - value/pattern to find
 \u2022 Replace - replacement value/pattern
 \u2022 Invert? - invert match
 \u2022 Lines - number of lines
 \u2022 Pattern - regular expression

""", "normal")
		
		help.insert(tk.END, "Input\n\n", "italic")
		help.insert(tk.END, "Use the Browse button to select one or more files. You can also enter the file names manually. For one file, enter the full path and file name. For multiple files, use a CSV string of full file names. You can also specify multiple file names with a wild card (*) character. All of the following are valid entries:\n\n", "normal")
		help.insert(tk.END, " \u2022 {0}input.csv\n \u2022 \"{0}input1.csv\",\"{0}input2.csv\"\n \u2022 {0}input*.csv\n\n".format(path), "normal")
		
		help.insert(tk.END, "Output\n\n", "italic")
		help.insert(tk.END, "Use the Browse button to select a shared output file. Use {f} (filename) and {e} (extension) for variable output filenames.\n\n", "normal")
		help.insert(tk.END, " \u2022 {f}{e} - will update files in-place\n \u2022 {f}-out{e} - will create individual outputs\n\n", "normal")
		
		help.insert(tk.END, "Input Options\n\n", "italic")
		help.insert(tk.END, """ \u2022 Delimiter - delimiter character
 \u2022 Enclose - enclose character
 \u2022 Escape - escape character
 \u2022 Encoding - file encoding (i.e., utf-8 or cp1252)
 \u2022 Headers? - input contains headers
 
 """, "normal")
		
		help.insert(tk.END, "Configuration File\n\n", "bold")
		help.insert(tk.END, "There is a configuration file at {0}. This file contains settings you can modify. Open it with Settings > Open Config File. You will need to close and reopen the application for any changes to take effect.".format(self.prog["config"]), "normal")
		
		help.config(height = 45)
		help.config(width  = 110)
	
	def enable_widgets(self, event=None):
		"""Enable all widgets for the current action."""
		
		action = self.widgets["action"].getval()
		actions = {
			"":["action"],
			
			"Combine"        :["action", "input", "input-browse", "output", "output-browse",                               "encoding", "headers", "submit"],
			"Filter"         :["action", "input", "input-browse", "output", "output-browse", "delim", "enclose", "escape", "encoding", "headers", "submit", "column", "invert", "pattern"],
			"Head"           :["action", "input", "input-browse", "output", "output-browse",                               "encoding", "headers", "submit", "lines"],
			"Remove Columns" :["action", "input", "input-browse", "output", "output-browse", "delim", "enclose", "escape", "encoding", "headers", "submit", "columns", "invert"],
			"Repair"         :["action", "input", "input-browse", "output", "output-browse", "delim", "enclose", "escape", "encoding", "headers", "submit"],
			"Replace Pattern":["action", "input", "input-browse", "output", "output-browse", "delim", "enclose", "escape", "encoding", "headers", "submit", "column", "find", "replace"],
			"Replace Value"  :["action", "input", "input-browse", "output", "output-browse", "delim", "enclose", "escape", "encoding", "headers", "submit", "column", "find", "replace"],
			
			"Delim to Fixed":["action", "input", "input-browse", "output", "output-browse", "delim", "enclose", "escape", "encoding", "headers", "submit", "definition", "definition-browse"],
			"Fixed to Delim":["action", "input", "input-browse", "output", "output-browse", "delim", "enclose", "escape", "encoding", "headers", "submit", "definition", "definition-browse"],
			
			"Split Lines":["action", "input", "input-browse",                               "encoding", "headers", "submit", "lines"],
			"Split Value":["action", "input", "input-browse", "delim", "enclose", "escape", "encoding", "headers", "submit", "column"],
			
			"Analyze"   :["action", "input", "input-browse", "output", "output-browse", "delim", "enclose", "escape", "encoding", "headers", "submit", "lines"],
			"SQL Import":["action", "input", "input-browse", "output", "output-browse", "delim", "enclose", "escape", "encoding", "headers", "submit", "lines"]
		}
		
		for name in self.widgets:
			if not isinstance(self.widgets[name], ttk.Notebook):
				self.widgets[name].config(state = (tk.NORMAL if not isinstance(self.widgets[name], ttk.Combobox) else "readonly") if name in actions[action] else tk.DISABLED)
		
		self.update()
	
	def create_widgets(self):	
		"""Create the widgets."""
		
		actions = ("", "Analyze", "Combine", "Delim to Fixed", "Filter", "Fixed to Delim", "Head", "Remove Columns", "Repair", "Replace Pattern", "Replace Value", "Split Lines", "Split Value", "SQL Import")
		self.create_combobox(self, "action", "Action", actions)
		self.widgets["action"].bind("<<ComboboxSelected>>", self.enable_widgets)
		
		self.create_entry   (self, "column"    , "Column" )
		self.create_entry   (self, "columns"   , "Columns")
		self.create_browse  (self, "definition", "Definition", self.get_input, filetypes=[("All Files", ".*")])
		self.create_entry   (self, "find"      , "Find"   )
		self.create_entry   (self, "replace"   , "Replace")
		self.create_entry   (self, "lines"     , "Lines"  )
		self.create_entry   (self, "pattern"   , "Pattern")
		
		self.create_browse  (self, "input"   , "Input"    , self.get_inputs, filetypes=[("All Files", ".*")])
		self.create_browse  (self, "output"  , "Output"   , self.get_output, filetypes=[("All Files", ".*")])
		self.create_entry   (self, "delim"   , "Delimiter", default=self.conf.get("delim", ""))
		self.create_entry   (self, "enclose" , "Enclose"  , default=self.conf.get("enclose", ""))
		self.create_entry   (self, "escape"  , "Escape"   , default=self.conf.get("escape", ""))
		self.create_entry   (self, "encoding", "Encoding" , default=self.conf.get("encoding", ""))
		self.create_checkbox(self, "headers" , "Headers?" , 0)
		self.create_checkbox(self, "invert"  , "Invert?"  , 0)
		
		self.create_button  (self, "submit", "Submit", self.action)
		
		self.disable_widgets()
		self.widgets["action"].config(state = "readonly")

	def get_action(self, inputs):
		"""Return the BaseAction subclass to use."""
		
		if inputs["action"] in ["Delim to Fixed", "Fixed to Delim"]:
			return FixedAction
		elif inputs["action"] in ["Split Lines", "Split Value"]:
			return SplitAction
		elif inputs["action"] in ["Analyze", "SQL Import"]:
			return AnalyzeAction
		else:
			return BasicAction
	
	def reset(self):
		"""Reset all widgets."""
		
		self.set_defaults()
		self.disable_widgets()
		self.widgets["action"].config(state = "readonly")

if __name__ == "__main__": main(program, Configuration, CLI, GUI)
