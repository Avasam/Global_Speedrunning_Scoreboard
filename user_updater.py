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
    place = 0
    leaderboard_size = 0
    category = ""
    game = ""

    def __init__(self, game, category, place):
        self.place = place
        self.category = category
        self.game = game

    def __str__(self):
        return "Run: <Game: "+self.game+", Category: "+self.category+", "+str(self.place)+"/"+str(self.leaderboard_size)+">"

    def set_leaderboard_size(self):
        self.leaderboard_size = get_leaderboard_size(self.game, self.category)

class User():
    _points = 0
    _name = ""
    _ID = ""

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
                japanese_name = infos["data"]["names"].get("japanese")
                if japanese_name:
                    self._name = japanese_name + " ("+infos["data"]["names"].get("international")+")"
                else:
                    self._name = infos["data"]["names"].get("international")
            else:
                # TODO: remove from spreadsheet
                pass
        except UserUpdaterError as exception:
            threadsException.append(exception.args[0])
        except Exception as exception:
            threadsException.append({"error":"Unhandled", "details":traceback.format_exc()})

    def set_points(self):
        try:
            def set_points_thread(p_run):
                # Check if the place is worth any point
                p_run.set_leaderboard_size()
                print(p_run)
                if p_run.leaderboard_size >= p_run.place and p_run.leaderboard_size >= MIN_LEADERBOARD_SIZE:
                    # Give points according to the formula
                    formula_result = math.log(p_run.leaderboard_size-MIN_LEADERBOARD_SIZE+2) * (1/EXP_DECREASE_CONST) * math.exp(-(EXP_DECREASE_CONST*(run.place-1)))
                    self._points += min(p_run.leaderboard_size-p_run.place, math.floor(formula_result))
                update_progress(1, 0)

            url = "http://www.speedrun.com/api/v1/users/"+self._ID+"/personal-bests?top=25&max=200"
            PBs = get_file(url)
            if "status" in PBs.keys(): raise UserUpdaterError({"error":str(infos["status"])+" (speedrun.com)", "details":PBs["message"]})
            update_progress(0, len(PBs["data"]))
            self._points = 0
            valid_runs = {}
            for pb in PBs["data"]:
                # Check if it's a valid run
                if pb["run"]["category"] and not pb["run"]["level"] and pb["run"].get("videos"): # TODO?: allow runs that have levels, but no category?
                    run = Run(pb["run"]["game"], pb["run"]["category"], pb["place"])
                    # Update the rank if a run is already known (probably with different variables)
                    # We do that to prevent having multiple PBs in the same category under different variables,
                    # but we also don't want to check leaderboards specific to said variables as it'll return a leaderboard size way too small
                    if run.category in valid_runs:
                        valid_runs[run.category].place = min(valid_runs[run.category].place, run.place)
                        update_progress(0, -1)
                    else: # ... else add it to the valid runs dict
                        valid_runs[run.category] = run
                else: update_progress(0, -1)

            # Compile the points for the runs
            threads = []
            for category, run in valid_runs.items():
                threads.append(Thread(target=set_points_thread, args=[run]))
            update_progress(0, len(threads))
            for t in threads: t.start()
            for t in threads: t.join()

            update_progress(1, 0)
        except UserUpdaterError as exception:
            threadsException.append(exception.args[0])
        except Exception as exception:
            threadsException.append({"error":"Unhandled", "details":traceback.format_exc()})

def get_leaderboard_size(p_game, p_category): ##, values={}
    try:
        url = "http://www.speedrun.com/api/v1/leaderboards/"+p_game+"/category/"+p_category+"?video-only=true&max=200"
        # for key, value in values.items(): url += "&var-"+key+"="+value
        # See note in User.set_points() concerning variables
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
            else: raise UserUpdaterError({"error":"HTTPError "+str(data.status_code), "details":exception})

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
    statusLabel.configure(text="Fetching online data from speedrun.com. Please wait... ["+str(int(statusLabel_current/statusLabel_max*100))+"%] ("+str(statusLabel_current)+"/"+str(statusLabel_max)+")")

global worksheet
worksheet = None
def get_updated_user(p_user_ID, p_statusLabel):
    """Called from ui.update_user_thread() and AutoUpdateUsers.run()"""
    global statusLabel
    statusLabel = p_statusLabel
    global statusLabel_current
    statusLabel_current = 0
    global statusLabel_max
    statusLabel_max = 0
    global worksheet
    global threadsException
    threadsException = []

    #Check if already connected
    if not worksheet:

	#Authentify to Google Sheets API
        statusLabel.configure(text="Establishing connexion to online Spreadsheet...")
        try:
            gc = gspread.authorize(credentials)
            docid = "1KpMnCdzFHmfU0XDzUon5XviRis1MvlB5M6Y8fyIvcmo"
            print("https://docs.google.com/spreadsheets/d/"+docid+"\n")
            worksheet = gc.open_by_key(docid).sheet1
        except gspread.exceptions.SpreadsheetNotFound:
            raise UserUpdaterError({"error":"Spreadsheet not found", "details":"https://docs.google.com/spreadsheets/d/"+docid})

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
        statusLabel.configure(text="Updating the leaderboard...")
        debugstr = "\n"+str(user)
        print(debugstr)
        row_count = worksheet.row_count
        # Try and find the user by its ID
        cell_list = worksheet.range("E"+str(ROW_FIRST)+":E"+str(row_count))
        row = None
        for cell in cell_list:
            if cell.value == user._ID:
                row = cell.row
                break
        if row:
            print("User " + user._ID + " found. Updating its cell.")
            cell_list = worksheet.range("B"+str(row)+":D"+str(row))
            cell_list[0].value = user._name
            cell_list[1].value = user._points
            cell_list[2].value = time.strftime("%Y/%m/%d %H:%M")
            worksheet.update_cells(cell_list)
        # If user not found, add a row to the spreadsheet
        else:
            debugstr = "User ID" + user._ID + " not found. Adding a new row."
            print(debugstr)
            values = ["=IF($C"+str(row_count+1)+"<$C"+str(row_count)+";$A"+str(row_count)+"+1;$A"+str(row_count)+")",
                      user._name,
                      user._points,
                      time.strftime("%Y/%m/%d %H:%M"),
                      user._ID]
            worksheet.insert_row(values, index=row_count+1)

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
    return(textOutput, textOutput)

class AutoUpdateUsers(Thread):
    BASE_URL = "http://www.speedrun.com/api/v1/users?orderby=signup&max=200&offset=400"
    paused = True
    global statusLabel


    def __init__(self, p_statusLabel, **kwargs):
        Thread.__init__(self, **kwargs)
        self.statusLabel = p_statusLabel

    def run(self):
        url = self.BASE_URL
        while True:
            if not self.paused:
                self.statusLabel.configure(text="Auto-updating userbase...")
                users = get_file(url)
                for user in users["data"]:
                    get_updated_user(user["id"], self.statusLabel)
                link_found = False
                for link in users["pagination"]["links"]:
                    if link["rel"] == "next":
                        url = link["uri"]
                        link_found = True
                if not link_found: url = self.BASE_URL

def spam_test():
    def spam():
        get_file("http://www.speedrun.com/api/v1/users?max=2")
    while True:
        Thread(target=spam).start()

