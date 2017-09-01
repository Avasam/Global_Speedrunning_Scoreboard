#!/usr/bin/python
# -*- coding: utf-8 -*-

###########################################################################
## Ava's Global speedrunning leaderboard
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
import httplib2
import oauth2client
from CONSTANTS import *
from collections import Counter
import gspread
import math
import requests
import time
from threading import Thread
import traceback
from sys import stdout

def print(string):
    stdout.write(str(string)+"\n")

class UserUpdaterError(Exception):
    """ raise UserUpdaterError({"error":"On Status Label", "details":"Details of error"}) """
    pass
class NotFoundError(UserUpdaterError):
    """ raise NotFoundError({"error":"404 Not Found", "details":"Details of error"}) """
    pass


class Run():
    ID = ""
    game = ""
    category = ""
    variables = {}
    level = ""
    level_count = 0
    _place = 0
    _points = 0
    _leaderboard_size = 0

    def __init__(self, ID, game, category, variables={}, level=""):
        self.ID = ID
        self.game = game
        self.category = category
        self.variables = variables
        self.level = level
        self.__set_points()

    def __str__(self):
        level_str = "Level: {}, ".format(self.level) if self.level else ""
        return "Run: <Game: {}, Category: {}, {}{}/{} ÷{}>".format(self.game, self.category, level_str, self._place, self._leaderboard_size, self.level_count+1)

    def __set_leaderboard_size_and_place(self):
        try:
            # If the run is an Individual Level, adapt the request url
            lvl_cat_str = "level/{level}/".format(level=self.level) if self.level else "category/"
            url = "https://www.speedrun.com/api/v1/leaderboards/{game}/{lvl_cat_str}{category}?video-only=true&embed=players".format(game=self.game, lvl_cat_str=lvl_cat_str, category=self.category)
            for var_id, var_value in self.variables.items(): url += "&var-{id}={value}".format(id=var_id, value=var_value)
            leaderboard = get_file(url)

            # Manually recalculating a player's rank as leaderboards w/ only video verification may be smaller than the run originally shown
            if len(leaderboard["data"]["runs"]) >= MIN_LEADERBOARD_SIZE : # Check to avoid useless computation and request
                self._place = 0
                self._leaderboard_size = 0
                previous_time = leaderboard["data"]["runs"][0]["run"]["times"]["primary_t"]
                is_speedrun = False
                found = False
                for run in leaderboard["data"]["runs"]:
                    # Making sure this is a speedrun and not a score leaderboard
                    if not is_speedrun: # To avoid false negatives due to missing primary times, stop comparing once we know it's a speedrun
                        if run["run"]["times"]["primary_t"] < previous_time: break # Score based leaderboard. No need to keep looking
                        elif run["run"]["times"]["primary_t"] > previous_time: is_speedrun = True

                    # Updating leaderboard size and rank
                    banned_players = []
                    for player in leaderboard["data"]["players"]["data"]:
                        if player.get("role") == "banned": banned_players.append(player["id"])
                    if run["place"] > 0:
                        players = []
                        is_banned = False
                        for player in run["run"]["players"]:
                            if player.get("id") in banned_players: is_banned = True
                        if not is_banned:
                    ### If the user isn't banned and the run is valid
                            self._leaderboard_size += 1
                            if not found:
                                self._place += 1
                                if run["run"]["id"] == self.ID:
                                    found = True
                if not (is_speedrun and found): self._place = -1

                # If the run is an Individual Level and worth looking at, set the level count
                if self.level and self._place/self._leaderboard_size <= MIN_RANK_PERCENT:
                    url = "https://www.speedrun.com/api/v1/games/{game}/levels".format(game=self.game)
                    levels = get_file(url)
                    self.level_count = len(levels["data"])

        except UserUpdaterError as exception:
            threadsException.append(exception.args[0])
        except Exception as exception:
            threadsException.append({"error":"Unhandled", "details":traceback.format_exc()})

    def __set_points(self):
        self._points = 0
        self.__set_leaderboard_size_and_place()
        print(self)
        # Check to avoid errors
        if self._leaderboard_size > self._place and self._leaderboard_size >= MIN_LEADERBOARD_SIZE and self._place > 0:
            # Give points according to the formula
            #ROUNDUP(MAX(0;LN(MAX(1;B$2-$D$34+2))*LN(MAX(1;(-$A3)+(B$2*$D$35+2)))*(1+$D$35/$A3)))
            LN1 = math.log(self._leaderboard_size-MIN_LEADERBOARD_SIZE+2)
            LN2 = math.log(max(1,-self._place+(self._leaderboard_size*MIN_RANK_PERCENT+2)))
            self._points = max(0, LN1 * LN2 * (1+MIN_RANK_PERCENT/self._place)) / (self.level_count+1)

class User():
    _points = 0
    _name = ""
    _weblink = ""
    _ID = ""
    _banned = False
    _point_distribution_str = ""

    def __init__(self, ID_or_name):
        self._ID = ID_or_name
        self._name = ID_or_name

    def __str__(self):
        return "User: <{}, {}, {}{}>".format(self._name, self._points, self._ID, "(Banned)" if self._banned else "")

    def set_code_and_name(self):
        url = "https://www.speedrun.com/api/v1/users/{user}".format(user=self._ID)
        try:
            infos = get_file(url)
        except NotFoundError as exception:
            raise UserUpdaterError({"error":exception.args[0]["error"], "details":"User \"{}\" not found. Make sure the name or ID is typed properly. It's possible the user you're looking for changed its name. In case of doubt, use its ID.".format(self._ID)})
        if "status" in infos: raise UserUpdaterError({"error":"{} (speedrun.com)".format(infos["status"]), "details":infos["message"]})
        self._ID = infos["data"]["id"]
        self._weblink = infos["data"]["weblink"]
        self._name = infos["data"]["names"].get("international")
        japanese_name = infos["data"]["names"].get("japanese")
        if japanese_name: self._name += " ({})".format(japanese_name)
        if infos["data"]["role"] == "banned":
            self._banned = True
            self._points = 0

    def set_points(self):
        counted_runs = {}
        def set_points_thread(pb):
            try:
                # Check if it's a valid run (has a category AND has video verification)
                level_count = 0
                if pb["run"]["category"] and pb["run"].get("videos"):
                    #Get a list of the game's subcategory variables
                    url = "https://www.speedrun.com/api/v1/games/{game}/variables".format(game=pb["run"]["game"])
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

                    run = Run(pb["run"]["id"], pb["run"]["game"], pb["run"]["category"], pb_subcategory_variables, pb["run"]["level"])
                    # If a category has already been counted, only keep the one that's worth the most.
                    # This can happen in leaderboards with multiple coop runs or multiple subcategories.
                    if run._points > 0:
                        if run.category in counted_runs:
                            counted_runs[run.category] = max(counted_runs[run.category], run._points)
                        else:
                            counted_runs[run.category] = run._points
            except UserUpdaterError as exception:
                threadsException.append(exception.args[0])
            except Exception as exception:
                threadsException.append({"error":"Unhandled", "details":traceback.format_exc()})
            finally:
                update_progress(1, 0)

        if not self._banned:
            url = "https://www.speedrun.com/api/v1/users/{user}/personal-bests".format(user=self._ID)
            try:
                PBs = get_file(url)
            except NotFoundError as exception:
                raise UserUpdaterError({"error":exception.args[0]["error"], "details":"User \"{}\" not found. Make sure the name or ID is typed properly. It's possible the user you're looking for changed its name. In case of doubt, use its ID.".format(self._ID)})
            if "status" in PBs: raise UserUpdaterError({"error":"{} (speedrun.com)".format(PBs["status"]), "details":PBs["message"]})
            self._points = 0
            update_progress(0, len(PBs["data"]))
            threads = []
            for pb in PBs["data"]:
                threads.append(Thread(target=set_points_thread, args=(pb,)))
            for t in threads: t.start()
            for t in threads: t.join()
            # Sum up the runs' score
            self._point_distribution_str="\nCategory | Points\n-------- | ------".format(self._name)
            for category, points in counted_runs.items():
                self._points += points
                self._point_distribution_str+="\n{} | {}".format(category, math.ceil(points*10)/10)
            if self._banned: self._points = 0 # In case the banned flag has been set mid-thread
            else: self._points = math.ceil(self._points)
        else: self._points = 0
        update_progress(1, 0)

global session
session = requests.Session()
def get_file(p_url):
    """
    Returns the content of "url" parsed as JSON dict.

    Parameters
    ----------
    url : str   # The url to query
    """
    global session
    print(p_url) #debugstr
    while True:
        try:
            data = session.get(p_url)
            data.raise_for_status()
            break
        except requests.exceptions.ConnectionError as exception:
            raise UserUpdaterError({"error":"Can't establish connexion to speedrun.com", "details":exception})
        except requests.exceptions.HTTPError as exception:
            if data.status_code in HTTP_RETRYABLE_ERRORS:
                print("WARNING: {}. Retrying in {} seconds.".format(exception.args[0], HTTPERROR_RETRY_DELAY)) #debugstr
                time.sleep(HTTPERROR_RETRY_DELAY)
            elif data.status_code == 404:
                raise NotFoundError({"error":"404 Not Found", "details":exception.args[0]})
            else: raise UserUpdaterError({"error":"HTTPError {}".format(data.status_code), "details":exception.args[0]})

    data = data.json()
    if type(data) != dict: print("{}:{}".format(type(data), data)) #debugstr
    if "error" in data: raise UserUpdaterError({"error":data["status"], "details":data["error"]})
    return(data)

def update_progress(p_current, p_max):
    global statusLabel_current
    global statusLabel_max
    statusLabel_current += p_current
    statusLabel_max += p_max
    percent = int(statusLabel_current/statusLabel_max*100) if statusLabel_max > 0 else 0
    statusLabel.configure(text="Fetching online data from speedrun.com. Please wait... [{}%] ({}/{})".format(percent, statusLabel_current, statusLabel_max))


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
    global session
    global worksheet
    global gs_client
    global threadsException
    threadsException = []
    textOutput = p_user_ID

    try:
        # Send to Webapp
        def send_to_webapp(p_user): session.post("https://avasam.pythonanywhere.com/", data = {"action": "update-user", "name-or-id": p_user})
        Thread(target=send_to_webapp, args=(p_user_ID,)).start()

        # Check if already connected
        if not (gs_client and worksheet):

            #Authentify to Google Sheets API
            statusLabel.configure(text="Establishing connexion to online Spreadsheet...")
            gs_client = gspread.authorize(credentials)
            print("https://docs.google.com/spreadsheets/d/{spreadsheet}\n".format(spreadsheet=SPREADSHEET_ID))
            worksheet = gs_client.open_by_key(SPREADSHEET_ID).sheet1

        # Refresh credentials
        gs_client.login()

        statusLabel.configure(text="Fetching online data from speedrun.com. Please wait...")
        user = User(p_user_ID)
        print("{}\n{}".format(SEPARATOR, user._name)) #debugstr
        
        update_progress(0, 2)
        user.set_code_and_name()
        user.set_points()
        update_progress(1, 0) # Because user.set_code_and_name() is too fast

        if threadsException == []:
            if user._points > 0: #TODO: once the database is full, move this in "# If user not found, add a row to the spreadsheet" (user should also be removed from spreadsheet)
                statusLabel.configure(text="Updating the leaderboard...")
                print("\nLooking for {}".format(user._ID)) #debugstr

                # Try and find the user by its ID
                worksheet = gs_client.open_by_key(SPREADSHEET_ID).sheet1
                row = 0
                # As of 2017/07/16 with current code searching by range is faster than col_values most of the time
##                t1 = time.time()
                row_count = worksheet.row_count
                print("slow call to GSheets")
                cell_list = worksheet.range(ROW_FIRST, COL_USERID, row_count, COL_USERID)
                print("slow call done")
                for cell in cell_list:
                    if cell.value == user._ID:
                        row = cell.row
                        break
##                t2 = time.time()
##                row_count = 0
##                cell_values_list = worksheet.col_values(COL_USERID)
##                for value in cell_values_list:
##                    row_count += 1
##                    if value == user._ID: row = row_count
##                t3 = time.time()
##                print("range took    : {} seconds\ncol_values took: {} seconds".format(t2-t1, t3-t2))
##                print("worksheet.range itself took {} seconds".format(tr2-tr1))
                timestamp = time.strftime("%Y/%m/%d %H:%M")
                linked_name = "=HYPERLINK(\"{}\";\"{}\")".format(user._weblink, user._name)
                if row >= ROW_FIRST:
                    textOutput = "{} found. Updated its cell.".format(user)
                    cell_list = worksheet.range(row, COL_USERNAME, row, COL_LAST_UPDATE)
                    cell_list[0].value = linked_name
                    cell_list[1].value = user._points
                    cell_list[2].value = timestamp
                    worksheet.update_cells(cell_list)
                # If user not found, add a row to the spreadsheet
                else:
                    textOutput = "{} not found. Added a new row.".format(user)
                    values = ["=IF($C{1}=$C{0};$A{0};ROW()-3)".format(row_count, row_count+1),
                              linked_name,
                              user._points,
                              timestamp,
                              user._ID]
                    worksheet.insert_row(values, index=row_count+1)
                textOutput += user._point_distribution_str
            else:
                textOutput = "Not updloading data as {} {}.".format(user, "is banned" if user._banned else "has a score of 0")

        else:
            errorStrList = []
            for e in threadsException: errorStrList.append("Error: {}\n{}".format(e["error"], e["details"]))
            errorStrCounter = Counter(errorStrList)
            errorsStr = "{0}\nNot updloading data as some errors were caught during execution:\n{0}\n".format(SEPARATOR)
            for error, count in errorStrCounter.items(): errorsStr += "[x{}] {}\n".format(count, error)
            textOutput += ("\n" if textOutput else "") + errorsStr

        print(textOutput)
        statusLabel.configure(text="Done! "+("({} error".format(len(threadsException))+("s" if len(threadsException) > 1 else "")+")" if threadsException != [] else ""))
        return(textOutput)

    except httplib2.ServerNotFoundError as exception:
        raise UserUpdaterError({"error":"Server not found", "details":"{}\nPlease make sure you have an active internet connection".format(exception)})
    except (requests.exceptions.ChunkedEncodingError, ConnectionAbortedError) as exception:
        raise UserUpdaterError({"error":"Connexion interrupted", "details":exception})
    except gspread.exceptions.SpreadsheetNotFound:
        raise UserUpdaterError({"error":"Spreadsheet not found", "details":"https://docs.google.com/spreadsheets/d/{spreadsheet}".format(spreadsheet=SPREADSHEET_ID)})
    except requests.exceptions.ConnectionError as exception:
        raise UserUpdaterError({"error":"Can't connect to Google Sheets", "details":exception})
    except oauth2client.client.HttpAccessTokenRefreshError as exception:
        raise UserUpdaterError({"error":"Authorization problems", "details":"{}\nThis version of the app may be outdated. Please see https://github.com/Avasam/Global_speedrunning_leaderboard/releases".format(exception)})


#!Autoupdater
class AutoUpdateUsers(Thread):
    BASE_URL = "https://www.speedrun.com/api/v1/users?orderby=signup&max=200&offset=0"
    paused = True
    global statusLabel

    def __init__(self, p_statusLabel, **kwargs):
        Thread.__init__(self, **kwargs)
        self.statusLabel = p_statusLabel

    def run(self):
        def auto_updater_thread(user):
            while True:
                self.__check_for_pause()
                try:
                    try:
                        get_updated_user(user["id"], self.statusLabel)
                        break
                    except gspread.exceptions.RequestError as exception:
                        if exception.args[0] in HTTP_RETRYABLE_ERRORS:
                            print("WARNING: {}. Retrying in {} seconds.".format(exception.args[0], HTTPERROR_RETRY_DELAY)) #debugstr
                            time.sleep(HTTPERROR_RETRY_DELAY)
                        else:
                            raise UserUpdaterError({"error":"Unhandled RequestError", "details":traceback.format_exc()})
                    except Exception:
                        raise UserUpdaterError({"error":"Unhandled", "details":traceback.format_exc()})
                except UserUpdaterError as exception:
                    print("WARNING: Skipping user {}. {}".format(user["id"], exception.args[0]["details"])) #debugstr
                    break
            
        url = self.BASE_URL
        while True:
            self.__check_for_pause()
            self.statusLabel.configure(text="Auto-updating userbase...")
            users = get_file(url)
##            threads = []
            for user in users["data"]:
                auto_updater_thread(user) # Not threaded
##                threads.append(Thread(target=auto_updater_thread, args=(user,)))
##            for t in threads: t.start()
##            for t in threads: t.join()
                

            link_found = False
            for link in users["pagination"]["links"]:
                if link["rel"] == "next":
                    url = link["uri"]
                    link_found = True
            if not link_found: url = self.BASE_URL

    def __check_for_pause(self):
        while self.paused:
            pass
