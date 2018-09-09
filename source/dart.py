#! /usr/bin/python3

#############################################################################################################################
# dart - Analyze and manipulate delimited data files
#
# Copyright © 2017, 2018 Ryan Weathers, All Rights Reserved.
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
# Version: 0.4.0-beta (2018.09.09)
#############################################################################################################################

from hydra import main
from classes.configuration import Configuration
from classes.cli import CLI
from classes.gui import GUI

program = {
	"name"     :"dart",
	"version"  :"0.4.0-beta",
	"date"     :"09/09/2018",
	"usage"    :"dart --action action [-options] -i input(s) [-o output]",
	"purpose"  :"Analyze and manipulate delimited data files.",
	"url"      :"https://github.com/rweathers/dart",
	"copyright":"Copyright © 2017, 2018 Ryan Weathers, All Rights Reserved.",
	"license"  :"This program is free software: you can redistribute it and/or modify\nit under the terms of the GNU General Public License as published by\nthe Free Software Foundation, either version 3 of the License, or\n(at your option) any later version.\n\nThis program is distributed in the hope that it will be useful,\nbut WITHOUT ANY WARRANTY; without even the implied warranty of\nMERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\nGNU General Public License for more details.\n\nYou should have received a copy of the GNU General Public License\nalong with this program.  If not, see <http://www.gnu.org/licenses/>.",
	"config"   :"{path}dart.ini",
	"error"    :"{path}dart.err",
	"icon-data":"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",
	"icon-file":None
}

main(program, Configuration, CLI, GUI)
