# -*- coding: utf8 -*-
from burpui.misc.parser.burp1 import Parser as Burp1

# inherit Burp1 parser so we can just override available options
class Parser(Burp1):
    pver = 2

