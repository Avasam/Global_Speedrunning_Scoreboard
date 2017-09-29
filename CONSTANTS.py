#!/usr/bin/python
# -*- coding: utf-8 -*-

###########################################################################
# Ava's Global speedrunning leaderboard
# Copyright (C) 2017 Samuel Therrien
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact:
# samuel.06@hotmail.com
###########################################################################

import os.path
import sys
from oauth2client.service_account import ServiceAccountCredentials

# try:
#     with open(os.path.join(sys._MEIPASS,"WCL_API_KEY.txt"), mode="r") as f: API_KEY = f.readline()
# except AttributeError:
#     print("API_KEY not in sys._MEIPASS. Looking for file on local computer.")
#     try:
#         with open("C:\ProgramData\WCL report analyser\WCL_API_KEY.txt", mode="r") as f: API_KEY = f.readline()
API_KEY = ""
SPREADSHEET_ID = "1kY983c46wQP155V0sBoXUFVu4wg9qlErU4MqGVjIUV0"
scope = ["https://spreadsheets.google.com/feeds"]
CREDENTIALS_PATH = None
try:
    CREDENTIALS_PATH = os.path.join(sys._MEIPASS, "JSON_CREDENTIALS.json")
except AttributeError:
    print("CREDENTIALS not in sys._MEIPASS. Looking for file on local computer.")
    CREDENTIALS_PATH = "C:\ProgramData\Global speedrunning leaderboard\JSON_CREDENTIALS.json"
finally:
    credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_PATH, scope)

SEPARATOR = "-" * 64
AUTOUPDATER_OFFSET = 4600

COL_USERNAME = 2
COL_POINTS = 3
COL_LAST_UPDATE = 4
COL_USERID = 5
ROW_FIRST = 3
MIN_LEADERBOARD_SIZE = 3
# Higher means more importance towards relatively good runs
# Lower means more importance towards playing multiple games
DEVIATION_MULTIPLIER = 3

HTTPERROR_RETRY_DELAY = 5
HTTP_RETRYABLE_ERRORS = [401, 420, 500, 502]
