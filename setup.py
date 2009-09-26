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

"""
 py2app/py2exe build script for Pwytter.

 Will automatically ensure that all build prerequisites are available
 via ez_setup

 Usage (Mac OS X):
     python setup.py py2app

 Usage (Windows):
     python setup.py py2exe
"""

import ez_setup
ez_setup.use_setuptools()
from setuptools import setup

import os, sys
import glob, fnmatch
from pwytter import __version__ as VERSION

mainscript = 'pwytter.py'

def rec_glob(path,*masks):
    l=[]
    d={}
    for root, dirs, files in os.walk(path):
        for m in masks:
            l=l+ glob.glob(os.path.join(root,m))
    for f in l:
        p,n= os.path.split(f)
        if p not in d.keys():
            d[p]=[]
        d[p]=d[p]+[f]
    return d


if sys.platform == 'darwin':
    extra_options = dict(
        setup_requires = ['py2app'],
        app = [mainscript],
        # Cross-platform applications generally expect sys.argv to
        # be used for opening files.
        options = dict(
            py2app = dict(
                argv_emulation=True,
                resources = ["theme","locale","media"],
                #distdir = 'MacBinaries'
            ),
            plist = dict(
                CFBundleName='Pwytter',
                CFBundleIconFile='media/pwytter.icns',
                #CFBundleDocumentTypes=[
                #     dict(
                #         CFBundleTypeName=DB_FILE_TYPE,
                #         CFBundleTypeRole='Editor',
                #         NSDocumentClass='PackageDatabase',
                #         # CFBundleTypeIconFile='Package Database.icns',
                #         CFBundleTypeExtensions = ['packman', 'plist' ],
                #         CFBundleTypeOSTypes=[],
                #     ),
                # ],
                CFBundleGetInfoString=VERSION+', Pierre-Jean Coudert 2007, GNU GPL Licence',
                CFBundleIdentifier='com.pwytter',
                CFBundleShortVersionString=VERSION,
                CFBundleVersion=VERSION,
                # We need at least Panther, it may work on Jaguar but I've not yet
                # verified if it should work.
                LSMinimumSystemVersion='10.3.0',
                 # We're not apple-scriptable
                NSAppleScriptEnabled='No',
            ),
        ),
    )

elif sys.platform == 'win32':
    import py2exe
    extra_options = dict(
        setup_requires = ['py2exe'],
        windows = [
            {"script": mainscript,
             "icon_resources": [(1, "media\\pwytter.ico")]
            }],
    )
else:
    extra_options = dict(
        # Normally unix-like platforms will use "setup.py install"
        # and install the main script as such
        scripts=[mainscript],
    )

setup(  
  name = "pwytter",
  version = VERSION,

  #install_requires = ["simplejson", "PIL"],
  #packages
  packages=['twclient'],
  package_dir={'twclient': 'twclient',
               'simplejson': 'twclient/simplejson'},
  #package_data={'twclient': glob.glob('twclient/doc/*.*')},
  py_modules = ['pwytter','tkBalloon','pwParam','pwTools','pwSplashScreen', 'pwTheme'],
  data_files=[("text", glob.glob("*.txt")),
              ("theme", glob.glob("theme\\*.pwt")),
              ("media", glob.glob("media\\*.png")
                        + glob.glob("media\\*.gif")
                        + glob.glob("media\\*.ico")
                        + glob.glob("media\\*.icns"))
              ]
              +rec_glob("locale","*.po","*.mo").items(),
  #
  #This next part is for the Cheese Shop.
  author='Pierre-Jean Coudert',
  author_email='coudert@free.fr',
  description='A python client for Twitter',
  long_description='A python client for Twitter. Portable User Interface in Tk.',
  license='GPL 2',
  platforms=['any'],
  url='http://www.pwytter.com',
  download_url='http://www.pwytter.com/download/',
  keywords='twitter client python tkinter',

  classifiers = [
      'Development Status :: 4 - Beta',
      'Environment :: MacOS X',
      'Environment :: Win32 (MS Windows)',
      'Environment :: X11 Applications',     
      'Intended Audience :: End Users/Desktop',
      'Intended Audience :: Developers',
      'License :: OSI Approved :: GNU General Public License (GPL)',
      'Operating System :: Microsoft :: Windows',
      'Operating System :: MacOS :: MacOS X',
      'Operating System :: POSIX :: Linux',
      'Programming Language :: Python',
      'Topic :: Communications :: Chat',
      'Topic :: Internet'
  ],
  
  **extra_options
)
