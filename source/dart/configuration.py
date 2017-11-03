#############################################################################################################################
# dart - Analyze and manipulate delimited data files.
# Configuration class
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
from hydra import BaseConfiguration
from hydra import localize_dir

# ===========================================================================================================================
# Class to validate the config file
class Configuration(BaseConfiguration):
	# -----------------------------------------------------------------------------------------------------------------------
	# Validates the config file
	def validate(self):
		errors = ""
		
		start_folder = self.conf.get("start-folder", "")
		if start_folder != "":
			start_folder = localize_dir(start_folder)
			if not os.path.isdir(start_folder): errors += start_folder +" is not a valid directory\n"
				
		if errors != "": raise Exception("The following errors occurred when parsing " + self.filename + "\n\n" + errors)
