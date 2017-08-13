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

class UserUpdaterError(Exception):
    """ raise UserUpdaterError({"error":"On Status Label", "details":"Details of error"}) """
    pass


class Run():
    ID = ""
    game = ""
    category = ""
    variables = {}
    _place = 0
    _points = 0
    __leaderboard_size = 0

    def __init__(self, ID, game, category, variables):
        self.ID = ID
        self.game = game
        self.category = category
        self.variables = variables
        self.__set_points()

    def __str__(self):
        return "Run: <Game: {}, Category: {}, {}/{}>".format(self.game, self.category, self._place, self._leaderboard_size)

    def get_leaderboard_size_and_rank(p_game, p_category, p_variables, p_run_id=None):
        try:
            url = "https://www.speedrun.com/api/v1/leaderboards/{game}/category/{category}?video-only=true".format(game=p_game, category=p_category)
            for var_id, var_value in p_variables.items(): url += "&var-{id}={value}".format(id=var_id, value=var_value)
            leaderboard = get_file(url)
            # Manually recalculating a player's rank as leaderboards w/ only video verification may be smaller than the run originally showed
            if p_run_id:
                rank = -1
                for run in leaderboard["data"]["runs"]:
                    if run["run"]["id"] == p_run_id and run["place"] > 0:
                        rank = run["place"]
                        break
                return len(leaderboard["data"]["runs"]), rank
            else:
                return len(leaderboard["data"]["runs"])
        except UserUpdaterError as exception:
            threadsException.append(exception.args[0])
        except Exception as exception:
            threadsException.append({"error":"Unhandled", "details":traceback.format_exc()})

    def __set_leaderboard_size_and_place(self):
        self._leaderboard_size, self._place = Run.get_leaderboard_size_and_rank(self.game, self.category, self.variables, self.ID)

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
            self._points = math.ceil(max(0, LN1 * LN2 * (1+MIN_RANK_PERCENT/self._place)))

class User():
    _points = 0
    _name = ""
    _ID = ""
    _banned = False

    def __init__(self, ID_or_name):
        self._ID = ID_or_name
        self._name = ID_or_name

    def __str__(self):
        return "User: <{}, {}, {}>".format(self._name, self._points, self._ID)

    def set_code_and_name(self):
        try:
            url = "https://www.speedrun.com/api/v1/users/{user}".format(user=self._ID)
            infos = get_file(url)
            if "status" in infos: raise UserUpdaterError({"error":"{} (speedrun.com)".format(infos["status"]), "details":infos["message"]})
            if infos["data"]["role"] != "banned":
                self._ID = infos["data"]["id"]
                self._name = infos["data"]["names"].get("international")
                japanese_name = infos["data"]["names"].get("japanese")
                if japanese_name: self._name += " ({})".format(japanese_name)
            else:
                self._banned = True
                self._points = 0
        except UserUpdaterError as exception:
            threadsException.append(exception.args[0])
        except Exception:
            threadsException.append({"error":"Unhandled", "details":traceback.format_exc()})

    def set_points(self):
        counted_runs = {}
        def set_points_thread(pb):
            try:
                # Check if it's a valid run (has a category, isn't an IL, has video verification)
                if pb["run"]["category"] and not pb["run"]["level"] and pb["run"].get("videos"): # TODO?: allow runs for games that have levels, but no category?
                    #Get a list of the game's subcategory variables
                    url = "https://www.speedrun.com/api/v1/games/{game}/variables?max=200".format(game=pb["run"]["game"])
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

                    run = Run(pb["run"]["id"], pb["run"]["game"], pb["run"]["category"], pb_subcategory_variables)
                    # If a category has already been counted, only keep the one that's worth the most.
                    # This can happen in leaderboards with multiple coop runs or multiple subcategories.
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

        try:
            if not self._banned:
                url = "https://www.speedrun.com/api/v1/users/{user}/personal-bests".format(user=self._ID)
                PBs = get_file(url)
                if "status" in PBs: raise UserUpdaterError({"error":"{} (speedrun.com)".format(PBs["status"]), "details":PBs["message"]})
                self._points = 0
                update_progress(0, len(PBs["data"]))
                threads = []
                for pb in PBs["data"]:
                    threads.append(Thread(target=set_points_thread, args=(pb,)))
                for t in threads: t.start()
                for t in threads: t.join()
                # Sum up the runs' score
                for points in counted_runs.values():
                    self._points += points
                if self._banned: self._points = 0 # In case the banned flag has been set mid-thread
            else: self._points = 0
        except UserUpdaterError as exception:
            threadsException.append(exception.args[0])
        except Exception as exception:
            threadsException.append({"error":"Unhandled", "details":traceback.format_exc()})
        finally:
            update_progress(1, 0)


def get_file(p_url):
    """
    Returns the content of "url" parsed as JSON dict.

    Parameters
    ----------
    url : str   # The url to query
    """
    print("\n{}".format(p_url)) #debugstr
    while True:
        try:
            data = requests.get(p_url)
            data.raise_for_status()
            break
        except requests.exceptions.ConnectionError as exception:
            raise UserUpdaterError({"error":"Can't establish connexion to speedrun.com", "details":exception})
        except requests.exceptions.HTTPError as exception:
            if data.status_code in HTTP_RETRYABLE_ERRORS:
                print("WARNING: {}. Retrying in {} seconds.".format(exception.args[0], HTTPERROR_RETRY_DELAY)) #debugstr
                time.sleep(HTTPERROR_RETRY_DELAY)
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
    global worksheet
    global gs_client
    global threadsException
    threadsException = []
    textOutput = p_user_ID

    try:
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

        threads = []
        threads.append(Thread(target=user.set_code_and_name))
        threads.append(Thread(target=user.set_points))
        update_progress(0, len(threads))
        for t in threads: t.start()
        for t in threads: t.join()
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
                if row >= ROW_FIRST:
                    textOutput = "{} found. Updated its cell.".format(user)
                    cell_list = worksheet.range(row, COL_USERNAME, row, COL_LAST_UPDATE)
                    cell_list[0].value = user._name
                    cell_list[1].value = user._points
                    cell_list[2].value = timestamp
                    worksheet.update_cells(cell_list)
                # If user not found, add a row to the spreadsheet
                else:
                    textOutput = "{} not found. Added a new row.".format(user)
                    values = ["=IF($C{1}=$C{0};$A{0};ROW()-3)".format(row_count, row_count+1),
                              user._name,
                              user._points,
                              timestamp,
                              user._ID]
                    worksheet.insert_row(values, index=row_count+1)
            else:
                textOutput = "Not updloading data as {} has a score of 0.".format(user)

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
        raise UserUpdaterError({"error":"Authorization problems", "details":"{}\nThis version of the app may be outdated. Please see https://github.com/Avasam/speedrun.com_-unofficial-_global_leaderboard/releases".format(exception)})


#!Autoupdater
class AutoUpdateUsers(Thread):
    BASE_URL = "https://www.speedrun.com/api/v1/users?orderby=signup&max=200&offset=0"
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
                while True:
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

            link_found = False
            for link in users["pagination"]["links"]:
                if link["rel"] == "next":
                    url = link["uri"]
                    link_found = True
            if not link_found: url = self.BASE_URL

    def __check_for_pause(self):
        while self.paused:
            pass
