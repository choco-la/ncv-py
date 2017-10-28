#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Authentication module for niconico."""

import urllib.request
from urllib.request import (build_opener, HTTPCookieProcessor)
from urllib.parse import urlencode
import http.cookiejar
import sys
import os
from getpass import getpass
import re
from typing import Dict


def _main() -> None:
    cookieDir = os.path.join("cookie", "")
    try:
        os.makedirs(cookieDir, exist_ok=True)
    except IOError as err:
        sys.exit("[ERR] {0}: Cannot access.".format(cookieDir))

    cookieFile = "cookie.txt"
    pathToCookie = os.path.join(cookieDir, cookieFile)

    loginUrl = "https://account.nicovideo.jp/api/v1/login"
    postData = input_auth()

    save_cookie(loginUrl, postData, pathToCookie)


def input_auth() -> Dict[str, str]:
    """Input informations for the authentication.

    Input username/e-mail and password for login.

    Arguments:
        None

    Returns:
        Dict that has mail and password attributes.
    """
    mail = ""
    password = ""

    while not is_valid_email(mail):
        mail = input("E-Mail >>").strip()

    while len(password) <= 0:
        password = getpass("Password >>").strip()

    return {"mail": mail, "password": password}


def is_valid_email(text: str) -> bool:
    """Check if it is valid for e-mail.

    Check if it is valid format for e-mail address.

    Arguments:
        text: E-mail like strings.

    Returns:
        True if it is valid, otherwise False.
    """
    # Regex-pattern parts for email addresses.
    username = r"[a-zA-Z0-9_.-]+"
    host = r"(?:[a-zA-Z0-9_-]+\.)+[a-z]{2,8}"

    # Full regex pattern for email addresses.
    email = r"^" + username + r"@" + host + r"$"
    return bool(re.match(email, text))


def save_cookie(url: str, data: Dict[str, str], cookie: str) -> None:
    """Save cookie to file.

    Save loged in cookie to local file
    using password.

    Arguments:
        url: Endpoint of login API.
        data: Post data dict.
        cookie: Path for saving the cookie generated by the request.

    Returns:
        None

    TODO:
        Retry when it failed.
    """
    lwp = http.cookiejar.LWPCookieJar()
    httpopener = build_opener(
                   HTTPCookieProcessor(lwp))
    encdata = urlencode(data).encode("utf-8")

    with httpopener.open(url, encdata) as resp:
        lwp.save(cookie)


if __name__ == "__main__":
    _main()
