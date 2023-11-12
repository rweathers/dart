#! /usr/bin/python3

"""dart unit tests."""

#############################################################################################################################
# dart
# Test script
#
# Copyright © 2017, 2018, 2019, 2020, 2021, 2023 Ryan Weathers, All Rights Reserved.
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
import tempfile
from datetime import datetime
from inspect import cleandoc
from dart import *

def test_combine(inputs):
	"""Test combine action."""
	
	inputs.update({
		"action":"combine",
		"input" :["{tmp}/test-input-file1.csv", "{tmp}/test-input-file2.csv", "{tmp}/test-input-file3.csv"],
		"output":"{tmp}/test-output.csv"
	})
	
	# Test with and without headers
	test_cases_1 = {True:"headers", False:"no headers"}
	for test_val_1, test_desc_1 in test_cases_1.items():
		inputs["headers"] = test_val_1
		
		description = [inputs["action"], test_desc_1]
		
		contents_input = "foo,bar\nbar,foo\n"
		contents_output = contents_input * len(inputs["input"])
		if inputs["headers"]:
			h = "field1,field2\n"
			contents_input = h + contents_input
			contents_output = h + contents_output
		
		message = "Processed 6 records sucessfully"
		
		test_helper(", ".join(description), BasicAction, inputs, contents_input, contents_output, message)
	
def test_filter(inputs):
	"""Test filter action."""
	
	inputs.update({
		"action" :"filter",
		"column" :1,
		"pattern":"foo",
		"input"  :["{tmp}/test-input-file1.csv", "{tmp}/test-input-file2.csv", "{tmp}/test-input-file3.csv"]
	})
	
	# Test with and without headers
	test_cases_1 = {True:"headers", False:"no headers"}
	for test_val_1, test_desc_1 in test_cases_1.items():
		inputs["headers"] = test_val_1
		
		# Test single, multiple and in-place outputs
		test_cases_2 = {"test-output.csv":"single", "{{f}}-out{{e}}":"multiple", "{{f}}{{e}}":"in-place"}
		for test_val_2, test_desc_2 in test_cases_2.items():
			inputs["output"] = "{tmp}/" + test_val_2
			
			# Test without and with invert
			test_cases_3 = {False:"not inverted", True:"inverted"}
			for test_val_3, test_desc_3 in test_cases_3.items():
				inputs["invert"] = test_val_3
				
				description = [inputs["action"], test_desc_1, test_desc_2, test_desc_3]
				
				contents_input = "foo,bar\nbar,foo\n"
				contents_output = "foo,bar\n" if not inputs["invert"] else "bar,foo\n"
				if test_desc_2 == "single": contents_output = contents_output * len(inputs["input"])
				if inputs["headers"]:
					h = "field1,field2\n"
					contents_input = h + contents_input
					contents_output = h + contents_output
				
				message = "Processed 6 records sucessfully"
				
				test_helper(", ".join(description), BasicAction, inputs, contents_input, contents_output, message)
	
def test_head(inputs):
	"""Test head action."""
	
	inputs.update({
		"action":"head",
		"lines" :5,
		"input" :["{tmp}/test-input-file1.csv", "{tmp}/test-input-file2.csv", "{tmp}/test-input-file3.csv"]
	})
	
	# Test with and without headers
	test_cases_1 = {True:"headers", False:"no headers"}
	for test_val_1, test_desc_1 in test_cases_1.items():
		inputs["headers"] = test_val_1
		
		# Test single, multiple and in-place outputs
		test_cases_2 = {"test-output.csv":"single", "{{f}}-out{{e}}":"multiple", "{{f}}{{e}}":"in-place"}
		for test_val_2, test_desc_2 in test_cases_2.items():
			inputs["output"] = "{tmp}/" + test_val_2
			
			description = [inputs["action"], test_desc_1, test_desc_2]
			
			d = "foo,bar\n"
			rows = 10
			contents_input = d * rows
			contents_output = d * inputs["lines"]
			if test_desc_2 == "single": contents_output = contents_output * len(inputs["input"])
			if inputs["headers"]:
				h = "field1,field2\n"
				contents_input = h + contents_input
				contents_output = h + contents_output
			
			message = "Processed 15 records sucessfully"
			
			test_helper(", ".join(description), BasicAction, inputs, contents_input, contents_output, message)
	
def test_remove_columns(inputs):
	"""Test remove columns action."""
	
	inputs.update({
		"action" :"remove-columns",
		"columns":"1,3-5",
		"input"  :["{tmp}/test-input-file1.csv", "{tmp}/test-input-file2.csv", "{tmp}/test-input-file3.csv"]
	})
	
	# Test with and without headers
	test_cases_1 = {True:"headers", False:"no headers"}
	for test_val_1, test_desc_1 in test_cases_1.items():
		inputs["headers"] = test_val_1
		
		# Test single, multiple and in-place outputs
		test_cases_2 = {"test-output.csv":"single", "{{f}}-out{{e}}":"multiple", "{{f}}{{e}}":"in-place"}
		for test_val_2, test_desc_2 in test_cases_2.items():
			inputs["output"] = "{tmp}/" + test_val_2
		
			# Test without and with invert
			test_cases_3 = {False:"not inverted", True:"inverted"}
			for test_val_3, test_desc_3 in test_cases_3.items():
				inputs["invert"] = test_val_3
				
				description = [inputs["action"], test_desc_1, test_desc_2, test_desc_3]
				
				rows = 3
				contents_input = "a,b,c,d,e,f\n" * rows
				contents_output = '"b","f"\n' if not inputs["invert"] else '"a","c","d","e"\n'
				contents_output = contents_output * rows
				if test_desc_2 == "single": contents_output = contents_output * len(inputs["input"])
				if inputs["headers"]:
					contents_input = "1,2,3,4,5,6\n" + contents_input
					h = '"2","6"\n' if not inputs["invert"] else '"1","3","4","5"\n'
					contents_output = h + contents_output
				
				message = "Processed 9 records sucessfully"
				
				test_helper(", ".join(description), BasicAction, inputs, contents_input, contents_output, message)

def test_repair(inputs):
	"""Test repair action."""
	
	inputs.update({
		"action":"repair",
		"input" :["{tmp}/test-input-file1.csv", "{tmp}/test-input-file2.csv", "{tmp}/test-input-file3.csv"]
	})
	
	# Test with and without headers
	test_cases_1 = {True:"headers", False:"no headers"}
	for test_val_1, test_desc_1 in test_cases_1.items():
		inputs["headers"] = test_val_1
		
		# Test single, multiple and in-place outputs
		test_cases_2 = {"test-output.csv":"single", "{{f}}-out{{e}}":"multiple", "{{f}}{{e}}":"in-place"}
		for test_val_2, test_desc_2 in test_cases_2.items():
			inputs["output"] = "{tmp}/" + test_val_2
			
			description = [inputs["action"], test_desc_1, test_desc_2]
			
			contents_input = "foo,bar\nbar,foo\n"
			contents_output = '"foo","bar"\n"bar","foo"\n'
			if test_desc_2 == "single": contents_output = contents_output * len(inputs["input"])
			if inputs["headers"]:
				contents_input = "field1,field2\n" + contents_input
				contents_output = '"field1","field2"\n' + contents_output
			
			message = "Processed 6 records sucessfully"
			
			test_helper(", ".join(description), BasicAction, inputs, contents_input, contents_output, message)
	
def test_replace_pattern(inputs):
	"""Test replace pattern action."""
	
	inputs.update({
		"action" :"replace-pattern",
		"column" :1,
		"find"   :"f.*",
		"replace":"bar",
		"input"  :["{tmp}/test-input-file1.csv", "{tmp}/test-input-file2.csv", "{tmp}/test-input-file3.csv"]
	})
	
	# Test with and without headers
	test_cases_1 = {True:"headers", False:"no headers"}
	for test_val_1, test_desc_1 in test_cases_1.items():
		inputs["headers"] = test_val_1
		
		# Test single, multiple and in-place outputs
		test_cases_2 = {"test-output.csv":"single", "{{f}}-out{{e}}":"multiple", "{{f}}{{e}}":"in-place"}
		for test_val_2, test_desc_2 in test_cases_2.items():
			inputs["output"] = "{tmp}/" + test_val_2
			
			description = [inputs["action"], test_desc_1, test_desc_2]
			
			contents_input = "foo\nbar\nfoo\nbar\n"
			contents_output = '"bar"\n"bar"\n"bar"\n"bar"\n'
			if test_desc_2 == "single": contents_output = contents_output * len(inputs["input"])
			if inputs["headers"]:
				contents_input = "field1\n" + contents_input
				contents_output = '"field1"\n' + contents_output
			
			message = "Processed 12 records sucessfully"
			
			test_helper(", ".join(description), BasicAction, inputs, contents_input, contents_output, message)
	
def test_replace_value(inputs):
	"""Test replace value action."""
	
	inputs.update({
		"action" :"replace-value",
		"column" :1,
		"find"   :"foo",
		"replace":"bar",
		"input"  :["{tmp}/test-input-file1.csv", "{tmp}/test-input-file2.csv", "{tmp}/test-input-file3.csv"]
	})
	
	# Test with and without headers
	test_cases_1 = {True:"headers", False:"no headers"}
	for test_val_1, test_desc_1 in test_cases_1.items():
		inputs["headers"] = test_val_1
		
		# Test single, multiple and in-place outputs
		test_cases_2 = {"test-output.csv":"single", "{{f}}-out{{e}}":"multiple", "{{f}}{{e}}":"in-place"}
		for test_val_2, test_desc_2 in test_cases_2.items():
			inputs["output"] = "{tmp}/" + test_val_2
			
			description = [inputs["action"], test_desc_1, test_desc_2]
			
			contents_input = "foo\nbar\nfoo\nbar\n"
			contents_output = '"bar"\n"bar"\n"bar"\n"bar"\n'
			if test_desc_2 == "single": contents_output = contents_output * len(inputs["input"])
			if inputs["headers"]:
				contents_input = "field1\n" + contents_input
				contents_output = '"field1"\n' + contents_output
			
			message = "Processed 12 records sucessfully"
			
			test_helper(", ".join(description), BasicAction, inputs, contents_input, contents_output, message)

def test_delim_to_fixed(inputs):
	"""Test delim to fixed action."""
	
	inputs.update({
		"action"    :"delim-to-fixed",
		"definition":"{tmp}/fixed.def".format(tmp=tempfile.gettempdir()),
		"input"     :["{tmp}/test-input-file1.csv", "{tmp}/test-input-file2.csv", "{tmp}/test-input-file3.csv"]
	})
	
	# Write definition file
	writeall("8\n8\n", inputs["definition"])
	try:
		# Test with and without headers
		test_cases_1 = {True:"headers", False:"no headers"}
		for test_val_1, test_desc_1 in test_cases_1.items():
			inputs["headers"] = test_val_1
			
			# Test single, multiple and in-place outputs
			test_cases_2 = {"test-output.csv":"single", "{{f}}-out{{e}}":"multiple", "{{f}}{{e}}":"in-place"}
			for test_val_2, test_desc_2 in test_cases_2.items():
				inputs["output"] = "{tmp}/" + test_val_2
				
				description = [inputs["action"], test_desc_1, test_desc_2]
				
				contents_input = "foo,bar\nbar,foo\n"
				contents_output = "foo     bar     \nbar     foo     \n"
				if test_desc_2 == "single": contents_output = contents_output * len(inputs["input"])
				if inputs["headers"]:
					contents_input = "field1,field2\n" + contents_input
					contents_output = "field1  field2  \n" + contents_output
				
				message = "Processed 6 records sucessfully"
				
				test_helper(", ".join(description), FixedAction, inputs, contents_input, contents_output, message)
	finally:
		os.remove(inputs["definition"])

def test_fixed_to_delim(inputs):
	"""Test fixed to delim action."""
	
	inputs.update({
		"action"    :"fixed-to-delim",
		"definition":"{tmp}/fixed.def".format(tmp=tempfile.gettempdir()),
		"input"     :["{tmp}/test-input-file1.txt", "{tmp}/test-input-file2.txt", "{tmp}/test-input-file3.txt"]
	})
	
	# Write definition file
	writeall("8\n8\n", inputs["definition"])
	try:
		# Test with and without headers
		test_cases_1 = {True:"headers", False:"no headers"}
		for test_val_1, test_desc_1 in test_cases_1.items():
			inputs["headers"] = test_val_1
			
			# Test single, multiple and in-place outputs
			test_cases_2 = {"test-output.csv":"single", "{{f}}-out{{e}}":"multiple", "{{f}}{{e}}":"in-place"}
			for test_val_2, test_desc_2 in test_cases_2.items():
				inputs["output"] = "{tmp}/" + test_val_2
				
				description = [inputs["action"], test_desc_1, test_desc_2]
				
				contents_input = "foo     bar     \nbar     foo     \n"
				contents_output = '"foo","bar"\n"bar","foo"\n'
				if test_desc_2 == "single": contents_output = contents_output * len(inputs["input"])
				if inputs["headers"]:
					contents_input = "field1  field2  \n" + contents_input
					contents_output = '"field1","field2"\n' + contents_output
				
				message = "Processed 6 records sucessfully"
				
				test_helper(", ".join(description), FixedAction, inputs, contents_input, contents_output, message)
	finally:
		os.remove(inputs["definition"])

def test_split_lines(inputs):
	"""Test split line action."""
	
	inputs.update({
		"action":"split-lines",
		"lines" :2,
		"input" :"{tmp}/test-input-file.csv"
	})
	
	# Test with and without headers
	test_cases_1 = {True:"headers", False:"no headers"}
	for test_val_1, test_desc_1 in test_cases_1.items():
		inputs["headers"] = test_val_1
		
		description = [inputs["action"], test_desc_1]
		
		d = "foo,bar\n"
		rows = 10
		contents_input = d * rows
		contents_output = d * inputs["lines"]
		if inputs["headers"]:
			h = "field1,field2\n"
			contents_input = h + contents_input
			contents_output = h + contents_output
		
		contents_outputs = {}
		for i in range(1, int(rows/inputs["lines"])+1): contents_outputs["{{tmp}}/test-input-file-{}.csv".format(i)] = contents_output
		
		message = "Processed 10 records sucessfully"
		
		test_helper_split(", ".join(description), inputs, contents_input, contents_outputs, message)

def test_split_value(inputs):
	"""Test split value action."""
	
	inputs.update({
		"action":"split-value",
		"column":1,
		"input" :"{tmp}/test-input-file.csv"
	})
	
	# Test with and without headers
	test_cases_1 = {True:"headers", False:"no headers"}
	for test_val_1, test_desc_1 in test_cases_1.items():
		inputs["headers"] = test_val_1
		
		description = [inputs["action"], test_desc_1]
		
		rows = 5
		contents_input = "foo,bar\nbar,foo\n" * rows
		contents_outputs = {}
		contents_outputs["{tmp}/test-input-file-foo.csv"] = 'foo,bar\n' * rows
		contents_outputs["{tmp}/test-input-file-bar.csv"] = 'bar,foo\n' * rows
		if inputs["headers"]:
			h = "field1,field2\n"
			contents_input = h + contents_input
			contents_outputs["{tmp}/test-input-file-foo.csv"] = h + contents_outputs["{tmp}/test-input-file-foo.csv"]
			contents_outputs["{tmp}/test-input-file-bar.csv"] = h + contents_outputs["{tmp}/test-input-file-bar.csv"]
		
		message = "Processed 10 records sucessfully"
		
		test_helper_split(", ".join(description), inputs, contents_input, contents_outputs, message)

def test_analyze(inputs):
	"""Test analyze action."""
	
	inputs.update({
		"action":"analyze",
		"lines" :0,
		"input" :["{tmp}/test-input-file1.csv", "{tmp}/test-input-file2.csv"],
		"output":"{{f}}-out{{e}}"
	})
	
	# Test with and without headers
	test_cases_1 = {True:"headers", False:"no headers"}
	for test_val_1, test_desc_1 in test_cases_1.items():
		inputs["headers"] = test_val_1
		
		description = [inputs["action"], test_desc_1]
		
		contents_input = cleandoc('''
			Alice,foobar,01234,123,123,07/16/17,13:00,2017-07-16 15:00:00,1
			Bob,,12345,123,123.45,07/17/17,14:00,2017-07-16 16:00:00,0
		''')

		contents_output = cleandoc('''
			"Data Type","Text","Text","Text","Integer","Decimal","Date","Time","Date/Time","Boolean"
			"Minimum Length","3","6","5","3","3","8","5","19","1"
			"Average Length","4.0","6.0","5.0","3.0","4.5","8.0","5.0","19.0","1.0"
			"Maximum Length","5","6","5","3","6","8","5","19","1"
			"Minimum Value","Alice","foobar","01234","123","123.0","07/16/17","13:00","2017-07-16 15:00:00","0"
			"Average Value","","","","123.0","123.225","","","","0.5"
			"Maximum Value","Bob","foobar","12345","123","123.45","07/17/17","14:00","2017-07-16 16:00:00","1"
			"Empty Values","0","1","0","0","0","0","0","0","0"
			"Distinct Values","2","2","2","1","2","2","2","2","2"
			"Total Values","2","2","2","2","2","2","2","2","2"
		''')
		
		if inputs["headers"]:
			contents_input = "Name,Text,Zip,Integer,Decimal,Date,Time,Date/Time,Boolean\n" + contents_input
			contents_output = '"Column Name","Name","Text","Zip","Integer","Decimal","Date","Time","Date/Time","Boolean"\n' + contents_output
		else:
			contents_output = '"Column Name","field-0","field-1","field-2","field-3","field-4","field-5","field-6","field-7","field-8"\n' + contents_output
		
		message = "Processed 4 records sucessfully"
		
		test_helper(", ".join(description), AnalyzeAction, inputs, contents_input, contents_output, message)
	
def test_sql_import(inputs):
	"""Test SQL import action."""
	
	inputs.update({
		"action":"sql-import",
		"lines" :0,
		"input" :["{tmp}/test-input-file1.csv"],
		"output":"{{f}}.sql"
	})
	
	# Test with and without headers
	test_cases_1 = {True:"headers", False:"no headers"}
	for test_val_1, test_desc_1 in test_cases_1.items():
		inputs["headers"] = test_val_1
		
		description = [inputs["action"], test_desc_1]
		
		contents_input = cleandoc('''
			Alice,foobar,01234,123,123,07/16/17,13:00,2017-07-16 15:00:00,1
			Bob,\\N,12345,-123,123.45,07/17/17,14:00,2017-07-16 16:00:00,0
		''')
		
		filename = "{}{}{}".format(tempfile.gettempdir(), os.sep, "test-input-file1.csv").replace("\\", "\\\\")
		contents_output = None
		if inputs["headers"]:
			contents_input = "Name,Text,Zip,Integer,Decimal,Date,Time,Date/Time,Boolean\n" + contents_input
			contents_output = cleandoc('''
				CREATE TABLE test_input_file1(
					`name` VARCHAR(10) NOT NULL,
					`text` CHAR(6) NULL,
					`zip` CHAR(5) NOT NULL,
					`integer` TINYINT NOT NULL,
					`decimal` DECIMAL NOT NULL,
					`date` CHAR(8) NOT NULL,
					`time` TIME NOT NULL,
					`datetime` DATETIME NOT NULL,
					`boolean` TINYINT UNSIGNED NOT NULL
				);
				
				LOAD DATA INFILE '{filename}' IGNORE INTO TABLE test_input_file1 FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' LINES TERMINATED BY '\\n' IGNORE 1 LINES;
			''').format(filename=filename).replace(" " * 8, "\t")
		else:
			contents_output = cleandoc('''
				CREATE TABLE test_input_file1(
					`field_0` VARCHAR(10) NOT NULL,
					`field_1` CHAR(6) NULL,
					`field_2` CHAR(5) NOT NULL,
					`field_3` TINYINT NOT NULL,
					`field_4` DECIMAL NOT NULL,
					`field_5` CHAR(8) NOT NULL,
					`field_6` TIME NOT NULL,
					`field_7` DATETIME NOT NULL,
					`field_8` TINYINT UNSIGNED NOT NULL
				);
				
				LOAD DATA INFILE '{filename}' IGNORE INTO TABLE test_input_file1 FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' LINES TERMINATED BY '\\n';
			''').format(filename=filename).replace(" " * 8, "\t")
		
		message = "Processed 2 records sucessfully"
		
		test_helper(", ".join(description), AnalyzeAction, inputs, contents_input, contents_output, message)

def test_sql_prepare(inputs):
	"""Test SQL prepare action."""
	
	inputs.update({
		"action" :"sql-prepare",
		"input"  :["{tmp}/test-input-file1.csv", "{tmp}/test-input-file2.csv", "{tmp}/test-input-file3.csv"]
	})
	
	# Test with and without headers
	test_cases_1 = {True:"headers", False:"no headers"}
	for test_val_1, test_desc_1 in test_cases_1.items():
		inputs["headers"] = test_val_1
		
		# Test single, multiple and in-place outputs
		test_cases_2 = {"test-output.csv":"single", "{{f}}-out{{e}}":"multiple", "{{f}}{{e}}":"in-place"}
		for test_val_2, test_desc_2 in test_cases_2.items():
			inputs["output"] = "{tmp}/" + test_val_2
			
			description = [inputs["action"], test_desc_1, test_desc_2]
			
			contents_input = 'foo,,"1,000$","($1,000.00)",01-01-23,Jan 01 2023,8:30 pm,bar1\n'
			contents_output = '"foo","\\N","1000","-1000.0","2023-01-01","2023-01-01","20:30:00","bar1"\n'
			if test_desc_2 == "single": contents_output = contents_output * len(inputs["input"])
			if inputs["headers"]:
				contents_input = "field1,field2,field3,field4,field5,field6,field7,field8\n" + contents_input
				contents_output = '"field1","field2","field3","field4","field5","field6","field7","field8"\n' + contents_output
			
			message = "Processed 3 records sucessfully"
			
			test_helper(", ".join(description), BasicAction, inputs, contents_input, contents_output, message)

def test_helper(description, action, inputs, contents_input, contents_output, expected_message):
	"""Test helper."""
	
	outputs = []
	try:
		print2("Testing: {} ".format(description))
		
		if "column"  not in inputs: inputs["column"]  = ""
		if "columns" not in inputs: inputs["columns"] = ""
		
		inputs = inputs.copy()
		
		# Add tmp dir to filenames
		tmp = []
		for f in inputs["input"]: tmp.append(f.format(tmp=tempfile.gettempdir()))
		inputs["input"] = tmp
		inputs["output"] = inputs["output"].format(tmp=tempfile.gettempdir())
		
		# Create input files
		for f in inputs["input"]: writeall(contents_input, f, inputs["encoding"])
		
		# Perform the action
		action = action(dict(inputs))
		actual_message = action.execute()
		
		# Check the message
		if actual_message != expected_message:
			print("FAIL\nExpected message: {}\nActual message: {}".format(expected_message, actual_message))
			return
		
		# Get the output filename(s)
		if "{" in inputs["output"]:
			for f in inputs["input"]:
				basename = os.path.basename(f)
				(filename, ext) = os.path.splitext(basename)
				outputs.append(inputs["output"].format(f=filename, e=ext))
		else:
			outputs.append(inputs["output"])
		
		# Check the output file(s)	
		for f in outputs:
			text = readall(f, inputs["encoding"])
			if text.strip() != contents_output.strip():
				print("FAIL\nExpected output contents:\n{}\nActual output contents:\n{}".format(contents_output, text))
				return
		
		print("PASS")
	finally:
		# Clean up test files
		for f in set(inputs["input"] + outputs): os.remove(f)

def test_helper_split(description, inputs, contents_input, contents_outputs, expected_message):
	"""Split test helper."""
	
	try:
		print2("Testing: {} ".format(description))
		
		if "column"  not in inputs: inputs["column"]  = ""
		if "columns" not in inputs: inputs["columns"] = ""
		
		inputs = inputs.copy()
		
		# Add tmp dir to filenames
		inputs["input"] = inputs["input"].format(tmp=tempfile.gettempdir())
		
		# Create input files
		writeall(contents_input, inputs["input"], inputs["encoding"])
		
		# Perform the action
		action = SplitAction(dict(inputs))
		actual_message = action.execute()
		
		# Check the message
		if actual_message != expected_message:
			print("FAIL\nExpected message: {}\nActual message: {}".format(expected_message, actual_message))
			return
		
		# Check the output files
		for f in contents_outputs:
			text = readall(f.format(tmp=tempfile.gettempdir()), inputs["encoding"])
			if text.strip() != contents_outputs[f].strip():
				print("FAIL\nExpected output contents:\n{}\nActual output contents:\n{}".format(contents_outputs[f], text))
				return
		
		print("PASS")
	finally:
		# Clean up test files
		os.remove(inputs["input"])
		for f in contents_outputs: os.remove(f.format(tmp=tempfile.gettempdir()))

def print2(text):
	"""Print the given text and leave cursor on same line."""
	width = 75
	print(text.ljust(width, ".")[0:width], end=" ", flush=True)

def writeall(text, filename, encoding="utf-8"):
	"""Write a string to a file."""
	with open(filename, mode="w", encoding=encoding) as f: f.write(text)

def readall(filename, encoding="utf-8"):
	"""Read a file into a string."""	
	with open(filename, mode="r", encoding=encoding) as f: return f.read()
	
def main():
	"""Run all tests."""
	
	try:
		print("")
		
		conf = Configuration(program)
		
		test_combine(conf.conf.copy())
		test_filter(conf.conf.copy())
		test_head(conf.conf.copy())
		test_remove_columns(conf.conf.copy())
		test_repair(conf.conf.copy())
		test_replace_pattern(conf.conf.copy())
		test_replace_value(conf.conf.copy())
		
		test_delim_to_fixed(conf.conf.copy())
		test_fixed_to_delim(conf.conf.copy())
		
		test_split_lines(conf.conf.copy())
		test_split_value(conf.conf.copy())
		
		test_analyze(conf.conf.copy())
		test_sql_import(conf.conf.copy())
		
		test_sql_prepare(conf.conf.copy())
		
		print("")
	except Exception as e:
		import traceback
		print("\n\n{}".format(traceback.format_exc()))

main()
