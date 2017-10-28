#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Connect to the comment server."""

import socket
from typing import List


class MsgSocket():
    """Socket handling class.

    Connection handling class.
    Use with context to call close surely.

    Attributes:
        __msgsock: Socket with comment server.
    """
    def __init__(self) -> None:
        """Constructor.

        In case network is ipv6, is socket.create_connection preferable?

        Arguments:
            None

        Returns:
            None
        """
        self.__msgsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self,
                addr: str,
                port: int,
                thread: int,
                log: int=20) -> socket.socket:
        """Connect to comment server.

        Connect to server, then send initial data to
        recieve comment.

        Arguments:
            addr: Comment server's host address.
            port: Comment server's port number.
            thread: Comment server's thread number.
            log: Number of past comment(0<= x <=1000).
        """
        self.__msgsock.connect((addr, port))

        msgthread = str(thread)
        resfrom = str(log)
        initsend = ('<thread thread="{}" version="20061206" res_from="-{}"/>'
                    .format(msgthread, resfrom))
        endbyte = b"\x00"
        self.__msgsock.send(initsend.encode("utf-8"))
        self.__msgsock.send(endbyte)

        return self.__msgsock

    def receive(self, buffer: int=4096) -> List[bytes]:
        """Recieve comment data.

        Recieve comment data from socket.
        Split data with null string.

        Argument:
            buffer: The buffer size for recieving data.

        Returns:
            Splitted comment data with null string.
        """
        endbyte = b"\x00"

        rawdata = self.__msgsock.recv(buffer).split(endbyte)
        return rawdata

    def recv_comments(self, partstr: str=None) -> List[str]:
        """Returns comment data.

        Returns comment dom data recieved from socket.
        If partial dom passed,
        concatenate with recieved strings
        (assert it also to be partial).

        Argument:
            partstr: A partial dom strings.

        Returns:
            List of comment dom strings.
        """
        rawdata = self.receive()
        comments = []
        for rawdatum in rawdata:
            if partstr:
                decdata = partstr + rawdatum.decode("utf-8")
                partstr = None
            else:
                decdata = rawdatum.decode("utf-8")
            if decdata.endswith(">"):
                comments.append(decdata)
            else:
                partstr = decdata

        if partstr:
            comments += self.recv_comments(partstr)

        return comments

    def close(self) -> None:
        """Close socket.

        This is also called by with context(__exit__).

        Arguments:
            None

        Returns:
            None
        """
        self.__msgsock.close()

    def __enter__(self):
        return self

    def __exit__(self, extype, exvalue, traceback):
        self.close()
