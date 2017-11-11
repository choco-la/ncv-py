#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate regex filtering dict."""

from typing import (Pattern, Iterable, Set)
import os
import re
import sre_constants


class MatchFilter():
    """The Class excecutes filtering method with set.

    Compiles filter words regex,
    use it to filtering check.

    Attributes:
        __regexset Compiled mute regex set.
    """

    def __init__(self, filepath: str) -> None:
        """Constructor.

        Set Compiled regex words to own property.

        Arguments:
            filepath: Regex words list text file.

        Returns:
            None
        """
        words = gen_word_set(filepath)
        self.__regexset = gen_reg_set(words)  # type: Set[Pattern]

    @property
    def word_set(self) -> Set[str]:
        words = {regex.pattern for regex in self.__regexset}
        return words

    @property
    def re_set(self) -> Set[Pattern]:
        return self.__regexset

    def ismatch(self, text: str) -> bool:
        """Check text matchs regex.

        Check if text matches regex set in even one.

        Arguments:
            text: strings to check with regex set.

        Returns:
            If matches in even one, True. If not, False.
        """
        return any(_.search(text) for _ in self.__regexset)


def gen_reg_set(words: Iterable[str]) -> Set[Pattern]:
    """Generate filtering compiled regex set.

    Generate set object from words.

    Arguments:
        words: Iterable words of regex.

    Returns:
        Compiled regex set.
    """
    regset = set()
    for word in words:
        try:
            # escaping quote/dquote is not needed.
            regex = re.compile(word.replace(r"\\", r"\\"))
        except sre_constants.error:
            pass
        else:
            regset.add(regex)
    return regset


def gen_word_set(txtfile: str) -> Set[str]:
    """Generate strings set from text file.
    """
    try:
        with open(txtfile, "r") as fopen:
            wordset = {ln.strip() for ln in fopen if not ignore(ln)}
    except FileNotFoundError:
        return set()
    except IOError:
        return set()

    return wordset


def ignore(line: str) -> bool:
    """Ignore comment/blank lines.
    """
    conditions = (
        line.startswith("#"),
        line == os.linesep
    )
    return any(conditions)


if __name__ == "__main__":
    import sys
    mutefilter = MatchFilter(sys.argv[1])

    for arg in sys.argv[2:]:
        result = mutefilter.ismatch(arg)
        print("{0}\t{1}".format(result, arg))
