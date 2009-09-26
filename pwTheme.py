#!/usr/bin/python
#
#   Author : Pierre-Jean Coudert
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; version 2 of the License.
# 
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.

import os
import glob

class pwTheme(object):
    """
    Usage:
    th=pwTheme('blue')
    th.readFromFile()
    print th.themeList
    print th.values
    """
    def __init__(self, aName="black"):
        self._themePath = 'theme'
        self.themeList = [os.path.splitext(os.path.basename(theme))[0] for theme in \
                           glob.glob(os.path.join(self._themePath, '*.pwt'))]
        self.values={}
        self._initDefault()
        self.setTheme(aName)

    def setTheme(self, aName):
        if aName in self.themeList:
            self.themeName = aName
        else:
            self.themeName = self.themeList[0]
        self._themeFile = os.path.join(self._themePath, self.themeName+'.pwt') 
        try:
            self._readFromFile()
        except Exception, e:
            print "Error reading theme", aName,":",str(e)
        
    def _initDefault(self):
        self.values={
            'text#'     : "white",
            'bg#'       : "#1F242A",
            '1stLine#'  : "#484C4F",
            'line#'     : "#2F3237",
            'directLine#': "#FFCCCC",
            'replyLine#' : "#FFFFCC",
            'param#'    : "#585C5F",
            'timeline#' : "#484C4F",
            'me_bg#'    : "#2F3237", 
            'me_fg#'    : "#BBBBBB",
            'time#'     : "#BBBBBB",
            'message#'  : "#99CBFE",
            'messageUrl#': "#B9DBFF",
            'directMsg#': "#686C6F",
            'update#'   : "#FFBBBB",
            'twitEdit#' : "#2F3237"
            }
        
    def _readFromFile(self):
        f = open(self._themeFile,'r')
        for line in f.readlines():
            color, value = line.split(':')
            color, value = color.strip(), value.strip()
            self.values[color] = value

    def __getitem__(self, aKey):
        return self.values[aKey]
        
    def __setitem__(self, aKey, value):
        self.values[aKey] = value
            