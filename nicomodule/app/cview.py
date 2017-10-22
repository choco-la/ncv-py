#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Comment viewer function library.
Load from the parent directory.
"""

import sys
import re
import os
from typing import Tuple
import unicodedata
import json

from nicomodule.common import (genfilter,
                               nicookie,
                               nicoid,
                               nickname,
                               nauth)
from nicomodule.live import (cparser,
                             niconnect,
                             pstat)


def pull_usersession(cookie: str) -> str:
    """Pull usersession value with appropriate method.

    Use appropriate method by cookie type.
        Firefox cookie(*.sqlite)
            -> pull_usrsess_fx
        Wget cookie(*.wget)
            -> pull_usrsess_wg
        Else(assert it as LWPCookie)
            -> pull_usrsess_lwp

    Arguments:
        cookie: Cookie already logged in to niconico.

    Returns:
        Usersession value.
    """
    try:
        if cookie.endswith(".sqlite"):
            usersession = (nicookie
                           .pull_usrsess_fx(cookie))
        elif cookie.endswith(".wget"):
            usersession = (nicookie
                           .pull_usrsess_wg(cookie))
        else:
            usersession = (nicookie
                           .pull_usrsess_lwp(cookie))
    except IOError as err:
        error_exit(err, cookie)
    except FileNotFoundError as err:
        error_exit(err, cookie)
    except IsADirectoryError as err:
        error_exit(err, cookie)
    except PermissionError as err:
        error_exit(err, cookie)
    except Exception as err:
        error_exit(err, cookie)

    return usersession


def login_nico(cookie: str) -> None:
    """Login to niconico.

    Login to niconico with password.

    Arguments:
        cookie: Path for saving cookie.

    Returns:
        None
    """
    loginurl = "https://account.nicovideo.jp/api/v1/login"
    postdata = nauth.input_auth()

    nauth.save_cookie(loginurl, postdata, cookie)


def mk_dir(dir: str) -> None:
    """Make a directory if not exists.

    Make a directory to save a logFile like $(mkdir -p).

    Arguments:
        dir: The Directory path to create.

    Returns:
        None
    """
    try:
        os.makedirs(dir, exist_ok=True)
    except IOError as err:
        error_exit(err, dir)
    except FileExistsError as err:
        error_exit(err, dir)
    except PermissionError as err:
        error_exit(err, dir)


def decode_data(raw: bytes, partial: str=None) -> str:
    """Decode the data recieved from a socket.

    Decode recieved chat data to UTF-8.
    If a partial data argued, concatenate with the data.

    Arguments:
        raw: Thr raw data of a socket.
        partial: None or a corrupt tag recieved previous loop.

    Returns:
        Decoded chat data strings.
    """
    if partial is None:
        decdata = raw.decode("utf-8", "ignore")
    else:
        decdata = partial + raw.decode("utf-8", "ignore")
    return decdata


def handle_chat(parsed: dict,
                confdict: dict,
                namemap: dict,
                filter,
                plystat) -> Tuple[bool, bool]:
    """Main chat-handling.

    Clean later. Too huge.

    Arguments:
        parsed: A parsed dict of a chat data.
        confDict: The configuration dict.
        namemap: The generated nickname list from a json.
        filter: A filtering instance that has a matching method.
        plystat: An instance of the getplayerstatus.xml properties.

    Returns:
        A boolean value tuple, first is "whether to reload the namemap.",
        second is "whether the program is ended."
    """
    toregist = to_regist(parsed["content"], parsed["id"], namemap)
    toreload = False

    if toregist:
        registname = re.search(r"[@＠](.+)$", parsed["content"]).group(1)
        try:
            if parsed["anonymity"] == "0":
                nickname.regist_nickname(
                  parsed["id"],
                  registname,
                  parsed["time"],
                  confdict["p-nickNameId"])
                # Reload namemap.
                namemap = load_json(
                            confdict["p-nickNameId"])
            elif parsed["anonymity"] == "1":
                nickname.regist_nickname(
                  parsed["id"],
                  registname,
                  parsed["time"],
                  confdict["p-nickNameAnon"])
                # Reload namemap.
                namemap = load_json(
                            confdict["p-nickNameAnon"])
            toreload = True
        except json.JSONDecodeError as err:
            error_exit(err,
                       confdict["p-nickNameId"])
        except IOError as err:
            error_exit(err,
                       confdict["p-nickNameId"])
        except IsADirectoryError as err:
            error_exit(err,
                       confdict["p-nickNameId"])
        except PermissionError as err:
            error_exit(err,
                       confdict["p-nickNameId"])
    else:
        pass

    parsed["nickname"], isnew = assign_nickname(
                                  parsed["id"],
                                  parsed["anonymity"],
                                  namemap)

    if isnew is True:
        toreload = True
        if parsed["anonymity"] == "0":
            nickname.regist_nickname(parsed["id"],
                                     parsed["nickname"],
                                     parsed["time"],
                                     confdict["p-nickNameId"])
        elif parsed["anonymity"] == "1":
            nickname.regist_nickname(parsed["id"],
                                     parsed["nickname"],
                                     parsed["time"],
                                     confdict["p-nickNameAnon"])
    elif isnew is False:
        pass

    parsed["nickname"], wchar = trunc_name(
                                  parsed["nickname"],
                                  confdict["nameLength"])
    parsed["cmttime"] = calc_rel_time(
                           int(parsed["time"]),
                           plystat.start)
    parsed["namelen"] = confdict["nameLength"]

    if filter is None:
        tomute = False
    else:
        tomute = all([confdict["use_cmt_filter"],
                      filter.ismatch(parsed["content"])])

    if tomute:
        pass
    else:
        if confdict["narrow"] is False:
            show_comment(parsed, wchar)
        elif confdict["narrow"] is True:
            narrow_comment(parsed, wchar)

    # Break when /disconnect is sent by admin/broadcaster.
    # If all() returns True, isDisconnected becomes False.
    isdisconnected = all([parsed["content"] == "/disconnect",
                          int(parsed["premium"]) > 1])

    return (toreload, isdisconnected)


def show_comment(parsed: dict, wchar: int) -> None:
    """Print a comment data by formatting.

    Print a comments with some additional info.

    Arguments:
        parsed: The parsed dict of a chat data.
        wchar: A number of double width characters.

    Returns:
        None
    """
    # Premium member
    if parsed["premium"] == "1":
        pmark = "P"
        color = "default"
    # Administrator
    elif parsed["premium"] == "2":
        pmark = "A"
        color = "darkpurple"
    # Owner
    elif parsed["premium"] == "3":
        pmark = "O"
        color = "sky"
    # BSP
    elif parsed["premium"] == "7":
        pmark = "B"
        color = "blue"
    else:
        pmark = " "
        color = "default"

    # Truncate display name to configured length.
    namearea = "[{2: ^" + str(parsed["namelen"] - wchar) + "}]"
    fullcmt = (("{0}:{1}" + namearea + " {3} [{4}]")
               .format(parsed["no"],
                       pmark,
                       parsed["nickname"],
                       parsed["content"],
                       parsed["cmttime"]))

    print_color(fullcmt, color)


def narrow_comment(parsed: dict, wchar: int) -> None:
    """Print a comment data by narrow formatting.

    Print a comments with some additional info.
    Adapted for narrow display.

    Arguments:
        parsed: The parsed dict of a chat data.
        wchar: A number of double width characters.

    Returns:
        None
    """
    # Premium member
    if parsed["premium"] == "1":
        color = "default"
    # Administrator
    elif parsed["premium"] == "2":
        color = "darkpurple"
    # Owner
    elif parsed["premium"] == "3":
        color = "sky"
    # BSP
    elif parsed["premium"] == "7":
        color = "blue"
    else:
        color = "default"

    namearea = "[{0: ^" + str(8 - wchar) + "}]"
    nname, _ = trunc_name(parsed["nickname"], 8)
    # Which is better,
    # substrings re.sub([letter count], ...)
    # or
    # text / (n: {2, 3, 4...}) < [count] => text / n
    """
    Format is like:

    [8_UserId] comment com
               ment commen
               t comment

    but _ is white space.
    """
    ncontent = re.sub(r"(?P<m>.{,16})",
                      "{0}\g<m>{1}".format(" " * 11,
                                           os.linesep),
                      parsed["content"])
    ncontent = re.sub(r"(?:^[\s]{11}|\n$)", "", ncontent)
    fullcmt = ((namearea + " {1}")
               .format(nname,
                       ncontent))

    print_color(fullcmt, color)


def load_json(filepath: str) -> dict:
    """Load a nickname json file.

    Loading a json, make it to the dict object.

    Arguments:
        filepath: The path to a json file to load.

    Returns:
        Dict of the json file content.
    """
    try:
        with open(filepath, "r") as jsonf:
            namemap = json.load(jsonf)
    except json.JSONDecodeError as err:
        error_exit(err, filepath)
    except IOError as err:
        error_exit(err, filepath)
    except IsADirectoryError as err:
        error_exit(err, filepath)
    except PermissionError as err:
        error_exit(err, filepath)

    return namemap


def to_regist(text: str, uid: str, namemap: dict) -> bool:
    """Check if the name should be registered.

    If text contains "@|＠", treat after it as a new nickname.
    Not already registered and not fixed, return True.

        text: "Hello, world@JohnDoe"
            -> register JohnDoe

    Arguments:
        text: A comment text may contains "@|＠".
        uid: A userID to check the registration.
        namemap: A nickname dict using for the registration check.

    Returns:
        If it should be registered. True.
        If the nickname is fixed or no nickname is given, False.
    """
    if re.match(r".*[@＠].+$", text):
        try:
            prop = namemap[uid]
        # Not registered.
        except KeyError as err:
            return True

        # If nickname is not fixed, register nickname.
        if prop["fixed"] == 1:
            return False
        elif prop["fixed"] == 0:
            return True
    else:
        return False


def assign_nickname(uid: str,
                    isanon: str,
                    namemap: dict) -> Tuple[str, bool]:
    """Assign the nickanme to userID.

    Assign the nickname to the userID if already registered.
    If not registered and it is not an anonymous comment,
    try to retrieve its user's niconico username.

    Arguments:
        uid: A userID to assign the nickname.
        isanon: Whether the user is anonymous.
        namemap: A nickname dict using for assigning the name.

    Returns:
        A tuple of the nickname and a boolean value
        whether the name was newly registered.
    """
    # Return name if already registered.
    try:
        return (namemap[uid]["name"], False)
    except KeyError as err:
        pass

    # Retrieve username if not anon comment.
    if isanon == "0":
        try:
            return (nickname.retrieve_name(uid), True)
        except IOError as err:
            return (uid, False)
    elif isanon == "1":
        return (uid, False)


def trunc_name(orig: str, limit: int) -> Tuple[str, int]:
    """Truncate displaying the name/userID.

    Truncate the name/userID to the limit length.

    Arguments:
        orig: The name/userID before truncating.
        limit: The limitation count of name/userID's length.

        Returns:
            A tuple of the truncated name/userID and
            a number of double width characters.
    """
    # A number of double width characters.
    wchar = 0
    # Truncated name width.
    width = 0
    # Truncated name.
    trunc = ""

    for char in list(orig):
        # 1 or 2 width acceptable.
        if width < limit - 1:
            trunc += char
            if get_chr_width(char) == 1:
                width += 1
            elif get_chr_width(char) == 2:
                width += 2
                wchar += 1
        # Only 1 width acceptable.
        elif width == limit - 1:
            if get_chr_width(char) == 1:
                trunc += char
                width += 1
            elif get_chr_width(char) == 2:
                break
        elif width == limit:
            break

    return (trunc, wchar)


def get_chr_width(char: str) -> int:
    """Count a character's width.

    Count the width of a character.
    Returns 1 or 2 as the width.

    Arguments:
        char: The character to count its width.

    Returns:
        1 or 2.
        In case it is ascii, return 1.
    """
    width = unicodedata.east_asian_width(char)
    if re.match(r"H|Na", width):
        return 1
    elif re.match(r"A|F|N|W", width):
        return 2


def print_color(text: str, color: str) -> None:
    """Print strings with escape sequence color.

    Print strings with the argued color using
    escape sequence.

    Arguments:
        text: A text to print with color.
        color: The color of the text.

    Returns:
        None
    """
    if color == "red":
        print("\033[31m" + text + "\033[0m")
    elif color == "darkgreen":
        print("\033[32m" + text + "\033[0m")
    elif color == "darkpurple":
        print("\033[35m" + text + "\033[0m")
    elif color == "orange":
        print("\033[91m" + text + "\033[0m")
    elif color == "green":
        print("\033[92m" + text + "\033[0m")
    elif color == "yellow":
        print("\033[93m" + text + "\033[0m")
    elif color == "blue":
        print("\033[94m" + text + "\033[0m")
    elif color == "purple":
        print("\033[95m" + text + "\033[0m")
    elif color == "sky":
        print("\033[96m" + text + "\033[0m")
    else:
        print(text)


def calc_rel_time(acttime: int, basetime: int) -> str:
    """Calculate the relation time from start.

    Calulate the relation comment time
    from program starts.

    Arguments:
        acttime: A time comment posted.
        basetime: The time program started.

    Returns:
        The relation time comment posted.
        Note that the type is not int but str.
        Format: HH:MM:SS (0 padding)
    """
    # TODO: use datetime
    reltime = acttime - basetime
    relhour = int(reltime / 3600)
    relmin = int(reltime / 60 - (relhour * 60))
    relsec = int(reltime % 60)

    cmttime = ("{0:0>2}:{1:0>2}:{2:0>2}"
               .format(str(relhour),
                       str(relmin),
                       str(relsec)))
    return cmttime


def write_file(text: str, filepath: str) -> None:
    """Write text to file.

    Write text to file as text.
    Use for logfile etc.

    Argument:
        text: Strings to write to file.
        filepath: Path to textfile.

    Returns:
        None
    """
    try:
        with open(filepath, "a") as log:
            log.write("{0}\n".format(text))
    except IOError as err:
        error_exit(err, filepath)
    except IsADirectoryError as err:
        error_exit(err, filepath)
    except PermissionError as err:
        error_exit(err, filepath)


def error_exit(err, targ: str, *details: tuple) -> None:
    """Exit script with error message.

    Print error messages such a error line, error details,
    then exit script.

    Arguments:
        err: Exception.
        targ: Error target.
        details: Error details.

    Returns:
        None
    """
    trace = sys.exc_info()[2]
    lineno = trace.tb_lineno
    if len(details) <= 0:
        details = err.args
    sys.exit("[ERR]L{0} {1}: {2}".format(lineno,
                                         targ,
                                         details))
