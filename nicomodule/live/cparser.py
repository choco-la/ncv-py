#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Comment displaying format."""

from xml.dom import minidom
import xml.parsers.expat
from typing import Dict


def parse_comment(dom: str) -> Dict[str, str]:
    """Parse comment tag.

    Parse comment tag to dict.
    The "tag" attribute of dict indicating data type.
        thread -> Initial received data.
        chat -> Chat data.
        partial -> Not the complete dom,
                   so concatinating is needed.

    Arguments:
        dom: Dom strings of chat data.

    Returns:
        Dict of parsed comment or other tag.
    """
    try:
        pstr = minidom.parseString(dom)
    # If it is not complete dom, mark it as "partial"
    # to concatinate to the next data.
    except xml.parsers.expat.ExpatError as err:
        resp = {
            "tag": "partial",
            "data": dom
        }
        return resp

    try:
        chat = pstr.getElementsByTagName("chat")[0]
    except IndexError as err:
        try:
            thread = pstr.getElementsByTagName("thread")[0]
        except:
            None
        # Initial recieved data.
        else:
            tag = "thread"
            resp = {
                "tag": tag
            }
    else:
        tag = "chat"
        # KeyError occurs on official programs.
        try:
            commentno = chat.attributes["no"].value
        except KeyError as err:
            commentno = "-"

        time = str(chat.attributes["date"].value)
        userid = chat.attributes["user_id"].value

        # Free members don't have premium key.
        try:
            premium = chat.attributes["premium"].value
        except KeyError as err:
            premium = "0"

        # ID users don't have anonymity key.
        try:
            anonymity = chat.attributes["anonymity"].value
        except KeyError as err:
            anonymity = "0"

        # Owner don't has locale key.
        try:
            locale = chat.attributes["locale"].value
        except KeyError as err:
            locale = "ja-jp"

        # If score is 0, dont have score key.
        try:
            score = chat.attributes["score"].value
        except KeyError as err:
            score = "0"

        # Comment content.
        content = chat.firstChild.data

        resp = {
            "tag": tag,
            "no": commentno,
            "time": time,
            "id": userid,
            "premium": premium,
            "anonymity": anonymity,
            "locale": locale,
            "score": score,
            "content": content
        }

    return resp
