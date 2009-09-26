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

'''A Parameter class for Pwytter'''

import xml.dom.minidom as dom
import os.path

class PwytterParams(object):
    """Handle the Pwtytter configuration in an XML file pwytter.xml
    """
    def __init__(self):
        self._paramPath = 'cfg'
        self._paramFileName = os.path.join(self._paramPath,'pwytter.xml')        
        self.values={}
        self._resetDefaults()
        
    def _resetDefaults(self):
        self.values['user'] = 'pwytterTest'
        self.values['password'] = 'pwytterTest'
        self.values['refresh_rate'] = '120'
        self.values['nb_lines'] = '4'
        self.values['theme'] = 'white'
        self.values['language'] = 'English'

    def __getitem__(self, aKey):
        return self.values[aKey]
        
    def __setitem__(self, aKey, value):
        self.values[aKey] = value

    def readFromXML(self):
        self._resetDefaults()
        self._paramDoc = dom.parse(self._paramFileName).documentElement
        assert self._paramDoc.tagName == 'pwytter'
        for val in self.values.keys(): 
            try :
                node=self._paramDoc.getElementsByTagName(val)
                self.values[val]=node[0].firstChild.data.strip()
            except Exception, e:
                print '!! Exception in process_node_string'+str(e)
                #self.values[val]=''
        print self.values
    
    def writeToXML(self):
        impl = dom.getDOMImplementation()
        self._paramDoc = impl.createDocument(None, 'pwytter', None)
        top_element = self._paramDoc.documentElement
        for val in self.values.keys(): 
            Element=self._paramDoc.createElement(val)
            Element.appendChild(self._paramDoc.createTextNode(str(self.values[val])))
            top_element.appendChild(Element)
        if not os.path.exists(self._paramPath) :
            os.makedirs(self._paramPath)
        f=open(self._paramFileName, 'w')
        f.write(self._paramDoc.toprettyxml())
        f.close()