#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Niconico comment viewer using nicomodule."""

import sys
import re
import os
import argparse
from json import JSONDecodeError

from nicomodule.common import (genfilter,
                               nicoid,
                               nickname)
from nicomodule.live import (cparser,
                             niconnect,
                             pstat)
from nicomodule.app import cview
from typing import Dict


def _main() -> None:
    conf = cview.Config()

    cview.mk_dir(conf.cookieDir)
    cview.mk_dir(conf.filterDir)
    nickname.touch_json(conf.nickNameId)
    nickname.touch_json(conf.nickNameAnon)
    nameMapId = cview.load_json(conf.nickNameId)
    nameMapAnon = cview.load_json(conf.nickNameAnon)

    parsedArgs = parse_args(conf)

    # If narrow option is explicited or configured, True.
    if conf.narrow is True:
        pass
    elif conf.narrow is False:
        conf.narrow = parsedArgs.narrow

    """
    TODO: clean arround mute toggle.
    default: True  / cmdopt: None  -> True
    default: False / cmdopt: None  -> False

    default: True  / cmdopt: True  -> True
    default: False / cmdopt: False -> False
    default: True  / cmdopt: False -> False
    default: False / cmdopt: True  -> True
    """
    if parsedArgs.use_filter is True:
        try:
            cmtFilter = (genfilter.MatchFilter(conf.muteReCmt))
            conf.use_cmt_filter = True
        # Disable comment filtering if any errors occurred.
        except IOError as err:
            print("[ERR] {0}: comment filter disabled."
                  .format(conf.muteReCmt),
                  file=sys.stderr)
            cmtFilter = None
            conf.use_cmt_filter = False
    elif parsedArgs.use_filter is False:
        if conf.use_cmt_filter is True:
            try:
                cmtFilter = (genfilter.MatchFilter(conf.muteReCmt))
            # Disable comment filtering if any errors occurred.
            except IOError as err:
                print("[ERR] {0}: comment filter disabled."
                      .format(conf.muteReCmt),
                      file=sys.stderr)
                cmtFilter = None
                conf.use_cmt_filter = False
        elif conf.use_cmt_filter is False:
            cmtFilter = None

    if os.path.basename(parsedArgs.url) != "getplayerstatus.xml":
        # Check if liveId is valid format.
        liveId = parsedArgs.url
        try:
            liveId = nicoid.grep_lv(liveId)
        except ValueError as err:
            try:
                liveId = nicoid.grep_co(liveId)
            except ValueError as err:
                cview.error_exit(err, parsedArgs.url)

        # If cookie does't exist, try to login.
        if not os.path.exists(parsedArgs.cookie):
            cview.login_nico(parsedArgs.cookie)
        userSession = cview.pull_usersession(parsedArgs.cookie)

        statusXml = pstat.get_live_player_status(userSession, liveId)
        plyStat = pstat.LivePlayerStatus(statusXml)
    elif os.path.basename(parsedArgs.url) == "getplayerstatus.xml":
        """
        Use local getplayerstatus.xml file.
        This can retrieved by:

        javascript:(function () {
            const host = '//live.nicovideo.jp/api/getplayerstatus?v=';
            const liveId = window.location.pathname.split('/').reverse()[0];
            const url = host + liveId;
            window.open(url, '_blank');
        })()

        on live page.
        """
        try:
            with open(parsedArgs.url, "r") as xmlopen:
                statusXml = xmlopen.read()
            plyStat = pstat.LivePlayerStatus(statusXml)
            liveId = plyStat.lvid
        # xml.parsers.expat.ExpatError,
        # FileNotFoundError, etc...
        except Exception as err:
            cview.error_exit(err, parsedArgs.url)

    # Check program status: ended/deleted/comingsoon.
    if plyStat.errcode:
        sys.exit("[INFO] program: {0} {1}"
                 .format(liveId, plyStat.errcode))

    # Check if logLimit is valid format.
    if (parsedArgs.limit >= 0 and parsedArgs.limit <= 1000):
        logLimit = parsedArgs.limit
    elif parsedArgs.limit < 0:
        logLimit = 0
    elif parsedArgs.limit > 1000:
        logLimit = 1000

    # If --save-log is true, define logFile and write program data.
    if parsedArgs.save_log is True:
        cview.mk_dir(conf.logDir)
        cview.mk_dir(os.path.join(conf.logDir,
                                  plyStat.community + ""))

        logFile = os.path.join(conf.logDir,
                               plyStat.community,
                               plyStat.lvid + ".txt")
        cview.write_file(
          "# {0} : {1}".format(
            plyStat.lvid,
            plyStat.title),
          logFile)
        cview.write_file(
          "# {0} / {1}".format(
            plyStat.owner,
            plyStat.community),
          logFile)
    else:
        logFile = None

    # Connect socket to comment-server.
    # socket.close() is called by __exit__.
    with niconnect.MsgSocket() as msgSock:
        msgSock.connect(
          plyStat.addr,
          plyStat.port,
          plyStat.thread,
          log=logLimit)

        # Program status: False: onair / True: ended
        isDisconnected = False

        while isDisconnected is False:
            comments = msgSock.recv_comments()
            for comment in comments:
                if logFile:
                    cview.write_file(comment, logFile)

                parsed = cparser.parse_comment(comment)
                if parsed["tag"] == "thread":
                    continue

                # ID users
                if parsed["anonymity"] == "0":
                    toReload = cview.name_handle(parsed,
                                                 conf,
                                                 nameMapId)
                    if toReload is True:
                        nameMapId = cview.load_json(
                                      conf.nickNameId)
                # 184(anonymous) users
                elif parsed["anonymity"] == "1":
                    toReload = cview.name_handle(parsed,
                                                 conf,
                                                 nameMapAnon)
                    if toReload is True:
                        nameMapAnon = cview.load_json(
                                        conf.nickNameAnon)

                # Break when "/disconnect" is sent by admin/broadcaster.
                # Assign before mute.
                isDisconnected = all([parsed["content"] == "/disconnect",
                                      int(parsed["premium"]) > 1])

                muteConditions = [
                    conf.use_cmt_filter,
                    cmtFilter.ismatch(parsed["content"])
                ]
                if all(muteConditions):
                        continue

                if conf.narrow is False:
                    cview.show_comment(parsed,
                                       plyStat.start,
                                       conf.nameLength)
                elif conf.narrow is True:
                    cview.narrow_comment(parsed, conf.nameLength)

    print("Program ended.")


def parse_args(conf: cview.Config) -> argparse.Namespace:
    # 0 ~ 1000
    defaultlimit = conf.logLimit

    argParser = argparse.ArgumentParser(description=__doc__, add_help=True)
    # Nicolive url.
    #   lv[0-9]+ / co[0-9]+
    #   live/community page URL
    argParser.add_argument(
      "url",
      help="live/community URL",
      metavar="lv[XXXX]/co[XXXX]")
    # Logged in cookie.
    argParser.add_argument(
      "-c", "--cookie",
      help="specify cookie to use",
      default=conf.cookieFile)
    # Whether save log.
    argParser.add_argument(
      "-s", "--save-log",
      help="save comment log",
      action="store_true")
    # Past comment limit to acquire.
    # Don't use choices=range(0, 1001),
    # help becomes too verbose.
    argParser.add_argument(
      "-l", "--limit",
      help="comment log to get [0-1000]",
      default=defaultlimit,
      type=int)
    # Use mute filtering.
    argParser.add_argument(
      "-f", "--use-filter",
      help="use mute filter",
      action="store_true")
    # Display in narrow mode.
    argParser.add_argument(
      "-n", "--narrow",
      help="narrow mode",
      action="store_true")
    return argParser.parse_args()


if __name__ == "__main__":
    try:
        _main()
    except KeyboardInterrupt as kint:
        sys.exit("QUIT")

"""
TODO
    オブジェクトフィルタプラグインぽいの
    置換フィルタ
    カラー切り替え
    自動コテハン無効
    URLチェック
"""
