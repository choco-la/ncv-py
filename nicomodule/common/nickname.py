#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Retrieve, register, assign the nickname."""

from time import sleep
from xml.dom import minidom
import collections
import json
import os.path
import re
import urllib.error
import urllib.request


def register_name(uid: str,
                  name: str,
                  time: int,
                  filepath: str) -> None:
    """Resister nickname to a json file.

    Dump dict of nicknames, registered time and
    fixed propertys to json with id.
    format: {id: {"name": name, "time": time, fixed: 0}}

    Arguments:
        uid: The commented user id.
        name: The nickname to register.
        time: Registed time.
        filepath: Path to a json file to dump.

    Returns:
        None
    """
    touch_json(filepath)
    decoder = json.JSONDecoder(
      object_pairs_hook=collections.OrderedDict)
    name = name.replace(r"\\", r"\\")
    name = name.replace(r'"', r'\"')

    # Load current json.
    with open(filepath, "r") as jsonf:
        namedict = decoder.decode(jsonf.read())

    add = {
        "name": name,
        "time": time,
        "fixed": 0
    }
    namedict[uid] = add

    with open(filepath, "w") as jsonf:
        json.dump(namedict,
                  jsonf,
                  ensure_ascii=False,
                  separators=(", ", ": "))


def touch_json(filepath: str) -> None:
    """Check if file exists.

    If the file do not exists, make a blank json.

    Argument:
        filepath: Path to the file to check.

    Returns:
        None
    """
    if not os.path.exists(filepath):
        with open(filepath, "w") as jsonf:
            jsonf.write("{}")


# TODO: not known what condition required to seiga-name.
def retrieve_name(uid: str) -> str:
    """Retrieve username.

    Retrieve the username of niconico.
    Not all of users can be retrieved their name by seiga API.
    If failed, it try to retrieve by the iframe page.

    Arguments:
        uid: The UserID to retrieve its name.

    Returns:
        The retrieved username if it succeeded,
        otherwise The userID if it failed.
    """
    # Not to send Excessive requests.
    sleep(1)
    try:
        return retr_name_seiga(uid)
    # some users are 404
    except urllib.error.HTTPError:
        try:
            return retr_name_iframe(uid)
        except urllib.error.HTTPError:
            return uid
        except AttributeError:
            return uid


def retr_name_seiga(uid: str) -> str:
    """Retrieve an username with seiga API.

    Retrieve an username from seiga API's json.
    It may failed for some users.

    Arguments:
        uid: A userID to retrieve its name.

    Returns:
        Retrieved username.
    """
    url = "http://seiga.nicovideo.jp/api/user/info?id={0}".format(uid)
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        pstr = minidom.parseString(resp.read().decode("utf-8"))
    nicknametag = pstr.getElementsByTagName("nickname")[0]
    return nicknametag.firstChild.data


def retr_name_iframe(uid: str) -> str:
    """Retrieve an username with iframe.

    Retrieve an username from the user iframe.
    It probably succeed unlike seiga API.

    Arguments:
        uid: A user id to retrieve its name.

    Returns:
        Retrieved username.

    TODO:
        Use not re but html parser.
        ElementTree causes a ParseError.
        lxml.html is not a stadard library.
    """
    url = "http://ext.nicovideo.jp/thumb_user/{0}".format(uid)
    req = urllib.request.Request(url)
    regex = (r'<p class="TXT12"><a href="'
             r'http://www.nicovideo.jp/user/' + uid + r'"'
             r' target="_blank"><strong>(.+)</strong></a></p>')
    with urllib.request.urlopen(req) as resp:
        return re.search(regex, resp.read().decode("utf-8")).group(1)
