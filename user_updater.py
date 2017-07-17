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
from CONSTANTS import *
from collections import Counter
import gspread
import math
import requests
import time
from threading import Thread
import traceback
import time

class UserUpdaterError(Exception):
    """ raise UserUpdaterError({"error":"On Status Label", "details":"Details of error"}) """
    pass

class Run():
    game = ""
    category = ""
    variables = {}
    place = 0
    _points = 0
    __leaderboard_size = 0

    def __init__(self, game, category, variables, place):
        self.game = game
        self.category = category
        self.variables = variables
        self.place = place
        self.__set_points()

    def __str__(self):
        return "Run: <Game: "+self.game+", Category: "+self.category+", "+str(self.place)+"/"+str(self._leaderboard_size)+">"

    #TODO: currently a player can be penalized by runs w/o videos as the leaderboard size will shrink but not its rank
    def __set_leaderboard_size(self):
        self._leaderboard_size = get_leaderboard_size(self.game, self.category, self.variables)

    def __set_points(self):
        self._points = 0
        # Check if the place is worth any point
        self.__set_leaderboard_size()
        print(self)
        if self._leaderboard_size >= self.place and self._leaderboard_size >= MIN_LEADERBOARD_SIZE:
            # Give points according to the formula
            formula_result = math.log(self._leaderboard_size-MIN_LEADERBOARD_SIZE+2) * (1/EXP_DECREASE_CONST) * math.exp(-(EXP_DECREASE_CONST*(self.place-1)))
            self._points += min(self._leaderboard_size-self.place, math.floor(formula_result))

class User():
    _points = 0
    _name = ""
    _ID = ""
    _banned = False

    def __init__(self, ID_or_name):
        self._ID = ID_or_name
        self._name = ID_or_name

    def __str__(self):
        return "User: <" + self._name + ", " + str(self._points) + ", " + self._ID+">"

    def set_code_and_name(self):
        try:
            url = "http://www.speedrun.com/api/v1/users/"+self._ID
            infos = get_file(url)
            if "status" in infos.keys(): raise UserUpdaterError({"error":str(infos["status"])+" (speedrun.com)", "details":infos["message"]})
            if infos["data"]["role"] != "banned":
                self._ID = infos["data"]["id"]
                self._name = infos["data"]["names"].get("international")
                japanese_name = infos["data"]["names"].get("japanese")
                if japanese_name: self._name += " "+japanese_name
            else:
                self._banned = True
                self._points = 0
        except UserUpdaterError as exception:
            threadsException.append(exception.args[0])
        except Exception:
            threadsException.append({"error":"Unhandled", "details":traceback.format_exc()})

    def set_points(self):
        try:
            if not self._banned:
                url = "http://www.speedrun.com/api/v1/users/"+self._ID+"/personal-bests?top=25&max=200"
                PBs = get_file(url)
                if "status" in PBs.keys(): raise UserUpdaterError({"error":str(infos["status"])+" (speedrun.com)", "details":PBs["message"]})
                self._points = 0
                update_progress(0, len(PBs["data"]))
                threads = []
                for pb in PBs["data"]:
                    threads.append(Thread(target=set_points_thread, args=(pb,)))
                for t in threads: t.start()
                for t in threads: t.join()
                if self._banned: sef._points = 0 # In case the banned flag has been set mid-thread
            else: self._points = 0
        except UserUpdaterError as exception:
            threadsException.append(exception.args[0])
        except Exception as exception:
            threadsException.append({"error":"Unhandled", "details":traceback.format_exc()})
        finally:
            update_progress(1, 0)

        def set_points_thread(pb):
            try:
                # Check if it's a valid run (has a category, isn't an IL, has video verification)
                if pb["run"]["category"] and not pb["run"]["level"] and pb["run"].get("videos"): # TODO?: allow runs for games that have levels, but no category?
                    #Get a list of the game's subcategory variables
                    url = "http://www.speedrun.com/api/v1/games/"+pb["run"]["game"]+"/variables?max=200"
                    game_variables = get_file(url)
                    game_subcategory_ids = []
                    for game_variable in game_variables["data"]:
                        if game_variable["is-subcategory"] == True:
                            game_subcategory_ids.append(game_variable["id"])

                    pb_subcategory_variables = {}
                    # For every variable in the run...
                    for pb_var_id, pb_var_value in pb["run"]["values"].items():
                        # ...find if said variable is one of the game's subcategories...
                        if pb_var_id in game_subcategory_ids:
                            # ... and add it to the run's subcategory variables
                            pb_subcategory_variables[pb_var_id] = pb_var_value
                            break

                    run = Run(pb["run"]["game"], pb["run"]["category"], pb_subcategory_variables, pb["place"])
                    self._points += run._points
            except UserUpdaterError as exception:
                threadsException.append(exception.args[0])
            except Exception as exception:
                threadsException.append({"error":"Unhandled", "details":traceback.format_exc()})
            finally:
                update_progress(1, 0)



def get_leaderboard_size(p_game, p_category, p_variables):
    try:
        url = "http://www.speedrun.com/api/v1/leaderboards/"+p_game+"/category/"+p_category+"?video-only=true&max=200"
        for var_id, var_value in p_variables.items(): url += "&var-"+var_id+"="+var_value
        leaderboard = get_file(url)
        size = 0
        size =+ len(leaderboard["data"]["runs"])
        return size
    except UserUpdaterError as exception:
        threadsException.append(exception.args[0])
    except Exception as exception:
        threadsException.append({"error":"Unhandled", "details":traceback.format_exc()})

def get_file(p_url):
    """
    Returns the content of "url" parsed as JSON dict.

    Parameters
    ----------
    url : str   # The url to query
    """
##    debugstr = p_url.replace(API_KEY, "****************************************")+"\n"
    debugstr = "\n"+p_url
    print(debugstr)
    while True:
        try:
            data = requests.get(p_url)
            data.raise_for_status()
            break
        except requests.exceptions.ConnectionError as exception:
            raise UserUpdaterError({"error":"Can't establish connexion to speedrun.com", "details":exception})
        except requests.exceptions.HTTPError as exception:
            debugstr = exception.args[0]+". Retrying in "+str(HTTPERROR_RETRY_DELAY)+" seconds."
            if data.status_code in HTTP_RETRYABLE_ERRORS:
                print(debugstr)
                time.sleep(HTTPERROR_RETRY_DELAY)
            else: raise UserUpdaterError({"error":"HTTPError "+str(data.status_code), "details":exception.args[0]})

    data = data.json()

    debugstr = str(type(data))+":"+str(data)
    if type(data) != dict: print(debugstr)
    if "error" in data.keys(): raise UserUpdaterError({"error":data["status"], "details":data["error"]})
    return(data)

def update_progress(p_current, p_max):
    global statusLabel_current
    global statusLabel_max
    statusLabel_current += p_current
    statusLabel_max += p_max
    statusLabel.configure(text="Fetching online data from speedrun.com. Please wait... ["+str(int(statusLabel_current/statusLabel_max*100) or 0)+"%] ("+str(statusLabel_current)+"/"+str(statusLabel_max)+")")

global worksheet
worksheet = None
global gs_client
gs_client = None
def get_updated_user(p_user_ID, p_statusLabel):
    """Called from ui.update_user_thread() and AutoUpdateUsers.run()"""
    global statusLabel
    statusLabel = p_statusLabel
    global statusLabel_current
    statusLabel_current = 0
    global statusLabel_max
    statusLabel_max = 0
    global worksheet
    global gs_client
    global threadsException
    threadsException = []

    #Check if already connected
    if not (gs_client and worksheet):

	#Authentify to Google Sheets API
        statusLabel.configure(text="Establishing connexion to online Spreadsheet...")
        try:
            gs_client = gspread.authorize(credentials)
            print("https://docs.google.com/spreadsheets/d/"+SPREADSHEET_ID+"\n")
            worksheet = gs_client.open_by_key(SPREADSHEET_ID).sheet1
        except gspread.exceptions.SpreadsheetNotFound:
            raise UserUpdaterError({"error":"Spreadsheet not found", "details":"https://docs.google.com/spreadsheets/d/"+SPREADSHEET_ID})

    #Refresh credentials
    gs_client.login()

    statusLabel.configure(text="Fetching online data from speedrun.com. Please wait...")
    user = User(p_user_ID)
    debugstr = "-"*71+"\n"+user._name
    print(debugstr)

    threads = []
    threads.append(Thread(target=user.set_code_and_name))
    threads.append(Thread(target=user.set_points))
    update_progress(0, len(threads))
    for t in threads: t.start()
    for t in threads: t.join()
    update_progress(1, 0) # Because user.set_code_and_name() is too fast

    textOutput = ""
    if threadsException == []:
        if user._points > 0: #TODO: once the database is full, move this in "# If user not found, add a row to the spreadsheet" (user should also be removed from spreadsheet)
            statusLabel.configure(text="Updating the leaderboard...")
            debugstr = "\n"+str(user)
            print(debugstr)

            # Try and find the user by its ID
            worksheet = gs_client.open_by_key(SPREADSHEET_ID).sheet1
            row = 0
            # As of 2017/07/16 with current code using searching by range is faster than col_values most of the time by up to 0.5s
    #        t1 = time.time()
            row_count = worksheet.row_count
            cell_list = worksheet.range(ROW_FIRST, COL_USERID, row_count, COL_USERID)
            for cell in cell_list:
                if cell.value == user._ID:
                    row = cell.row
                    break
    #        t2 = time.time()
    #        row_count = 0
    #        cell_values_list = worksheet.col_values(COL_USERID)
    #        for value in cell_values_list:
    #            row_count += 1
    #            if value == user._ID: row = row_count
    #        t3 = time.time()
    #        print(debugstr = "range took    : " + str(t2-t1) + "seconds\ncol_values took: "+ str(t3-t2) + "seconds")
            timestamp = time.strftime("%Y/%m/%d %H:%M")
            if row >= ROW_FIRST:
                print("User " + user._ID + " found. Updating its cell.")
                cell_list = worksheet.range(row, COL_USERNAME, row, COL_LAST_UPDATE)
                cell_list[0].value = user._name
                cell_list[1].value = user._points
                cell_list[2].value = timestamp
                worksheet.update_cells(cell_list)
            # If user not found, add a row to the spreadsheet
            else:
                debugstr = "User ID " + user._ID + " not found. Adding a new row."
                print(debugstr)
                values = ["=IF($C"+str(row_count+1)+"<$C"+str(row_count)+";$A"+str(row_count)+"+1;$A"+str(row_count)+")",
                          user._name,
                          user._points,
                          timestamp,
                          user._ID]
                worksheet.insert_row(values, index=row_count+1)
        else:
            textOutput = "Not updloading data as " + str(user) + " has a score of 0."
            print(textOutput)
    else:
        errorStrList = []
        for e in threadsException: errorStrList.append("Error: "+str(e["error"])+"\n"+str(e["details"]))
        errorStrCounter = Counter(errorStrList)
        SEPARATOR = "\n"+("-"*64)+"\n"
        errorsStr = ("\n"+SEPARATOR+"Not updloading data as some errors were caught during execution:"+SEPARATOR+"\n")
        for error, count in errorStrCounter.items(): errorsStr += "[x"+str(count)+"] "+str(error)+"\n\n"
        print("[x"+str(count)+"] "+str(error)+"\n\n")
        textOutput += errorsStr

    statusLabel.configure(text="Done! "+("("+str(len(threadsException))+" error"+("s" if len(threadsException) > 1 else "")+")" if threadsException != [] else ""))
    return(textOutput)

class AutoUpdateUsers(Thread):
    BASE_URL = "http://www.speedrun.com/api/v1/users?orderby=signup&max=200&offset=0"
    paused = True
    global statusLabel


    def __init__(self, p_statusLabel, **kwargs):
        Thread.__init__(self, **kwargs)
        self.statusLabel = p_statusLabel

    def run(self):
        url = self.BASE_URL
        while True:
            self.__check_for_pause()
            self.statusLabel.configure(text="Auto-updating userbase...")
            users = get_file(url)
            for user in users["data"]:
                self.__check_for_pause()
                #TODO: Log this better
                while True:
                    try:
                        try:
                            get_updated_user(user["id"], self.statusLabel)
                            break
                        except gspread.exceptions.RequestError as exception:
                            if exception.args[0] in HTTP_RETRYABLE_ERRORS:
                                debugstr = str(exception.args[0])+". Retrying in "+str(HTTPERROR_RETRY_DELAY)+" seconds."
                                print(debugstr)
                                time.sleep(HTTPERROR_RETRY_DELAY)
                            else:
                                raise UserUpdaterError({"error":"Unhandled RequestError", "details":traceback.format_exc()})
                        except Exception:
                            raise UserUpdaterError({"error":"Unhandled", "details":traceback.format_exc()})
                    except UserUpdaterError as exception:
                        debugstr = "Skipping user "+user["id"]+". "+exception.args[0]["details"]
                        print(debugstr)
                        break


            link_found = False
            for link in users["pagination"]["links"]:
                if link["rel"] == "next":
                    url = link["uri"]
                    link_found = True
            if not link_found: url = self.BASE_URL

    def __check_for_pause(self):
        while self.paused:
            pass

def spam_test():
    def spam():
        get_file("http://www.speedrun.com/api/v1/users?max=2")
    while True:
        Thread(target=spam).start()

