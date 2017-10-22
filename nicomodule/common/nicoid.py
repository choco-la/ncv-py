#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Grep nico content id."""

import re


def grep_lv(url: str) -> str:
    """Like grep -oE, find lvXXXX.

    Argument:
        url: Text to find content id.

    Returns:
        Content id like lv2525.
    """
    schm = r"(?:https?://)?"
    host = r"(?:live2?\.nicovideo\.jp/watch|nico\.ms)/"
    idpat = r"lv[0-9]+"

    # only lvXXXX
    if re.match(idpat + r"$", url):
        return url

    match = re.match(schm + host + r"(" + idpat + r")", url)
    if match:
        return match.group(1)
    else:
        raise ValueError("invalid format")


def grep_co(url: str) -> str:
    """Like grep -oE, find coXXXX, ch2525.

    Argument:
        url: Text to find content id.

    Returns:
        Content id like co2525, ch2525.
    """
    schm = r"(?:https?://)?"
    comhost = r"(?:com\.nicovideo\.jp/community|nico\.ms)/"
    chnhost = r"(?:ch\.nicovideo\.jp/channel|nico\.ms)/"
    coidpat = r"co[0-9]+"
    chidpat = r"ch[0-9]+"

    if re.match(coidpat + r"$", url):
        return url
    elif re.match(chidpat + r"$", url):
        return url

    matchcom = re.match(schm + comhost + r"(" + coidpat + r")", url)
    matchchn = re.match(schm + chnhost + r"(" + chidpat + r")", url)
    if matchcom:
        return matchcom.group(1)
    elif matchchn:
        return matchchn.group(1)
    else:
        raise ValueError("invalid format")


def grep_video(url: str) -> str:
    """Like grep -oE, find smXXXX, soXXXX, nmXXXX.

    Argument:
        url: Text to find content id.

    Returns:
        Content id like sm2525.
    """
    schm = r"(?:https?://)?"
    host = r"(?:www\.nicovideo\.jp/watch|nico\.ms)/"
    idpat = r"(?:sm|so|nm)[0-9]+"

    if re.match(idpat + r"$", url):
        return url

    match = re.match(schm + host + r"(" + idpat + r")", url)
    if match:
        return match.group(1)
    else:
        raise ValueError("invalid format")
