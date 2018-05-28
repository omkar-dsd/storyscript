# -*- coding: utf-8 -*-
from lark import Lark
from lark.common import UnexpectedToken

from .grammar import Grammar
from .indenter import CustomIndenter
from .transformer import Transformer


class Parser:
    """
    Wraps up the parser submodule and exposes parsing and lexing
    functionalities.
    """
    def __init__(self, algo='lalr', ebnf_file=None):
        self.algo = algo
        self.ebnf_file = ebnf_file

    def indenter(self):
        """
        Initialize the indenter
        """
        return CustomIndenter()

    def transformer(self):
        """
        Initialize the transformer
        """
        return Transformer()

    def lark(self):
        """
        Get the grammar and initialize Lark.
        """
        grammar = self.grammar.build()
        return Lark(grammar, parser=self.algo, postlex=self.indenter())

    def parse(self, source):
        """
        Parses the source string.
        """
        lark = self.lark()
        try:
            tree = lark.parse(source)
        except UnexpectedToken:
            return None
        return self.transformer().transform(tree)

    def lex(self, source):
        """
        Lexes the source string
        """
        return self.lark().lex(source)
