#!/usr/bin/python
# -*- coding: utf-8 -*-

###########################################################################
## Speedrun.com (unofficial) Global leaderboard
## Copyright (C) 2017 Samuel Therrien
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU Affero General Public License as published
## by the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Affero General Public License for more details.
##
## You should have received a copy of the GNU Affero General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.
##
## Contact:
## samuel.06@hotmail.com
###########################################################################

from oauth2client.service_account import ServiceAccountCredentials
import sys
import os.path

##try:
##    with open(os.path.join(sys._MEIPASS,"WCL_API_KEY.txt"), mode="r") as f: API_KEY = f.readline()
##except AttributeError:
##    print("API_KEY not in sys._MEIPASS. Looking for file on local computer.")
##    try:
##        with open("C:\ProgramData\WCL report analyser\WCL_API_KEY.txt", mode="r") as f: API_KEY = f.readline()
##    except FileNotFoundError as exception:
##        raise AnalyserError({"error":"API_KEY not found", "details":exception})
API_KEY = ""

scope = ["https://spreadsheets.google.com/feeds"]
CREDENTIALS_PATH = None
try:
    CREDENTIALS = os.path.join(sys._MEIPASS,"JSON_CREDENTIALS.json")
except AttributeError:
    print("CREDENTIALS not in sys._MEIPASS. Looking for file on local computer.")
    CREDENTIALS = "C:\ProgramData\Speedrun.com (unofficial) global leaderboard\JSON_CREDENTIALS.json"
finally:
    try:
        credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS, scope)
    except FileNotFoundError as exception:
        raise AnalyserError({"error":"CREDENTIALS not found", "details":exception})

COL_USERNAME = 2
COL_POINTS = 3
COL_LAST_UPDATE = 4
COL_USERID = 5
ROW_FIRST = 3

MIN_LEADERBOARD_SIZE = 4
# Highest 9 decimals constant to: Give a score for 20th rank with 30 runners
if   MIN_LEADERBOARD_SIZE == 3: EXP_DECREASE_CONST = 0.160265062
elif MIN_LEADERBOARD_SIZE == 4: EXP_DECREASE_CONST = 0.159850138
elif MIN_LEADERBOARD_SIZE == 5: EXP_DECREASE_CONST = 0.159415772
elif MIN_LEADERBOARD_SIZE == 6: EXP_DECREASE_CONST = 0.158960230

HTTPERROR_RETRY_DELAY = 5
HTTP_RETRYABLE_ERRORS = [401, 420, 500, 502]
