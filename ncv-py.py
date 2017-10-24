#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Niconico comment viewer using nicomodule."""

import sys
import re
import os
import argparse
from json import JSONDecodeError

from nicomodule.common import (genfilter,
                               nicookie,
                               nicoid,
                               nickname,
                               nauth)
from nicomodule.live import (cparser,
                             niconnect,
                             pstat)
from nicomodule.app import cview


def _main():
    # Initial configurations.
    confDict = {
        "cookieDir": os.path.join("cookie", ""),
        "filterDir": os.path.join("filter", ""),
        "logDir": os.path.join("log", ""),
        "cookieFile": "cookie.txt",
        "muteReCmt": "mute-re-comment.txt",
        "nickNameId": "nickname-id.txt",
        "nickNameAnon": "nickname-anon.txt",
        "use_cmt_filter": False,
        "logLimit": 20,
        "nameLength": 12,
        "narrow": False
    }
    # Path to file.
    confDict["p-muteReCmt"] = os.path.join(confDict["filterDir"],
                                           confDict["muteReCmt"])
    confDict["p-nickNameId"] = os.path.join(confDict["filterDir"],
                                            confDict["nickNameId"])
    confDict["p-nickNameAnon"] = os.path.join(confDict["filterDir"],
                                              confDict["nickNameAnon"])

    cview.mk_dir(confDict["cookieDir"])
    cview.mk_dir(confDict["filterDir"])
    nickname.touch_json(confDict["p-nickNameId"])
    nickname.touch_json(confDict["p-nickNameAnon"])
    nameMapId = cview.load_json(confDict["p-nickNameId"])
    nameMapAnon = cview.load_json(confDict["p-nickNameAnon"])

    parsedArgs = parse_args(confDict)

    # If narrow option is explicited or configured, True.
    if confDict["narrow"] is True:
        pass
    elif confDict["narrow"] is False:
        confDict["narrow"] = parsedArgs.narrow

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
            cmtFilter = (genfilter.MatchFilter(confDict["p-muteReCmt"]))
            confDict["use_cmt_filter"] = True
        # Disable comment filtering if any errors occurred.
        except IOError as err:
            print("[ERR] {0}: comment filter disabled."
                  .format(confDict["p-muteReCmt"]),
                  file=sys.stderr)
            cmtFilter = None
            confDict["use_cmt_filter"] = False
    elif parsedArgs.use_filter is False:
        if confDict["use_cmt_filter"] is True:
            try:
                cmtFilter = (genfilter.MatchFilter(confDict["p-muteReCmt"]))
            # Disable comment filtering if any errors occurred.
            except IOError as err:
                print("[ERR] {0}: comment filter disabled."
                      .format(confDict["p-muteReCmt"]),
                      file=sys.stderr)
                cmtFilter = None
                confDict["use_cmt_filter"] = False
        elif confDict["use_cmt_filter"] is False:
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
    if plyStat.errcode is not None:
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
        cview.mk_dir(confDict["logDir"])
        cview.mk_dir(os.path.join(confDict["logDir"],
                                  plyStat.community + ""))

        logFile = os.path.join(confDict["logDir"],
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

        # Partial dom strings of <chat>
        partStr = None
        # Program status: False: onair / True: ended
        isDisconnected = False

        while isDisconnected is False:
            rawdatas = msgSock.receive()
            for rawdata in rawdatas:
                decdata = cview.decode_data(rawdata, partStr)
                partStr = None

                # To tell the data is partial or not,
                # parse it before logging.
                parsed = cparser.parse_comment(decdata)
                if logFile is None:
                    pass
                elif parsed["tag"] != "partial":
                    cview.write_file(decdata, logFile)

                if parsed["tag"] == "thread":
                    continue
                if parsed["tag"] == "partial":
                    partStr = parsed["data"]
                    continue

                assert parsed["tag"] is "chat"
                # ID users
                if parsed["anonymity"] == "0":
                    toReload = cview.name_handle(parsed,
                                                 confDict,
                                                 nameMapId)
                    if toReload is True:
                        nameMapId = cview.load_json(
                                      confDict["p-nickNameId"])
                # 184(anonymous) users
                elif parsed["anonymity"] == "1":
                    toReload = cview.name_handle(parsed,
                                                 confDict,
                                                 nameMapAnon)
                    if toReload is True:
                        nameMapAnon = cview.load_json(
                                        confDict["p-nickNameAnon"])

                cview.show(parsed, confDict, cmtFilter, plyStat)

                # Break when "/disconnect" is sent by admin/broadcaster.
                isDisconnected = all([parsed["content"] == "/disconnect",
                                      int(parsed["premium"]) > 1])

    print("Program ended.")


def parse_args(conf: dict) -> argparse.Namespace:
    pathtocookie = os.path.join(conf["cookieDir"],
                                conf["cookieFile"])
    # 0 ~ 1000
    defaultlimit = conf["logLimit"]

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
      default=pathtocookie)
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
