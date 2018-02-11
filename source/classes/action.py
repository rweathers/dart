#############################################################################################################################
# dart - Analyze and manipulate delimited data files.
# Action classes
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

import os
import re
import shutil
import sys
import time
from datetime import datetime
from hydra import BaseAction
from classes.data_reader import DataReader

# ===========================================================================================================================
# Class to validate the user's inputs and do the actual work
class Action(BaseAction):
	# -----------------------------------------------------------------------------------------------------------------------
	# Standardizes the inputs
	def standardize(self):
		# Standardize action name
		self.inputs["action"] = self.inputs["action"].lower().replace(" ", "-")
		
		# Convert column to int
		if self.inputs["action"] in ["filter", "replace-pattern", "replace-value", "split-value"]:
			try:
				self.inputs["column"] = int(self.inputs["column"])
			except ValueError as e:
				pass
			
		# Convert columns to a list of ints
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
							for j in range(int(x), int(y)+1): self.inputs["columns"].append(j)
						else:
							self.inputs["columns"].append(int(columns[i]))
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
	
	# -----------------------------------------------------------------------------------------------------------------------
	# Raises an exception if any of the inputs are invalid
	def validate(self):
		message = ""
		
		if self.inputs["action"] == "": message += "Action required\n"
		
		# Validate column
		if self.inputs["action"] in ["filter", "replace-pattern", "replace-value", "split-value"]:
			try:
				if not isinstance(self.inputs["column"], int): raise Exception()
				if self.inputs["column"] < 0: raise Exception()
			except Exception as e:
				message += "column must be an non-negative integer\n"
			
		# Validate columns
		if self.inputs["action"] in ["remove-columns"]:
			try:
				if self.inputs["columns"] is None: raise Exception()
				for i in self.inputs["columns"]:
					if i < 0: raise Exception()
			except Exception as e:
				message += "columns must be a comma separated list of non-negative integers\n"
		
		# Validate lines
		if self.inputs["action"] in ["analyze", "sql-import"]:
			try:
				if not isinstance(self.inputs["lines"], int): raise Exception()
				if self.inputs["lines"] < 0: raise Exception()
			except Exception as e:
				message += "if supplied, lines must be a non-negative integer\n"
		elif self.inputs["action"] in ["head", "split-lines"]:
			try:
				if not isinstance(self.inputs["lines"], int): raise Exception()
				if self.inputs["lines"] <= 0: raise Exception()
			except Exception as e:
				message += "lines must be a positive integer\n"
		
		if len(self.inputs["input"]) == 0: message += "Input file(s) required\n"
		
		if (self.inputs["action"] not in ["split-lines", "split-value", "uncombine"]) and (self.inputs["output"] == ""): message += "Output file required\n"
		
		if (self.inputs["action"] in ["delim-to-fixed", "fixed-to-delim"]) and (self.inputs["definition"] == ""): message += "Definition file required\n"
		
		if self.inputs["encoding"] == "": message += "File encoding required\n"
		
		if message != "": raise Exception(message)
	
	# -----------------------------------------------------------------------------------------------------------------------
	# Parses a delimited string into a list
	def parse_data(self, record, delim=",", enclose="\"", escape="\""):
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
	
	# -----------------------------------------------------------------------------------------------------------------------
	# Unparses a list into a delimited string
	def unparse_data(self, record, delim=",", enclose="\"", escape="\""):
		ret = []
		if enclose == "": escape = ""
		for r in record: ret.append(enclose + str(r).replace(enclose, escape + enclose) + enclose)
		return delim.join(ret)

# ===========================================================================================================================
# Class to perform actions that analyze the full file and output something besides the original data
class AnalyzeAction(Action):
	# -----------------------------------------------------------------------------------------------------------------------
	# Processes the input file(s) and performs the user's action
	def action(self):
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
				datetime_formats.append(d + " " + t)

		# Loop over input files
		b = i = f = 0
		started = time.time()
		for input_filename in self.inputs["input"]:
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
				for line in DataReader(f_in):
					b += len(line.encode(self.inputs["encoding"])) + len(os.linesep)

					# Parse the data
					record = self.parse_data(line, self.inputs["delim"], self.inputs["enclose"], self.inputs["escape"])
					
					# Initialize the field information
					if (l == 0):
						k = 0
						for value in record:
							field = {
								"name":value if headers else "field-" + str(k),
								
								"length-min":None,
								"length-avg":0,
								"length-max":None,
								
								"text-min":None,
								"text-max":None,
								
								"integer":True,
								"integer-min":None,
								"integer-avg":0,
								"integer-max":None,
								
								"float":True,
								"float-min":None,
								"float-avg":0.0,
								"float-max":None,
								
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
								
								"blanks":0,
								
								"values":{}
							}
							fields.append(field)
							k += 1
							
					# Process the record
					if not headers:
						k = 0
						for value in record:
							if (value != "") and (value != "\\N"):
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
								
								if d["float"]:
									try:
										if re.search("^0[^\\.]", value): raise Exception()
										
										val = float(value)
										d["float-min"] = val if d["float-min"] is None else min(val, d["float-min"])
										d["float-avg"] += val
										d["float-max"] = val if d["float-max"] is None else max(val, d["float-max"])
									except Exception as e:
										d["float"] = False
								
								def dt_helper(key, formats):
									if d[key]:
										val = None
										formats = [d[key + "-format"]] if d[key + "-format"] is not None else formats
										for format in formats:
											try:
												val = datetime.strptime(value, format)
												d[key + "-format"] = format
												break
											except Exception as e:
												pass
												
										if val is not None:
											if (d[key + "-min"] is None) or (val < datetime.strptime(d[key + "-min"], d[key + "-format"])): d[key + "-min"] = value
											if (d[key + "-max"] is None) or (val > datetime.strptime(d[key + "-max"], d[key + "-format"])): d[key + "-max"] = value
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
								
							else:
								fields[k]["blanks"] += 1
							
							k += 1
					
					if not headers:
						j += 1
						i += 1
					
					if headers: headers = False
					
					l += 1
					
					if (self.inputs["lines"] > 0) and (j >= self.inputs["lines"]): break
					
					if self.inputs["lines"] > 0:
						self.progress("Record: " + str(i), started, i, self.inputs["lines"] * len(self.inputs["input"]))
					else:
						self.progress("Record: " + str(i), started, b, total_bytes)
					
				# Clean up blank fields
				for field in fields:
					if field["blanks"] == j:
						field["length-min"] = 0
						field["length-max"] = 0
						field["text-min"] = ""
						field["text-max"] = ""
						field["integer"] = False
						field["float"] = False
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
						["Blank Values"],
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
						elif field["float"]:
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
						data[x].append(0 if (j - field["blanks"]) == 0 else round(field["length-avg"]/(j - field["blanks"]), 1))
						x += 1
						
						# Maximum Length
						data[x].append(field["length-max"])
						x += 1
						
						if field["integer"]:
							# Minimum Value
							data[x].append(field["integer-min"])
							x += 1
							
							# Average Value
							data[x].append("" if (j - field["blanks"]) == 0 else round(field["integer-avg"]/(j - field["blanks"]), 1))
							x += 1
							
							# Maximum Value
							data[x].append(field["integer-max"])
							x += 1
						elif field["float"]:
							# Minimum Value
							data[x].append(field["float-min"])
							x += 1
							
							# Average Value
							data[x].append(field["float-avg"]/j)
							x += 1
							
							# Maximum Value
							data[x].append(field["float-max"])
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
						
						# Blank Values
						data[x].append(field["blanks"])
						x += 1
						
						# Distinct Values
						data[x].append(len(field["values"]))
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
					
					# Create column definitions
					columns = []
					for field in fields:
						column_name = field["name"].strip().lower()
						column_name = re.sub("[ -]+", "_", column_name)
						column_name = re.sub("[^A-Za-z0-9_]+", "", column_name)
						
						null = "NULL" if field["blanks"] > 0 else "NOT NULL"
								
						datatype = None
						if (field["date"]) and (field["date-format"] == "%Y-%m-%d"):
							datatype = "DATE"
						elif (field["datetime"]) and ((field["datetime-format"] == "%Y-%m-%d %H:%M") or (field["datetime-format"] == "%Y-%m-%d %H:%M:%S")):
								datatype = "DATETIME"
						elif (field["time"]) and ((field["time-format"] == "%H:%M") or (field["time-format"] == "%H:%M:%S")):
							datatype = "TIME"
						elif (field["length-min"] > 0) and (field["length-min"] == field["length-max"]):
							datatype = "CHAR({})".format(field["length-min"])
						elif field["integer"]:
							 datatype = "INT"
						elif field["float"]:
							datatype = "FLOAT"
						else:
							length = field["length-max"]
							if length <= 10: length = 10
							elif length <= 25: length = 25
							elif length <= 50: length = 50
							elif length <= 100: length = 100
							elif length <= 255: length = 255
							else: length = 1024
							datatype = "VARCHAR({})".format(length)
							
						columns.append("\t{} {} {}".format(column_name, datatype, null))
						
					# Create full SQL
					def escape(s):
						s = s.replace("\\", "\\\\")
						s = s.replace("'", "\\'")
						s = s.replace("\t", "\\t")
						s = s.replace("\r", "\\r")
						s = s.replace("\n", "\\n")
						return s
					parts = [table_name, ",\n".join(columns), escape(os.path.abspath(input_filename)), table_name, escape(self.inputs["delim"]), escape(self.inputs["enclose"]), escape(os.linesep), " IGNORE 1 LINES" if self.inputs["headers"] else ""]
					results = "CREATE TABLE {}(\n{}\n);\n\nLOAD DATA INFILE '{}' IGNORE INTO TABLE {} FIELDS TERMINATED BY '{}' OPTIONALLY ENCLOSED BY '{}' LINES TERMINATED BY '{}'{};\n".format(*parts)
				else:
					raise Exception("Unknown action: " + self.inputs["action"])
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
		
		return "Processed " + str(i) + " records sucessfully"

# ===========================================================================================================================
# Class to perform basic actions
class BasicAction(Action):
	# -----------------------------------------------------------------------------------------------------------------------
	# Processes the input file(s) and performs the user's action
	def action(self):
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
					for line in DataReader(f_in):
						b += len(line.encode(self.inputs["encoding"])) + len(os.linesep)
						
						# Skip the header row on all files except the first one, unless each file gets its own output
						if (f == 0) or (not headers) or inidvidual_outputs:
							# Parse the data
							record = self.parse_data(line, self.inputs["delim"], self.inputs["enclose"], self.inputs["escape"])
							
							# Column error checking
							columns = []
							if isinstance(self.inputs["columns"], list): columns = self.inputs["columns"]
							if isinstance(self.inputs["column"], int): columns.append(self.inputs["column"])
							for c in columns:
								if c > len(record):
									raise Exception("Column #" + str(c) + " does not exist on line " + str(j+1) + " of " + input_filename)
							
							# Process the record
							if self.inputs["action"] == "combine":
								record.append("Original Filename" if headers else os.path.basename(input_filename))
							elif self.inputs["action"] == "filter":
								if not headers:
									match = re.search(self.inputs["pattern"], record[self.inputs["column"]])
									if not((match and not self.inputs["invert"]) or (not match and self.inputs["invert"])): record = None
							elif self.inputs["action"] == "head":
								if (j+1) > self.inputs["lines"]: break
							elif self.inputs["action"] == "remove-columns":
								if self.inputs["invert"]:
									self.inputs["columns"] = list(set(range(len(record))) - set(self.inputs["columns"]))
									self.inputs["columns"].sort(reverse=True)
									self.inputs["invert"] = False
								for k in self.inputs["columns"]: del record[k]
							elif self.inputs["action"] == "repair":
								pass
							elif self.inputs["action"] == "replace-pattern":
								if not headers: record[self.inputs["column"]] = re.sub(self.inputs["find"], self.inputs["replace"], record[self.inputs["column"]])
							elif self.inputs["action"] == "replace-value":
								if not headers: record[self.inputs["column"]] = record[self.inputs["column"]].replace(self.inputs["find"], self.inputs["replace"])
							else:
								raise Exception("Unknown action: " + self.inputs["action"])
							
							# Output the record
							if record is not None:
								f_out.write(self.unparse_data(record, self.inputs["delim"], self.inputs["enclose"], self.inputs["escape"]) + "\n")
							
							if not headers:
								j += 1
								i += 1
						
						if headers: headers = False
						
						if self.inputs["action"] == "head":
							self.progress("Record: " + str(i), started, i, self.inputs["lines"] * len(self.inputs["input"]))
						else:
							self.progress("Record: " + str(i), started, b, total_bytes)
				finally:
					if f_out != sys.stdout: f_out.close()
			finally:
				if f_in != sys.stdin: f_in.close()
				if in_place: shutil.move(output_filename + ".tmp", output_filename)
				
			f += 1
		
		return "Processed " + str(i) + " records sucessfully"

# ===========================================================================================================================
# Class to perform actions on fixed width files
class FixedAction(Action):
	# -----------------------------------------------------------------------------------------------------------------------
	# Processes the input file(s) and performs the user's action
	def action(self):
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
					for line in DataReader(f_in):
						b += len(line.encode(self.inputs["encoding"])) + len(os.linesep)
						
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
								raise Exception("Unknown action: " + self.inputs["action"])
							
							if not headers:
								j += 1
								i += 1
						
						if headers: headers = False
						
						self.progress("Record: " + str(i), started, b, total_bytes)
				finally:
					if f_out != sys.stdout: f_out.close()
			finally:
				if f_in != sys.stdin: f_in.close()
				if in_place: shutil.move(output_filename + ".tmp", output_filename)
				
			f += 1
		
		return "Processed " + str(i) + " records sucessfully"
		
	# -----------------------------------------------------------------------------------------------------------------------
	# Parses a fixed length record
	def parse_fixed(self, line, fixed_map, fixed_length, i):
		if len(line) != fixed_length: raise Exception("Line #" + str(i) + " is not the required " + str(fixed_length) + " characters long. It is " + str(len(line)) + " characters long.")
		
		record = []
		position = 0
		for m in fixed_map:
			record.append(line[position:(position + m)].strip())
			position += m

		return record
		
	# -----------------------------------------------------------------------------------------------------------------------
	# Unparses a fixed length record
	def unparse_fixed(self, record, fixed_map, fixed_length):
		line = ""
		i = 0
		for column in record:
			line += column.ljust(fixed_map[i])[0:fixed_map[i]]
			i += 1
		
		return line

# ===========================================================================================================================
# Class to perform actions that have multiple output files per input file
class SplitAction(Action):
	# -----------------------------------------------------------------------------------------------------------------------
	# Processes the input file(s) and performs the user's action
	def action(self):
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
				header_record = None
				j = 0
				for line in DataReader(f_in):
					b += len(line.encode(self.inputs["encoding"])) + len(os.linesep)
					
					# Parse the data
					record = self.parse_data(line, self.inputs["delim"], self.inputs["enclose"], self.inputs["escape"])
					
					# Column error checking
					c = self.inputs["column"]
					if isinstance(c, int) and (c > len(record)):
						raise Exception("Column #" + str(c) + " does not exist on line " + str(j+1) + " of " + input_filename)
					
					# Save the header
					if headers and (j == 0):
						header_record = record
						if self.inputs["action"] == "uncombine": del header_record[-1]
					
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
						elif self.inputs["action"] == "uncombine":
							output_filename_record = dirname + record[-1]
							del record[-1]
						else:
							raise Exception("Unknown action: " + self.inputs["action"])
						
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
								if header_record is not None: f_out.write(self.unparse_data(header_record, self.inputs["delim"], self.inputs["enclose"], self.inputs["escape"]) + "\n")
						
						# Output the data
						f_out.write(self.unparse_data(record, self.inputs["delim"], self.inputs["enclose"], self.inputs["escape"]) + "\n")
						
						j += 1
						i += 1
						
						self.progress("Record: " + str(i), started, b, total_bytes)
					else:
						headers = False
			finally:
				if f_in != sys.stdin: f_in.close()
				if f_out is not None: f_out.close()
				
			f += 1
		
		return "Processed " + str(i) + " records sucessfully"
