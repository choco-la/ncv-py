#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parse getplayerstatus.xml."""

from typing import Optional
from urllib import request
from xml.dom import minidom
import sys


def _main() -> None:
    if len(sys.argv) > 1:
        xmlfile = sys.argv[1]
        with open(xmlfile, "r") as xmlopen:
            pstat = xmlopen.read()
            lvstatus = LivePlayerStatus(pstat)
    else:
        _show_usage()
        exit(1)
    statDict = {
        "lvid": lvstatus.lvid,
        "title": lvstatus.title,
        "community": lvstatus.community,
        "owner": lvstatus.owner,
        "seetno": lvstatus.seetno,
        "addr": lvstatus.addr,
        "port": lvstatus.port,
        "thread": lvstatus.thread
    }
    print(str(statDict))


def _show_usage() -> None:
    print("Usage: {} getplayerstatus.xml".format(__file__), file=sys.stderr)


def get_live_player_status(session: str, liveid: str) -> str:
    """Retrieve getplayerstatus.xml.

    Arguments:
        session: Sesseion value of user_session from cookie.
        liveid: Content id, like lv2525, co2525 and ch2525.

    Returns:
        Text content of getplayerstatus.xml's.
    """
    baseurl = "http://live.nicovideo.jp/api/getplayerstatus"
    url = baseurl + "?v={}".format(liveid)

    req = request.Request(url)
    req.add_header("Cookie", "user_session={}".format(session))
    try:
        with request.urlopen(req) as resp:
            pstat = resp.read().decode("utf-8")
    except IOError as err:
        sys.exit("[ERR] HTTP request: {} {}".format(url, err.args))
    else:
        return pstat


class LivePlayerStatus():
    """Handling getplayerstatus.xml's properties.

    Parse getplayerstatus.xml, store its properties.

    Attributes:
        errcode: closed/commingsoon etc if it is not onair.
        lvid: Content id.
        title: Program's title.
        start: The time prgram started.
        community: Streaming community id.
        owner: Broadcaster's name.
        seetno: My Seet number.

        rtmpurl: Rtmp url for streaming.
        ticket: The ticket value.
        addr: Address for conection.
        port: Comment server's port number.
        thread: Comment server's thread number.

    TODO: Use getter.
    """
    def __init__(self, pstat: str) -> None:
        """Constructor.

            Set values to own properties.

            Arguments:
                pstat: getplayerstatus.xml's text content.

            Returns:
                None
        """
        xmldom = minidom.parseString(pstat)
        body = xmldom.getElementsByTagName("getplayerstatus")[0]

        try:
            errtag = body.getElementsByTagName("error")[0]
        except IndexError:
            self.errcode = None  # type: Optional[str]
        else:
            self.errcode = (errtag.getElementsByTagName("code")[0]
                            .firstChild.data.strip())
            return

        streamtag = body.getElementsByTagName("stream")[0]
        self.lvid = (streamtag.getElementsByTagName("id")[0]
                     .firstChild.data.strip())  # type: str
        self.title = (streamtag.getElementsByTagName("title")[0]
                      .firstChild.data.strip())  # type: str
        msstart = (streamtag.getElementsByTagName("start_time")[0]
                   .firstChild.data.strip())
        self.start = int(msstart)  # type: int

        # Official programs don't has default_community key.
        try:
            self.community = (streamtag.getElementsByTagName(
                                "default_community")[0]
                              .firstChild.data.strip())  # type: str
        except AttributeError:
            self.community = "official"

        # Official programs don't has owner_name key.
        try:
            self.owner = (streamtag.getElementsByTagName("owner_name")[0]
                          .firstChild.data.strip())  # type: str
        except AttributeError:
            self.owner = "official"

        usertag = body.getElementsByTagName("user")[0]
        self.seetno = (usertag.getElementsByTagName("room_seetno")[0]
                       .firstChild.data.strip())  # type: str

        # Some official programs don't has rtmpurl key.
        rtmp = body.getElementsByTagName("rtmp")[0]
        try:
            self.rtmpurl = (rtmp.getElementsByTagName("url")[0]
                            .firstChild.data.strip())  # type: str
        except AttributeError:
            pass
        self.ticket = (rtmp.getElementsByTagName("ticket")[0]
                       .firstChild.data.strip())  # type: str

        mstag = body.getElementsByTagName("ms")[0]
        self.addr = (mstag.getElementsByTagName("addr")[0]
                     .firstChild.data.strip())  # type: str
        msport = (mstag.getElementsByTagName("port")[0]
                  .firstChild.data.strip())
        self.port = int(msport)  # type: int
        msthread = (mstag.getElementsByTagName("thread")[0]
                    .firstChild.data.strip())
        self.thread = int(msthread)  # type: int


if __name__ == "__main__":
    _main()
