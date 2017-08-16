#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Retrieve, register, assign the nickname."""

import re
import json
import collections
import os.path
import urllib.request
import urllib.error
from xml.dom import minidom
from time import sleep


def regist_nickname(id: str,
                    name: str,
                    time: int,
                    filepath: str) -> None:
    """Resister nickname to a json file.

    Dump dict of nicknames, registered time and
    fixed propertys to json with id.
    format: {id: {"name": name, "time": time, fixed: 0}}

    Arguments:
        id: The commented user id.
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

    # load current json.
    with open(filepath, "r") as jsonf:
        namedict = decoder.decode(jsonf.read())

    add = {
        "name": name,
        "time": time,
        "fixed": 0
    }
    namedict[id] = add

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
def retrieve_name(id: str) -> str:
    """Retrieve username.

    Retrieve the username of niconico.
    Not all of users can be retrieved their name by seiga API.
    If failed, it try to retrieve by the iframe page.

    Arguments:
        id: The UserID to retrieve its name.

    Returns:
        The retrieved username if it succeeded,
        otherwise The userID if it failed.
    """
    # not too Excessive requests.
    sleep(1)
    try:
        return retr_name_seiga(id)
    # some users are 404
    except urllib.error.HTTPError as err:
        try:
            return retr_name_iframe(id)
        except urllib.error.HTTPError as err:
            return id
        except AttributeError as err:
            return id


def retr_name_seiga(id: str) -> str:
    """Retrieve an username with seiga API.

    Retrieve an username from seiga API's json.
    It may failed for some users.

    Arguments:
        id: A userID to retrieve its name.

    Returns:
        Retrieved username.
    """
    url = "http://seiga.nicovideo.jp/api/user/info?id={0}".format(id)
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        pstr = minidom.parseString(resp.read().decode("utf-8"))
    nicknametag = pstr.getElementsByTagName("nickname")[0]
    return nicknametag.firstChild.data


def retr_name_iframe(id: str) -> str:
    """Retrieve an username with iframe.

    Retrieve an username from the user iframe.
    It probably succeed unlike seiga API.

    Arguments:
        id: A user id to retrieve its name.

    Returns:
        Retrieved username.
    TODO:
        Use not re but html parser.
        ElementTree causes a ParseError.
        lxml.html is not a stadard library.
    """
    url = "http://ext.nicovideo.jp/thumb_user/{0}".format(id)
    req = urllib.request.Request(url)
    regex = (r'<p class="TXT12"><a href="'
             r'http://www.nicovideo.jp/user/' + id + r'"'
             r' target="_blank"><strong>(.+)</strong></a></p>')
    with urllib.request.urlopen(req) as resp:
        return re.search(regex, resp.read().decode("utf-8")).group(1)
