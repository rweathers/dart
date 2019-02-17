#! /usr/bin/python3

"""dart unit tests."""

#############################################################################################################################
# dart
# Test script
#
# Copyright © 2017, 2018, 2019 Ryan Weathers, All Rights Reserved.
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
from datetime import datetime
from hydra import progress
from dart import *

last_update = 0

def test_combine():
	"""Test combine action."""
	
	inputs = {
		"action"  :"combine",
		"input"   :["/tmp/test-input-file1.csv", "/tmp/test-input-file2.csv", "/tmp/test-input-file3.csv"],	
		"delim"   :",",
		"enclose" :"\"",
		"escape"  :"\"",
		"encoding":"utf-8"
	}
	
	output_progress("Starting Test: " + inputs["action"])
	
	contents_input = "foo,bar\nbar,foo\n"
	
	contents_output_combined_headers = 'foo,bar\nbar,foo\nbar,foo\nbar,foo\n'
	contents_output_combined_no_headers = 'foo,bar\nbar,foo\nfoo,bar\nbar,foo\nfoo,bar\nbar,foo\n'
	
	# Test single output only
	inputs["output"] = "/tmp/test-output.csv"
	
	# Test with and without headers
	for h in [False, True]:
		inputs["headers"] = h
		
		contents_output = None
		if "{" in inputs["output"]:
			contents_output = contents_output_individual
		elif inputs["headers"]:
			contents_output = contents_output_combined_headers
		else:
			contents_output = contents_output_combined_no_headers
		
		message = "Processed {0} records sucessfully".format(3 if inputs["headers"] else 6)
		
		success = test_helper(BasicAction, inputs, contents_input, contents_output, message)
		if not success: return
	
	print("Test Passed: " + inputs["action"])
	
def test_filter():
	"""Test filter action."""
	
	inputs = {
		"action"  :"filter",
		"column"  :1,
		"pattern" :"foo",
		"input"   :["/tmp/test-input-file1.csv", "/tmp/test-input-file2.csv", "/tmp/test-input-file3.csv"],	
		"delim"   :",",
		"enclose" :"\"",
		"escape"  :"\"",
		"encoding":"utf-8"
	}
	
	output_progress("Starting Test: " + inputs["action"])
	
	contents_input = "field1,field2\nfoo,bar\nbar,foo\n"
	
	# Test with and without invert
	for i in [False, True]:
		inputs["invert"] = i
		
		if not inputs["invert"]:
			contents_output_combined_headers = 'field1,field2\n' + ('bar,foo\n' * 3)
			contents_output_combined_no_headers = 'bar,foo\n' * 3
			contents_output_individual_headers = 'field1,field2\nbar,foo\n'
			contents_output_individual_no_headers = 'bar,foo\n'
		else:
			contents_output_combined_headers = 'field1,field2\n' + ('foo,bar\n' * 3)
			contents_output_combined_no_headers = 'field1,field2\nfoo,bar\n' * 3
			contents_output_individual_headers = 'field1,field2\nfoo,bar\n'
			contents_output_individual_no_headers = 'field1,field2\nfoo,bar\n'
		
		# Test single, multiple and in-place outputs
		for o in ["test-output.csv", "{f}-out{e}", "{f}{e}"]:
			inputs["output"] = "/tmp/" + o
			
			# Test with and without headers
			for h in [False, True]:
				inputs["headers"] = h
				
				contents_output = None
				if ("{" in inputs["output"]) and inputs["headers"]:
					contents_output = contents_output_individual_headers
				elif ("{" in inputs["output"]) and not inputs["headers"]:
					contents_output = contents_output_individual_no_headers
				elif inputs["headers"]:
					contents_output = contents_output_combined_headers
				else:
					contents_output = contents_output_combined_no_headers
				
				message = "Processed {0} records sucessfully".format(6 if inputs["headers"] else 9)
				
				success = test_helper(BasicAction, inputs, contents_input, contents_output, message)
				if not success: return
	
	print("Test Passed: " + inputs["action"])
	
def test_head():
	"""Test head action."""
	
	inputs = {
		"action"  :"head",
		"input"   :["/tmp/test-input-file1.csv", "/tmp/test-input-file2.csv", "/tmp/test-input-file3.csv"],	
		"lines"   :5,
		"delim"   :",",
		"enclose" :"\"",
		"escape"  :"\"",
		"encoding":"utf-8"
	}
	
	output_progress("Starting Test: " + inputs["action"])
	
	contents_input = "foo,bar\n" * 10
	
	contents_output_combined_headers = 'foo,bar\n' * 16
	contents_output_combined_no_headers = 'foo,bar\n' * 15
	contents_output_individual_headers = 'foo,bar\n' * 6
	contents_output_individual_no_headers = 'foo,bar\n' * 5
	
	# Test single, multiple and in-place outputs
	for o in ["test-output.csv", "{f}-out{e}", "{f}{e}"]:
		inputs["output"] = "/tmp/" + o
		
		# Test with and without headers
		for h in [False, True]:
			inputs["headers"] = h
			
			contents_output = None
			if ("{" in inputs["output"]) and inputs["headers"]:
				contents_output = contents_output_individual_headers
			elif ("{" in inputs["output"]) and not inputs["headers"]:
				contents_output = contents_output_individual_no_headers	
			elif inputs["headers"]:
				contents_output = contents_output_combined_headers
			else:
				contents_output = contents_output_combined_no_headers
			
			message = "Processed {0} records sucessfully".format(15)
			
			success = test_helper(BasicAction, inputs, contents_input, contents_output, message)
			if not success: return
	
	print("Test Passed: " + inputs["action"])
	
def test_remove_columns():
	"""Test remove columns action."""
	
	inputs = {
		"action"  :"remove-columns",
		"columns" :"0,2-4",
		"input"   :["/tmp/test-input-file1.csv", "/tmp/test-input-file2.csv", "/tmp/test-input-file3.csv"],	
		"delim"   :",",
		"enclose" :"\"",
		"escape"  :"\"",
		"encoding":"utf-8"
	}
	
	output_progress("Starting Test: " + inputs["action"])
	
	contents_input = "a,b,c,d,e,f\n" * 3
	
	# Test with and without invert
	for i in [False, True]:
		inputs["invert"] = i

		if not i:
			contents_output_combined_headers    = '"b","f"\n' * 7
			contents_output_combined_no_headers = '"b","f"\n' * 9
			contents_output_individual          = '"b","f"\n' * 3
		else:
			contents_output_combined_headers    = '"a","c","d","e"\n' * 7
			contents_output_combined_no_headers = '"a","c","d","e"\n' * 9
			contents_output_individual          = '"a","c","d","e"\n' * 3
		
		# Test single, multiple and in-place outputs
		for o in ["test-output.csv", "{f}-out{e}", "{f}{e}"]:
			inputs["output"] = "/tmp/" + o
			
			# Test with and without headers
			for h in [False, True]:
				inputs["headers"] = h
				
				contents_output = None
				if "{" in inputs["output"]:
					contents_output = contents_output_individual
				elif inputs["headers"]:
					contents_output = contents_output_combined_headers
				else:
					contents_output = contents_output_combined_no_headers
				
				message = "Processed {0} records sucessfully".format(6 if inputs["headers"] else 9)
				
				success = test_helper(BasicAction, inputs, contents_input, contents_output, message)
				if not success: return
		
	print("Test Passed: " + inputs["action"])

def test_repair():
	"""Test repair action."""
	
	inputs = {
		"action"  :"repair",
		"input"   :["/tmp/test-input-file1.csv", "/tmp/test-input-file2.csv", "/tmp/test-input-file3.csv"],	
		"delim"   :",",
		"enclose" :"\"",
		"escape"  :"\"",
		"encoding":"utf-8"
	}
	
	output_progress("Starting Test: " + inputs["action"])
	
	contents_input = "foo,bar\nbar,foo\n"
	
	contents_output_combined_headers = '"foo","bar"\n' + ('"bar","foo"\n' * 3)
	contents_output_combined_no_headers = '"foo","bar"\n"bar","foo"\n' * 3
	contents_output_individual = '"foo","bar"\n"bar","foo"\n'
	
	# Test single, multiple and in-place outputs
	for o in ["test-output.csv", "{f}-out{e}", "{f}{e}"]:
		inputs["output"] = "/tmp/" + o
		
		# Test with and without headers
		for h in [False, True]:
			inputs["headers"] = h
			
			contents_output = None
			if "{" in inputs["output"]:
				contents_output = contents_output_individual
			elif inputs["headers"]:
				contents_output = contents_output_combined_headers
			else:
				contents_output = contents_output_combined_no_headers
			
			message = "Processed {0} records sucessfully".format(3 if inputs["headers"] else 6)
			
			success = test_helper(BasicAction, inputs, contents_input, contents_output, message)
			if not success: return
	
	print("Test Passed: " + inputs["action"])
	
def test_replace_pattern():
	"""Test replace pattern action."""
	
	inputs = {
		"action"  :"replace-pattern",
		"column"  :0,
		"find"    :"f.*",
		"replace" :"bar",
		"input"   :["/tmp/test-input-file1.csv", "/tmp/test-input-file2.csv", "/tmp/test-input-file3.csv"],	
		"delim"   :",",
		"enclose" :"\"",
		"escape"  :"\"",
		"encoding":"utf-8"
	}
	
	output_progress("Starting Test: " + inputs["action"])
	
	contents_input = "foo\nbar\nfoo\nbar\n"
	
	contents_output_combined_headers = '"foo"\n' + '"bar"\n' * 9
	contents_output_combined_no_headers = '"bar"\n' * 12
	contents_output_individual_headers = '"foo"\n"bar"\n"bar"\n"bar"\n'
	contents_output_individual_no_headers = '"bar"\n"bar"\n"bar"\n"bar"\n'
	
	# Test single, multiple and in-place outputs
	for o in ["test-output.csv", "{f}-out{e}", "{f}{e}"]:
		inputs["output"] = "/tmp/" + o
		
		# Test with and without headers
		for h in [False, True]:
			inputs["headers"] = h
			
			contents_output = None
			if "{" in inputs["output"]:
				if inputs["headers"]:
					contents_output = contents_output_individual_headers
				else:
					contents_output = contents_output_individual_no_headers
			else:
				if inputs["headers"]:
					contents_output = contents_output_combined_headers
				else:
					contents_output = contents_output_combined_no_headers
			
			message = "Processed {0} records sucessfully".format(9 if inputs["headers"] else 12)
			
			success = test_helper(BasicAction, inputs, contents_input, contents_output, message)
			if not success: return
	
	print("Test Passed: " + inputs["action"])
	
def test_replace_value():
	"""Test replace value action."""
	
	inputs = {
		"action"  :"replace-value",
		"column"  :0,
		"find"    :"foo",
		"replace" :"bar",
		"input"   :["/tmp/test-input-file1.csv", "/tmp/test-input-file2.csv", "/tmp/test-input-file3.csv"],	
		"delim"   :",",
		"enclose" :"\"",
		"escape"  :"\"",
		"encoding":"utf-8"
	}
	
	output_progress("Starting Test: " + inputs["action"])
	
	contents_input = "foo\nbar\nfoo\nbar\n"
	
	contents_output_combined_headers = '"foo"\n' + '"bar"\n' * 9
	contents_output_combined_no_headers = '"bar"\n' * 12
	contents_output_individual_headers = '"foo"\n"bar"\n"bar"\n"bar"\n'
	contents_output_individual_no_headers = '"bar"\n"bar"\n"bar"\n"bar"\n'
	
	# Test single, multiple and in-place outputs
	for o in ["test-output.csv", "{f}-out{e}", "{f}{e}"]:
		inputs["output"] = "/tmp/" + o
		
		# Test with and without headers
		for h in [False, True]:
			inputs["headers"] = h
			
			contents_output = None
			if "{" in inputs["output"]:
				if inputs["headers"]:
					contents_output = contents_output_individual_headers
				else:
					contents_output = contents_output_individual_no_headers
			else:
				if inputs["headers"]:
					contents_output = contents_output_combined_headers
				else:
					contents_output = contents_output_combined_no_headers
			
			message = "Processed {0} records sucessfully".format(9 if inputs["headers"] else 12)
			
			success = test_helper(BasicAction, inputs, contents_input, contents_output, message)
			if not success: return
	
	print("Test Passed: " + inputs["action"])

def test_delim_to_fixed():
	"""Test delim to fixed action."""
	
	inputs = {
		"action"    :"delim-to-fixed",
		"definition":"/tmp/fixed.def",
		"input"     :["/tmp/test-input-file1.csv", "/tmp/test-input-file2.csv", "/tmp/test-input-file3.csv"],
		"delim"     :",",
		"enclose"   :"\"",
		"escape"    :"\"",
		"encoding"  :"utf-8"
	}
	
	output_progress("Starting Test: " + inputs["action"])
	
	# Write definition file
	writeall("5\n5\n", inputs["definition"])
	
	contents_input = "foo,bar\nbar,foo\n"
	
	contents_output_combined_headers = 'foo  bar  \n' + ('bar  foo  \n' * 3)
	contents_output_combined_no_headers = 'foo  bar  \nbar  foo  \n' * 3
	contents_output_individual = 'foo  bar  \nbar  foo  \n'
	
	# Test single, multiple and in-place outputs
	for o in ["test-output.txt", "{f}-out{e}", "{f}{e}"]:
		inputs["output"] = "/tmp/" + o
		
		# Test with and without headers
		for h in [False, True]:
			inputs["headers"] = h
			
			contents_output = None
			if "{" in inputs["output"]:
				contents_output = contents_output_individual
			elif inputs["headers"]:
				contents_output = contents_output_combined_headers
			else:
				contents_output = contents_output_combined_no_headers
			
			message = "Processed {0} records sucessfully".format(3 if inputs["headers"] else 6)
			
			success = test_helper(FixedAction, inputs, contents_input, contents_output, message)
			if not success: return
	
	os.remove(inputs["definition"])
	
	print("Test Passed: " + inputs["action"])
	
def test_fixed_to_delim():
	"""Test fixed to delim action."""
	
	inputs = {
		"action"    :"fixed-to-delim",
		"definition":"/tmp/fixed.def",
		"input"     :["/tmp/test-input-file1.txt", "/tmp/test-input-file2.txt", "/tmp/test-input-file3.txt"],
		"delim"     :",",
		"enclose"   :"\"",
		"escape"    :"\"",
		"encoding"  :"utf-8"
	}
	
	output_progress("Starting Test: " + inputs["action"])
	
	# Write definition file
	writeall("5\n5\n", inputs["definition"])
	
	contents_input = "foo  bar  \nbar  foo  \n"
	
	contents_output_combined_headers = '"foo","bar"\n' + ('"bar","foo"\n' * 3)
	contents_output_combined_no_headers = '"foo","bar"\n"bar","foo"\n' * 3
	contents_output_individual = '"foo","bar"\n"bar","foo"\n'
	
	# Test single, multiple and in-place outputs
	for o in ["test-output.csv", "{f}-out{e}", "{f}{e}"]:
		inputs["output"] = "/tmp/" + o
		
		# Test with and without headers
		for h in [False, True]:
			inputs["headers"] = h
			
			contents_output = None
			if "{" in inputs["output"]:
				contents_output = contents_output_individual
			elif inputs["headers"]:
				contents_output = contents_output_combined_headers
			else:
				contents_output = contents_output_combined_no_headers
			
			message = "Processed {0} records sucessfully".format(3 if inputs["headers"] else 6)
			
			success = test_helper(FixedAction, inputs, contents_input, contents_output, message)
			if not success: return
	
	os.remove(inputs["definition"])
	
	print("Test Passed: " + inputs["action"])

def test_split_lines():
	"""Test split line action."""
	
	inputs = {
		"action"  :"split-lines",
		"lines"   :2,
		"input"   :"/tmp/test-input-file.csv",
		"delim"   :",",
		"enclose" :"\"",
		"escape"  :"\"",
		"encoding":"utf-8"
	}
	
	output_progress("Starting Test: " + inputs["action"])
	
	contents_input_headers = "FOO,BAR\n" + "foo,bar\n" * 10
	contents_output_headers = 'FOO,BAR\n' + 'foo,bar\n' * 2
	
	contents_input_no_headers = "foo,bar\n" * 10
	contents_output_no_headers = 'foo,bar\n' * 2
	
	contents_outputs_headers = {}
	for i in range(1, 6): contents_outputs_headers["/tmp/test-input-file-{i}.csv".format(i=i)] = contents_output_headers
	
	contents_outputs_no_headers = {}
	for i in range(1, 6): contents_outputs_no_headers["/tmp/test-input-file-{i}.csv".format(i=i)] = contents_output_no_headers
	
	# Test with and without headers
	for h in [False, True]:
		inputs["headers"] = h
		
		contents_input   = contents_input_headers  if h else contents_input_no_headers
		contents_outputs = contents_outputs_headers if h else contents_outputs_no_headers
		
		message = "Processed 10 records sucessfully"
		
		success = test_helper_split(inputs, contents_input, contents_outputs, message)
		if not success: return
	
	print("Test Passed: " + inputs["action"])

def test_split_value():
	"""Test split value action."""
	
	inputs = {
		"action"  :"split-value",
		"column"  :0,
		"input"   :"/tmp/test-input-file.csv",
		"delim"   :",",
		"enclose" :"\"",
		"escape"  :"\"",
		"encoding":"utf-8"
	}
	
	output_progress("Starting Test: " + inputs["action"])
	
	contents_input_headers = "FOO,BAR\n" + "foo,bar\nbar,foo\n" * 5	
	contents_outputs_headers = {}
	contents_outputs_headers["/tmp/test-input-file-foo.csv"] = 'FOO,BAR\n' + 'foo,bar\n' * 5
	contents_outputs_headers["/tmp/test-input-file-bar.csv"] = 'FOO,BAR\n' + 'bar,foo\n' * 5
	
	contents_input_no_headers = "foo,bar\nbar,foo\n" * 5
	contents_outputs_no_headers = {}
	contents_outputs_no_headers["/tmp/test-input-file-foo.csv"] = 'foo,bar\n' * 5
	contents_outputs_no_headers["/tmp/test-input-file-bar.csv"] = 'bar,foo\n' * 5
	
	# Test with and without headers
	for h in [False, True]:
		inputs["headers"] = h
		
		contents_input   = contents_input_headers  if h else contents_input_no_headers
		contents_outputs = contents_outputs_headers if h else contents_outputs_no_headers
		
		message = "Processed 10 records sucessfully"
		
		success = test_helper_split(inputs, contents_input, contents_outputs, message)
		if not success: return
	
	print("Test Passed: " + inputs["action"])

def test_analyze():
	"""Test analyze action."""
	
	inputs = {
		"action"  :"analyze",
		"lines"   :0,
		"input"   :["/tmp/test-input-file1.csv", "/tmp/test-input-file2.csv"],
		"output"  :"{f}-out{e}",
		"delim"   :",",
		"enclose" :"\"",
		"escape"  :"\"",
		"encoding":"utf-8"
	}
	
	output_progress("Starting Test: " + inputs["action"])
	
	contents_input_data = '''Alice,foobar,01234,123,123,07/16/17,13:00,2017-07-16 15:00:00,1
Bob,,12345,123,123.45,07/17/17,14:00,2017-07-16 16:00:00,0
'''
	contents_output_data = '''"Data Type","Text","Text","Text","Integer","Decimal","Date","Time","Date/Time","Boolean"
"Minimum Length","3","6","5","3","3","8","5","19","1"
"Average Length","4.0","6.0","5.0","3.0","4.5","8.0","5.0","19.0","1.0"
"Maximum Length","5","6","5","3","6","8","5","19","1"
"Minimum Value","Alice","foobar","01234","123","123.0","07/16/17","13:00","2017-07-16 15:00:00","0"
"Average Value","","","","123.0","123.225","","","","0.5"
"Maximum Value","Bob","foobar","12345","123","123.45","07/17/17","14:00","2017-07-16 16:00:00","1"
"Blank Values","0","1","0","0","0","0","0","0","0"
"Distinct Values","2","1","2","1","2","2","2","2","2"
"Total Values","2","2","2","2","2","2","2","2","2"
'''

	contents_input_headers = 'Name,Text,Zip,Integer,Decimal,Date,Time,Date/Time,Boolean\n' + contents_input_data
	contents_output_headers = '"Column Name","Name","Text","Zip","Integer","Decimal","Date","Time","Date/Time","Boolean"\n' + contents_output_data
	
	contents_input_no_headers = contents_input_data
	contents_output_no_headers = '"Column Name","field-0","field-1","field-2","field-3","field-4","field-5","field-6","field-7","field-8"\n' + contents_output_data
	
	# Test with and without headers
	for h in [False, True]:
		inputs["headers"] = h
		
		contents_input = None
		contents_output = None
		if inputs["headers"]:
			contents_input = contents_input_headers
			contents_output = contents_output_headers
		else:
			contents_input = contents_input_no_headers
			contents_output = contents_output_no_headers
		
		message = "Processed 4 records sucessfully"
		
		success = test_helper(AnalyzeAction, inputs, contents_input, contents_output, message)
		if not success: return
	
	print("Test Passed: " + inputs["action"])
	
def test_sql_import():
	"""Test SQL import action."""
	
	inputs = {
		"action"  :"sql-import",
		"lines"   :0,
		"input"   :["/tmp/test-input-file1.csv"],
		"output"  :"{f}.sql",
		"delim"   :",",
		"enclose" :"\"",
		"escape"  :"\"",
		"encoding":"utf-8"
	}
	
	output_progress("Starting Test: " + inputs["action"])
	
	contents_input_data = '''Alice,foobar,01234,123,123,07/16/17,13:00,2017-07-16 15:00:00,1
Bob,,12345,123,123.45,07/17/17,14:00,2017-07-16 16:00:00,0
'''

	contents_input_headers = 'Name,Text,Zip,Integer,Decimal,Date,Time,Date/Time,Boolean\n' + contents_input_data
	contents_output_headers = '''CREATE TABLE test_input_file1(
	name VARCHAR(10) NOT NULL,
	text CHAR(6) NULL,
	zip CHAR(5) NOT NULL,
	integer CHAR(3) NOT NULL,
	decimal FLOAT NOT NULL,
	date CHAR(8) NOT NULL,
	time TIME NOT NULL,
	datetime DATETIME NOT NULL,
	boolean CHAR(1) NOT NULL
);

LOAD DATA INFILE '/tmp/test-input-file1.csv' IGNORE INTO TABLE test_input_file1 FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' LINES TERMINATED BY '\\n' IGNORE 1 LINES;
'''
	
	contents_input_no_headers = contents_input_data
	contents_output_no_headers = '''CREATE TABLE test_input_file1(
	field_0 VARCHAR(10) NOT NULL,
	field_1 CHAR(6) NULL,
	field_2 CHAR(5) NOT NULL,
	field_3 CHAR(3) NOT NULL,
	field_4 FLOAT NOT NULL,
	field_5 CHAR(8) NOT NULL,
	field_6 TIME NOT NULL,
	field_7 DATETIME NOT NULL,
	field_8 CHAR(1) NOT NULL
);

LOAD DATA INFILE '/tmp/test-input-file1.csv' IGNORE INTO TABLE test_input_file1 FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' LINES TERMINATED BY '\\n';
'''
	
	# Test with and without headers
	for h in [False, True]:
		inputs["headers"] = h
		
		contents_input = None
		contents_output = None
		if inputs["headers"]:
			contents_input = contents_input_headers
			contents_output = contents_output_headers
		else:
			contents_input = contents_input_no_headers
			contents_output = contents_output_no_headers
		
		message = "Processed 2 records sucessfully"
		
		success = test_helper(AnalyzeAction, inputs, contents_input, contents_output, message)
		if not success: return
	
	print("Test Passed: " + inputs["action"])

def test_helper(action, inputs, contents_input, contents_output, expected_message):
	"""Test helper."""
	
	if "column"  not in inputs: inputs["column"]  = ""
	if "columns" not in inputs: inputs["columns"] = ""
	
	# Create input files
	for f in inputs["input"]: writeall(contents_input, f, inputs["encoding"])
	
	# Perform the action
	action = action(dict(inputs), output_progress)
	message = action.execute()
	output_progress("")
	
	# Check the message
	if message != expected_message:
		print("TEST FAILED: " + inputs["action"])
		print("Expected message: " + expected_message)
		print("Actual message: " + message)
		return False
	
	# Get the output filename(s)
	outputs = []
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
		if text != contents_output:
			print("TEST FAILED: " + inputs["action"])
			print("Expected output contents:")
			print(contents_output)
			print("Actual output contents:")
			print(text)
			return False
	
	# Clean up test files
	for f in set(inputs["input"] + outputs): os.remove(f)
	
	return True
	
def test_helper_split(inputs, contents_input, contents_outputs, expected_message):
	"""Split test helper."""
	
	if "column"  not in inputs: inputs["column"]  = ""
	if "columns" not in inputs: inputs["columns"] = ""
	
	# Create input files
	writeall(contents_input, inputs["input"], inputs["encoding"])
	
	# Perform the action
	action = SplitAction(dict(inputs), output_progress)
	message = action.execute()
	output_progress("")
	
	# Check the message
	if message != expected_message:
		print("TEST FAILED: " + inputs["action"])
		print("Expected message: " + expected_message)
		print("Actual message: " + message)
		return False
	
	# Check the output files
	for f in contents_outputs:
		text = readall(f, inputs["encoding"])
		if text != contents_outputs[f]:
			print("TEST FAILED: " + inputs["action"])
			print("Expected output contents:")
			print(contents_outputs[f])
			print("Actual output contents:")
			print(text)
			return False
	
	# Clean up test files
	os.remove(inputs["input"])
	for f in contents_outputs: os.remove(f)
	
	return True
	
def output_progress(text, started=None, processed=None, total=None):
	"""Callback to output progress."""
	
	global last_update
	
	p = progress(last_update, text, started, processed, total)
	if p is not None:
		last_update = p[0]
		print(p[1].ljust(80)[0:80-1] + "\r", end="", flush=True)

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
		
		test_combine()
		test_filter()
		test_head()
		test_remove_columns()
		test_repair()
		test_replace_pattern()
		test_replace_value()
		
		test_delim_to_fixed()
		test_fixed_to_delim()
		
		test_split_lines()
		test_split_value()
		
		test_analyze()
		test_sql_import()
		
		print("")
	except Exception as e:
		import traceback
		print("ERROR: " + str(e))
		print(traceback.format_exc())

main()
