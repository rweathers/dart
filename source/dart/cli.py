#############################################################################################################################
# dart - Analyze and manipulate delimited data files.
# CLI class
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
from hydra import BaseCLI
from dart.action import AnalyzeAction
from dart.action import BasicAction
from dart.action import FixedAction
from dart.action import SplitAction

# ===========================================================================================================================
# Class to define the command line interface
class CLI(BaseCLI):
	# -----------------------------------------------------------------------------------------------------------------------
	# Defines the command line arguments
	def define_arguments(self):
		self.arguments = [
			("help"      , "h", "Show help information"                , "boolean"),
			("version"   , "V", "Show version information"             , "boolean"),
			("license"   , "l", "Show license information"             , "boolean"),
			("quiet"     , "q", "Suppress all output"                  , "boolean"),
			("verbose"   , "v", "Enable verbose output\n"              , "boolean"),
			
			("action"    , "a", "Action to perform (see below)"        , "value"),
			("column"    , "" , "Column index, starting a 0"           , "value"),
			("columns"   , "" , "Column indexes, starting at 0 (1)"    , "value"),
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
			("encoding"  , "c", "File encoding"                        , "value"),
			("headers"   , "H", "Input contains headers"               , "boolean")
		]
		
		# Flags used: a, c, d, e, h, i, l, o, q, s, v, H, V
	
	# -----------------------------------------------------------------------------------------------------------------------
	# Prints the program's help information
	def print_help(self):
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
		
		print("  combine - combine multiple files and append original filename")
		print("    dart -a combine -i *.csv -o b.csv")
		print("")
		
		print("  delim-to-fixed - covert a delimited file to a fixed width file")
		print("    dart -a delim-to-fixed --definition fixed.def -i a.csv -o b.txt")
		print("")
		
		print("  filter - filter records based on a column's value")
		print("    dart -a filter --column 0 --pattern " + q + "^A" + q + " -i a.csv -o b.csv")
		print("    dart -a filter --column 0 --pattern " + q + "^A" + q + " -i a.csv -o b.csv --invert")
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
		print("    dart -a replace-pattern --column 0 --find " + q + "f(.*)" + q + " --replace " + q + "b\\1" + q + " -i a.csv " + continue_char + "\n      -o b.csv")
		print("")
		
		print("  replace-value - replace a value in a column with another")
		print("    dart -a replace-value --column 0 --find foo --replace bar -i a.csv -o b.csv")
		print("")
		
		print("  split-lines - split one file into many based on number of lines")
		print("    dart -a split-lines --lines 500 -i a.csv")
		print("")
		
		print("  split-value - split one file into many based on a column's value")
		print("    dart -a split-value --column 0 -i a.csv")
		print("")
		
		print("  sql-import - create SQL CREATE TABLE and LOAD DATA statements")
		print("    dart --a sql-import -i a.csv -o b.sql --headers")
		print("    dart --a sql-import -i a.csv -o b.sql --headers --lines 1000")
		print("")
		
		print("  uncombine - inverse of combine")
		print("    dart -a uncombine -i a.csv")
		print("")
		
	# -----------------------------------------------------------------------------------------------------------------------
	# Returns the action class to use
	def get_action(self, inputs):
		if inputs["action"] in ["delim-to-fixed", "fixed-to-delim"]:
			return FixedAction
		elif inputs["action"] in ["split-lines", "split-value", "uncombine"]:
			return SplitAction
		elif inputs["action"] in ["analyze", "sql-import"]:
			return AnalyzeAction
		else:
			return BasicAction
