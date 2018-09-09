#############################################################################################################################
# dart - Analyze and manipulate delimited data files.
# GUI class
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

import sys
import tkinter as tk
from tkinter import ttk
from hydra import BaseGUI
from classes.action import AnalyzeAction
from classes.action import BasicAction
from classes.action import FixedAction
from classes.action import SplitAction

# ===========================================================================================================================
# Class to define the graphical user interface
class GUI(BaseGUI):
	# -----------------------------------------------------------------------------------------------------------------------
	# Defines the menu
	def define_menu(self):
		self.menu = [
			("File"    , [("Exit", self.quit)]),
			("Edit"    , [("Reset", self.reset)]),
			("Settings", [("Open Config File", self.open_config)]),
			("Help"    , [("Help", self.show_help), ("About", self.show_about)])
		]
	
	# -----------------------------------------------------------------------------------------------------------------------
	# Defines help information
	def define_help(self, help):
		path = "C:\\example\\" if "win" in sys.platform else "/home/example/"
		
		help.insert(tk.END, "Usage\n\n", "bold")
		help.insert(tk.END, "To use this program, select an Action, enter all necessary fields and click the Submit button.\n\n", "normal")
		
		help.insert(tk.END, "Action\n\n", "italic")
		help.insert(tk.END, """ \u2022 Analyze - analyze a file and output a summary of its contents
 \u2022 Combine - combine multiple files and append original filename
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
		help.insert(tk.END, """ \u2022 Column - column index, starting at 0
 \u2022 Columns - column indexes, starting at 0, separate with commas, you can also use ranges, i.e.: 1,3-5
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
 \u2022 Encoding - file encoding 
 \u2022 Headers? - input contains headers
 
 """, "normal")
		
		help.insert(tk.END, "Configuration File\n\n", "bold")
		help.insert(tk.END, "There is a configuration file at {0}. This file contains settings you can modify. Open it with Settings > Open Config File. You will need to close and reopen the application for any changes to take effect.".format(self.prog["config"]), "normal")
		
		help.config(height = 45)
		help.config(width  = 110)
	
	# -----------------------------------------------------------------------------------------------------------------------
	# Enables all widgets for the current action
	def enable_widgets(self, event=None):
		action = self.widgets["action"].getval()
		actions = {
			"":["action"],
			
			"Combine"        :["action", "input", "input-browse", "output", "output-browse", "delim", "enclose", "escape", "encoding", "headers", "submit"],
			"Filter"         :["action", "input", "input-browse", "output", "output-browse", "delim", "enclose", "escape", "encoding", "headers", "submit", "column", "invert", "pattern"],
			"Head"           :["action", "input", "input-browse", "output", "output-browse", "delim", "enclose", "escape", "encoding", "headers", "submit", "lines"],
			"Remove Columns" :["action", "input", "input-browse", "output", "output-browse", "delim", "enclose", "escape", "encoding", "headers", "submit", "columns", "invert"],
			"Repair"         :["action", "input", "input-browse", "output", "output-browse", "delim", "enclose", "escape", "encoding", "headers", "submit"],
			"Replace Pattern":["action", "input", "input-browse", "output", "output-browse", "delim", "enclose", "escape", "encoding", "headers", "submit", "column", "find", "replace"],
			"Replace Value"  :["action", "input", "input-browse", "output", "output-browse", "delim", "enclose", "escape", "encoding", "headers", "submit", "column", "find", "replace"],
			
			"Delim to Fixed":["action", "input", "input-browse", "output", "output-browse", "delim", "enclose", "escape", "encoding", "headers", "submit", "definition", "definition-browse"],
			"Fixed to Delim":["action", "input", "input-browse", "output", "output-browse", "delim", "enclose", "escape", "encoding", "headers", "submit", "definition", "definition-browse"],
			
			"Split Lines":["action", "input", "input-browse", "delim", "enclose", "escape", "encoding", "headers", "submit", "lines"],
			"Split Value":["action", "input", "input-browse", "delim", "enclose", "escape", "encoding", "headers", "submit", "column"],
			
			"Analyze"   :["action", "input", "input-browse", "output", "output-browse", "delim", "enclose", "escape", "encoding", "headers", "submit", "lines"],
			"SQL Import":["action", "input", "input-browse", "output", "output-browse", "delim", "enclose", "escape", "encoding", "headers", "submit", "lines"]
		}
		
		for name in self.widgets:
			if not isinstance(self.widgets[name], ttk.Notebook):
				self.widgets[name].config(state = (tk.NORMAL if not isinstance(self.widgets[name], ttk.Combobox) else "readonly") if name in actions[action] else tk.DISABLED)
		
		self.update()
	
	# -----------------------------------------------------------------------------------------------------------------------
	# Creates all widgets
	def create_widgets(self):	
		actions = ("", "Analyze", "Combine", "Delim to Fixed", "Filter", "Fixed to Delim", "Head", "Remove Columns", "Repair", "Replace Pattern", "Replace Value", "Split Lines", "Split Value", "SQL Import")
		self.create_combobox(self, "action", "Action", actions)
		self.widgets["action"].bind("<<ComboboxSelected>>", self.enable_widgets)
		
		self.create_entry   (self, "column"    , "Column"    , default=self.conf.get("column", ""))
		self.create_entry   (self, "columns"   , "Columns"   , default=self.conf.get("columns", ""))
		self.create_browse  (self, "definition", "Definition", self.get_input, initialdir=self.conf.get("start-folder", ""), filetypes=[("All Files", ".*")])
		self.create_entry   (self, "find"      , "Find"      , default=self.conf.get("find", ""))
		self.create_entry   (self, "replace"   , "Replace"   , default=self.conf.get("replace", ""))
		self.create_entry   (self, "lines"     , "Lines"     , default=self.conf.get("lines", ""))
		self.create_entry   (self, "pattern"   , "Pattern"   , default=self.conf.get("pattern", ""))
		
		self.create_browse  (self, "input"   , "Input"    , self.get_inputs, initialdir=self.conf.get("start-folder", ""), filetypes=[("All Files", ".*")])
		self.create_browse  (self, "output"  , "Output"   , self.get_output, initialdir=self.conf.get("start-folder", ""), filetypes=[("All Files", ".*")])
		self.create_entry   (self, "delim"   , "Delimiter", default=self.conf.get("delim", ""))
		self.create_entry   (self, "enclose" , "Enclose"  , default=self.conf.get("enclose", ""))
		self.create_entry   (self, "escape"  , "Escape"   , default=self.conf.get("escape", ""))
		self.create_entry   (self, "encoding", "Encoding" , default=self.conf.get("encoding", ""))
		self.create_checkbox(self, "headers" , "Headers?" , 0)
		self.create_checkbox(self, "invert"  , "Invert?"  , 0)
		
		self.create_button  (self, "submit", "Submit", self.action)
		
		self.disable_widgets()
		self.widgets["action"].config(state = tk.NORMAL)

	# -----------------------------------------------------------------------------------------------------------------------
	# Returns the action class to use
	def get_action(self, inputs):
		if inputs["action"] in ["Delim to Fixed", "Fixed to Delim"]:
			return FixedAction
		elif inputs["action"] in ["Split Lines", "Split Value"]:
			return SplitAction
		elif inputs["action"] in ["Analyze", "SQL Import"]:
			return AnalyzeAction
		else:
			return BasicAction
	
	# -----------------------------------------------------------------------------------------------------------------------
	# Resets the widgets
	def reset(self):
		self.set_defaults()
		self.disable_widgets()
		self.widgets["action"].config(state = tk.NORMAL)
