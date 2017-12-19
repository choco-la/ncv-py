#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Comment viewer function library.
Load from the parent directory.
"""

from typing import (Tuple, Dict, cast)
import json
import os
import re
import sys
import unicodedata

from nicomodule.common import (nicookie,
                               nickname,
                               nauth)
from .deftypes import NameProp


class Config():
    def __init__(self) -> None:
        self.cookieDir = os.path.join("cookie", "")  # type: str
        self.filterDir = os.path.join("filter", "")  # type: str
        self.logDir = os.path.join("log", "")  # type: str
        self.cookieFile = os.path.join(
            self.cookieDir,
            "cookie.txt")  # type: str
        self.muteReCmt = os.path.join(
            self.filterDir,
            "mute-re-comment.txt")  # type: str
        self.nickNameId = os.path.join(
            self.filterDir,
            "nickname-id.txt")  # type: str
        self.nickNameAnon = os.path.join(
            self.filterDir,
            "nickname-anon.txt")  # type: str
        self.use_cmt_filter = False  # type: bool
        self.logLimit = 20  # type: int
        self.nameLength = 12  # type: int
        self.narrow = False  # type: bool


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
            usersession = (nicookie.pull_usrsess_fx(cookie))
        elif cookie.endswith(".wget"):
            usersession = (nicookie.pull_usrsess_wg(cookie))
        else:
            usersession = (nicookie.pull_usrsess_lwp(cookie))
    except FileNotFoundError as err:
        error_exit(err, cookie)
    except IsADirectoryError as err:
        error_exit(err, cookie)
    except PermissionError as err:
        error_exit(err, cookie)
    except IOError as err:
        error_exit(err, cookie)

    if usersession is None:
        sys.exit("[ERR] Cookie has no session value: {0}".format(cookie))
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


def mk_dir(newdir: str) -> None:
    """Make a directory if not exists.

    Make a directory to save a logFile like $(mkdir -p).

    Arguments:
        newdir: The Directory path to create.

    Returns:
        None
    """
    try:
        os.makedirs(newdir, exist_ok=True)
    except FileExistsError as err:
        error_exit(err, newdir)
    except PermissionError as err:
        error_exit(err, newdir)
    except IOError as err:
        error_exit(err, newdir)


def name_handle(parsed: Dict[str, str],
                conf: Config,
                namemap: Dict[str, NameProp]) -> bool:
    """Nickname handling.

    Check if nickname needs registered,
    namemap needs reloaded.

    Arguments:
        parsed: A parsed dict of a chat data.
        conf: The configuration instance.
        namemap: The generated nickname list from a json.

    Returns:
        A boolean value "whether to reload the namemap".
    """
    reload = False

    if should_register(parsed["content"], parsed["id"], namemap):
        registname = re.search(r"[@＠](.+)$", parsed["content"]).group(1)
        try:
            if parsed["anonymity"] == "0":
                nickname.register_name(
                    parsed["id"],
                    registname,
                    int(parsed["time"]),
                    conf.nickNameId)
                # Reload namemap.
                namemap = load_json(
                    conf.nickNameId)
            elif parsed["anonymity"] == "1":
                nickname.register_name(
                    parsed["id"],
                    registname,
                    int(parsed["time"]),
                    conf.nickNameAnon)
                # Reload namemap.
                namemap = load_json(
                    conf.nickNameAnon)
            reload = True
        except json.JSONDecodeError as err:
            error_exit(err,
                       conf.nickNameId)
        except IsADirectoryError as err:
            error_exit(err,
                       conf.nickNameId)
        except PermissionError as err:
            error_exit(err,
                       conf.nickNameId)
        except IOError as err:
            error_exit(err,
                       conf.nickNameId)
    else:
        pass

    parsed["nickname"], isnew = assign_nickname(
        parsed["id"],
        parsed["anonymity"],
        namemap)

    if isnew is True:
        reload = True
        if parsed["anonymity"] == "0":
            nickname.register_name(parsed["id"],
                                   parsed["nickname"],
                                   int(parsed["time"]),
                                   conf.nickNameId)
        elif parsed["anonymity"] == "1":
            nickname.register_name(parsed["id"],
                                   parsed["nickname"],
                                   int(parsed["time"]),
                                   conf.nickNameAnon)
    elif isnew is False:
        pass

    return reload


def show_comment(parsed: Dict[str, str],
                 starttime: int,
                 width: int) -> None:
    """Print a comment data by formatting.

    Print a comments with some additional info.

    Arguments:
        parsed: The parsed dict of a chat data.
        starttime: Tha UnixTime program starts.
        width: The width of displaying name on console.

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
    name, wchar = trunc_name(parsed["nickname"], width)
    namearea = "[{2: ^" + str(width - wchar) + "}]"
    commenttime = calc_rel_time(
        int(parsed["time"]),
        starttime)
    fullcmt = (("{0}:{1}" + namearea + " {3} [{4}]")
               .format(parsed["no"],
                       pmark,
                       name,
                       parsed["content"],
                       commenttime))

    print_color(fullcmt, color)


def narrow_comment(parsed: Dict[str, str],
                   width: int) -> None:
    """Print a comment data by narrow formatting.

    Print a comments with some additional info.
    Adapted for narrow display.

    Arguments:
        parsed: The parsed dict of a chat data.
        width: The width of displaying name on console.

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

    width = int(width * 2 / 3)
    wchar = trunc_name(parsed["nickname"], width)[1]
    namearea = "[{0: ^" + str(width - wchar) + "}]"
    nname = trunc_name(parsed["nickname"], width)[0]
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
                      r"{0}\g<m>{1}".format(" " * 11,
                                            os.linesep),
                      parsed["content"])
    ncontent = re.sub(r"(?:^[\s]{11}|\n$)", "", ncontent)
    fullcmt = ((namearea + " {1}")
               .format(nname,
                       ncontent))

    print_color(fullcmt, color)


def load_json(filepath: str) -> Dict[str, NameProp]:
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
    except IsADirectoryError as err:
        error_exit(err, filepath)
    except PermissionError as err:
        error_exit(err, filepath)
    except IOError as err:
        error_exit(err, filepath)

    return namemap


def should_register(text: str, uid: str, namemap: Dict[str, NameProp]) -> bool:
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
        except KeyError:
            return True

        # If nickname is not fixed, register nickname.
        if prop["fixed"] == 1:
            return False
        elif prop["fixed"] == 0:
            return True

    return False


def assign_nickname(uid: str,
                    isanon: str,
                    namemap: Dict[str, NameProp]) -> Tuple[str, bool]:
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
        nameprop = namemap[uid]["name"]
        return (cast(str, nameprop), False)
    except KeyError:
        pass

    # Retrieve username if not anon comment.
    if isanon == "0":
        try:
            return (nickname.retrieve_name(uid), True)
        except IOError:
            return (uid, False)
    elif isanon == "1":
        return (uid, False)

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

    for char in orig:
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
    single = ("H", "Na")
    double = ("A", "F", "N", "W")
    width = unicodedata.east_asian_width(char)
    if width in single:
        return 1
    elif width in double:
        return 2

    return 1


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
    color = color.lower()
    colordict = {
        "red": "31",
        "darkgreen": "32",
        "darkpurple": "35",
        "orange": "91",
        "green": "92",
        "yellow": "93",
        "blue": "94",
        "purple": "95",
        "sky": "96"
    }
    if color not in colordict.keys():
        print(text, flush=True)
        return

    print("\033[{0}m{1}\033[0m".format(
        colordict[color],
        text), flush=True)


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
    except IsADirectoryError as err:
        error_exit(err, filepath)
    except PermissionError as err:
        error_exit(err, filepath)
    except IOError as err:
        error_exit(err, filepath)


def error_exit(err: Exception, targ: str, *details: tuple) -> None:
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
