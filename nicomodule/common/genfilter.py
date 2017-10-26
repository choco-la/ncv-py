#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate regex filtering dict."""

import re
from typing import (List, Pattern)


class MatchFilter():
    """The Class excecutes filtering method with list.

    Compiles filter words regex,
    use it to filtering check.

    Attributes:
        __wordlist(list): Mute regex words list.
        __regexlist(list): Compiled mute regex list.
    """

    def __init__(self, filepath: str) -> None:
        """Constructor.

        Set word list to own property.
        Compile these regex words.

        Arguments:
            filepath: Regex words list text file.

        Returns:
            None
        """
        self.__wordlist = self.gen_word_list(filepath)
        self.__regexlist = self.gen_reg_list(self.__wordlist)

    @property
    def re_list(self) -> List[Pattern]:
        return self.__regexlist

    def gen_word_list(self, filepath: str) -> List[str]:
        """Generate filtering word list.

        Generate list object from text file.

        Arguments:
            filepath: Path to text file of mute regex words.

        Returns:
            Words list of regex.
        """
        with open(filepath) as fopen:
            words = fopen.readlines()
        wordlist = []
        for word in words:
            ignorecondition = (word.startswith("#") or
                               word == "\n")
            if not ignorecondition:
                wordlist.append(word.strip())
        return wordlist

    def gen_reg_list(self, words: List[str]) -> List[Pattern]:
        """Generate filtering compiled regex list.

        Generate list object from words list.

        Arguments:
            words: Words list of regex.

        Returns:
            Compiled regex list.
        """
        reglist = []
        for word in words:
            try:
                # escaping quote/dquote is not needed.
                regex = re.compile(word.replace(r"\\", r"\\"))
            # Invalid regex causes sre_constants.error,
            # but NameError occurs.
            # -> `import sre_constants.error` is needed.
            except Exception as err:
                pass
            else:
                reglist.append(regex)
        return reglist

    def ismatch(self, text: str) -> bool:
        """Check text matchs regex.

        Check if text matches regex list in even one.

        Arguments:
            text: strings to check with regex list.

        Returns:
            If matches in even one, True. If not, False.
        """
        return any(_.search(text) for _ in self.__regexlist)


if __name__ == "__main__":
    import sys
    mutefilter = MatchFilter(sys.argv[1])

    for arg in sys.argv[2:]:
        result = mutefilter.ismatch(arg)
        print("{0}\t{1}".format(result, arg))
