#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""Unittest script."""
# python3 -m unittest tests/test.py

import unittest
import os
import nicomodule.common.nicoid as nicoid
import nicomodule.common.genfilter as genfilter


class TestGrepUrl(unittest.TestCase):
    def test_grep_ch(self):
        self.assertEqual(
          nicoid.grep_co("http://ch.nicovideo.jp/channel/ch1234?q=query"),
          "ch1234")

    def test_grep_lv(self):
        trueurls = [
            "lv1234",
            "nico.ms/lv1234?q=query",
            "https://live.nicovideo.jp/watch/lv1234",
            "live2.nicovideo.jp/watch/lv1234"
        ]
        for url in trueurls:
            self.assertEqual(nicoid.grep_lv(url), "lv1234")

        falseurls = [
            "example.com/lv1234",
            "testlv1234"
        ]
        for url in falseurls:
            self.assertRaises(ValueError, nicoid.grep_lv, (url))

    def test_grep_co(self):
        trueurls = [
            "co1234",
            "nico.ms/co1234?q=query",
            "https://com.nicovideo.jp/community/co1234",
            "com.nicovideo.jp/community/co1234"
        ]
        for url in trueurls:
            self.assertEqual(nicoid.grep_co(url), "co1234")

        falseurls = [
            "example.com/co1234",
            "testco1234"
        ]
        for url in falseurls:
            self.assertRaises(ValueError, nicoid.grep_co, (url))

    def test_grep_vid(self):
        trueurls = [
            "sm1234",
            "nico.ms/sm1234"
            "https://www.nicovideo.jp/watch/sm1234?q=query",
            "www.nicovideo.jp/watch/sm1234"
        ]
        for url in trueurls:
            self.assertEqual(nicoid.grep_video(url), "sm1234")

        falseurls = [
            "example.com/sm1234",
            "testsm1234"
        ]
        for url in falseurls:
            self.assertRaises(ValueError, nicoid.grep_video, (url))


class TestFilter(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.truelist = ["d.ot",
                         "0123",
                         '"',
                         "/hb ifseetno 0"]
        self.falselist = [" text",
                          "(invalid_regex",
                          "notmatch"]
        filepath = os.path.join("tests", "filter", "mute-example.txt")
        self.filter = genfilter.MatchFilter(filepath)

    def setUp(self):
        pass

    def test_filter_ignore(self):
        self.assertEqual(len(self.filter.re_list), 6)

    def test_filter_word_0(self):
        text = self.truelist[0]
        self.assertTrue(self.filter.ismatch(text))

    def test_filter_all_1(self):
        for text in self.truelist:
            self.assertTrue(self.filter.ismatch(text))

    def test_filter_all_2(self):
        for text in self.falselist:
            self.assertFalse((self.filter.ismatch(text)))

    def tearDown(self):
        pass


if __name__ == "__main__":
    unittest.main()
