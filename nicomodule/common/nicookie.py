#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Print user_session value in Niconico."""

import http.cookiejar
import re
import sqlite3
import sys


def _main() -> None:
    if len(sys.argv) <= 1:
        _show_usage()
        exit(1)

    for cookie in sys.argv[1:]:
        try:
            if cookie.endswith(".sqlite"):
                nicoUserSess = pull_usrsess_fx(cookie)
            elif cookie.endswith(".wget"):
                nicoUserSess = pull_usrsess_wg(cookie)
            else:
                nicoUserSess = pull_usrsess_lwp(cookie)
        except:
            trace = sys.exc_info()[1]
            print("[ERR] {0}: {1}".format(cookie, trace))
        else:
            print("{0}: {1}".format(cookie, nicoUserSess))


def _show_usage() -> None:
    print("Usage: {} [COOKIE]".format(__file__), file=sys.stderr)


def pull_usrsess_fx(cookiedb: str) -> str:
    """Pull user_session value from a mozilla cookie.

    Pull user_session value from firefox-like browser's
    sqlite cookies.

    Arguments:
        cookiedb: Path to cookie.sqlite.

    Returns:
        The user_session value of .nicovodeo.jp.
    """
    with sqlite3.connect(cookiedb) as dbconnection:
        dbcursor = dbconnection.cursor()

        dbstatement = 'SELECT "value" \
                       FROM "moz_cookies" \
                       WHERE "host" = ".nicovideo.jp" \
                       AND "name" = "user_session"'
        dbcursor.execute(dbstatement)
        usersession = dbcursor.fetchone()[0]
    return usersession


def pull_usrsess_wg(cookie: str) -> str:
    """Pull user_session value from a wget cookie.

    Pull user_session value from wget's cookies
    generated by the --save-cookie option.

    Arguments:
        cookie: Path to cookiefile.

    Returns:
        The user_session value of .nicovodeo.jp.
    """
    with open(cookie, "r") as opencookie:
        pat1 = r"\.nicovideo\.jp[\s](TRUE|FALSE)[\s]/[\s](TRUE|FALSE)[\s]"
        pat2 = r"[0-9]+[\s]user_session[\s]user_session_[0-9]+_[a-z0-9]+"
        match = re.search(pat1 + pat2, opencookie.read())
        if match:
            usersession = match.group(0).split()[-1]
        else:
            sys.exit("[ERR] cookie: {} {}"
                     .format(cookie,
                             "no user_session value"))
    return usersession


def pull_usrsess_lwp(cookie: str) -> str:
    """Pull user_session value from a LWPCookie.

    Pull user_session value from LWPCookies.
    This cookie is generated by
    http.cookiejar.LWPCookieJar().save() etc.

    Arguments:
        cookie: Path to cookiefile.

    Returns:
        The user_session value of .nicovodeo.jp.
    """
    cj = http.cookiejar.LWPCookieJar()
    cj.load(cookie)
    return cj._cookies[".nicovideo.jp"]["/"]["user_session"].value


if __name__ == "__main__":
    _main()
