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
  The Twitter Client encapsulated for Pwytter
"""

import twitter
import pwCache
import urllib2
import StringIO
import os.path
import Queue
import threading
import simplejson
import time
import operator
from urlparse import urlparse,urlunparse
from PIL import Image, ImageTk
import re
from htmlentitydefs import name2codepoint

AUTOBLOCK = 'autoblock'

class TwClientError(Exception):
  '''Base class for TwClient errors'''

def htmlentitydecode(s):
    return re.sub('&(%s);' % '|'.join(name2codepoint), 
            lambda m: unichr(name2codepoint[m.group(1)]), s)

def urlExtract(msg):
    urlstart = msg.find("http://")
    if urlstart > -1 :
        msgurl = msg[urlstart:].split(' ')[0]
        urlDetected = urlunparse(urlparse(msgurl)).split('"')[0]
    else:
        urlDetected = ''
    return urlDetected
    
StatusType = ['standard', 'reply', 'direct']    

class ExtStatus(twitter.Status):
    def __init__(self, created_at=None, id=None, text=None,
                 user=None, now=None, type='standard'):
        twitter.Status.__init__(self,created_at,id,text,user,now)
        self._type = type        
        
    def GetType(self):
        '''Get the type of this status.
        '''
        return self._type

    def SetType(self, type):
        '''Set the type of this status.
        '''
        self._type = type

    type = property(GetType, SetType,
                    doc='The type of this status.')        

class PwDeferedTwitter(object):
    """ An ansynchronous URL loader. It uses URL Filesystem caching
        It can use an _NewObjectFromURL function to create an object from the data
        This object is cached in a dict (url,object) in memory
    """
    def __init__(self, pwClient=None, timeout=500):
        self._notAvailableObject = None
        self._timeout = timeout
        self._keyQueue = Queue.Queue()
        self._objectQueue = Queue.Queue()
        self._dataCache = {}
        self._requestedKeys = []
        
    def _threadLoadData(self):
        key, call = self._keyQueue.get()
        needToCall = True
        while needToCall:
            try:
                data = call()
                needToCall = False
            except Exception, e:
                print "Deferred load error:", str(e)
                time.sleep(1000)
                needToCall = True
        self._objectQueue.put((key, data))       
        #self._objectQueue.task_done()

    def _dataToCache(self):
        while not self._objectQueue.empty():
            key,dataObject = self._objectQueue.get() 
            self._dataCache[key]=dataObject
            #self._dataCache.task_done()

    def _requestData(self, key, call):
        if key not in self._requestedKeys:
            self._requestedKeys.append(key)
            self._keyQueue.put( (key,call) )
            t = threading.Thread(None,self._threadLoadData)
            t.setDaemon(True)
            t.start() 
            
    def Get(self, key, call):
        """  Get returns the object/data corresponding to call
             >>>>  (True, Object)
             If the requested URL is currently loading (in a separate thread) 
               getData returns then notAvailableObject object/data
             >>>>  (False, notAvailableObject)           
        """
        self._dataToCache()
        if key not in self._dataCache.keys() :
            self._requestData(key,call)
            return False, self._notAvailableObject
        return True, self._dataCache[key]

class TwClient(object):
    def __init__(self, aVersion, params):
        self._params = params
        self.user, self.password = params['user'], params['password']
        self.api = twitter.Api(self.user,self.password)
        self.api.SetXTwitterHeaders('pwytter', 'http://www.pwytter.com/files/meta.xml', aVersion)       
        self.api.SetSource('pwytter')       

        self._cache= pwCache.PwytterCache()
        self._imageLoading = Image.open(os.path.join("media",'loading.png'))
        self._imageLoading.thumbnail((32,32),Image.ANTIALIAS)
        self._imageLoader=pwCache.PwDeferedLoader(NewObjectFromURL=self.ConvertImage, 
                                                    notAvailableObject=self._imageLoading, 
                                                    timeout=3600*24)

        self._favoriteLoader=pwCache.PwDeferedLoader(NewObjectFromURL=self.ConvertFavoriteHTML, 
                                                    notAvailableObject=False, 
                                                    timeout=3600*24,
                                                    urlReader= self.api._FetchUrl)
        self._deferredLoader = PwDeferedTwitter()
        
        self._statuses =[]
        self.texts = []
        self.ids = []
        self._friends = []
        self.Friends=[]
        self._followers = []
        self.Followers=[]
        self._usercache={}
        self.timeLines=("User","Friends","Replies","Direct", "Composite","Public")
        self._currentTimeLine = "Friends"  
        self._filters = []
        self.get_filters()
        
        self._currentVersion = float(aVersion)
        self.VersionOK = False
        
    def _checkversion(self):
        versionURL="http://www.pwytter.com/files/PWYTTER-VERSION.txt"
        try:
            lastVersion= float(urllib2.urlopen(versionURL).read())
            print '>> Verified Pwytter last Version:',lastVersion
        except Exception,e:
            print "Unable to check Pwytter Version:",str(e)
            lastVersion = self._currentVersion            
        return lastVersion <= self._currentVersion
        
    def VersionChecked(self):
        loaded, self.VersionOK = self._deferredLoader.Get('pwytter_version', 
                                                          self._checkversion)
        return loaded

    def login(self, aUser, aPassword):
        self.user, self.password = aUser, aPassword     
        self.api.SetCredentials(self.user, self.password)

    def _getMe(self):
        return self.userFromCache(self.user)
    
    def getMyDetails(self):
        userloaded, self.me = self._deferredLoader.Get('user:%s' % self.user,
                                                       self._getMe)
        imageloaded, self.myimage = self.imageFromCache(self.user)
        print "My details",self.me
        return userloaded and imageloaded

    def setTimeLine(self, timelineName):
        if timelineName in self.timeLines:
            self._currentTimeLine = timelineName

    def timeLineName(self):
        return self._currentTimeLine
       
    def _getCurrentTimeLine(self):
        if self._currentTimeLine=="Public":
            self._statuses = self.StatusesToExt(self.api.GetPublicTimeline(),'standard')
        elif self._currentTimeLine=="User":
            self._statuses = self.StatusesToExt(self.api.GetUserTimeline(self.user),'standard')
        elif self._currentTimeLine=="Replies":
            self._statuses = self.StatusesToExt(self.api.GetReplies(),'reply')
        elif self._currentTimeLine=="Direct":
            self._statuses = self.getDirectsAsStatuses()
#        elif self._currentTimeLine=="Favorites":
#            self._statuses = self.StatusesToExt(self.api.GetFavorites(self.user),'standard')                       
        elif self._currentTimeLine=="Composite":
            self._statuses = self.StatusesToExt(self.api.GetFriendsTimeline(),'standard') \
                                + self.StatusesToExt(self.api.GetReplies(),'reply') \
                                + self.getDirectsAsStatuses()
            self._statuses.sort(key=ExtStatus.GetCreatedAtInSeconds,
                                reverse=True)
        else :
            self._statuses = self.StatusesToExt(self.api.GetFriendsTimeline(),'standard')

    def StatusesToExt(self, aTimeline, aType):
        """ return a status list as a ExtStatus list
        """
        statuses=[]
        for status in aTimeline:
            extstatus = ExtStatus(               
               created_at=status.created_at,
               id=status.id,
               text=status.text,
               user=status.user,
               type=aType)
            statuses += [extstatus]
        return statuses
            
    def getDirectsAsStatuses(self):
        """ return a DirectMessages list as a ExtStatus list
        """
        statuses=[]
        try:
            directs=self.api.GetDirectMessages()
            for direct in directs:
                try :
                    auser=self.userFromCache(direct.sender_screen_name)
                except :
                    auser=self.userFromCache('Pwytter')              
                extstatus = ExtStatus(               
                   created_at=direct.created_at,
                   id=direct.id,
                   text=direct.text,
                   user=auser,
                   type='direct')
                statuses += [extstatus]
        except Exception, e:
            print str(e)
        return statuses

    def createFavorite(self, screen_name, id):
        '''Favorites the status specified in the ID parameter as the authenticating user.  
    
        The twitter.Api instance must be authenticated and thee
        authenticating user must be the author of the specified status.
    
        Args:
          id: The numerical ID of the status you're trying to favorite.
        '''
        try:
          if id:
            int(id)
        except:
          raise TwClientError("id must be an integer")
        url = 'http://twitter.com/favourings/create/%s' % id
        json = self.api._FetchUrl(url)
        #update cache 
        url = 'http://twitter.com/%s/statuses/%s ' % (screen_name, id)
        self._cache.Set(url,str(True))

    def isFavorite(self, screen_name, id):
        '''Favorites the status specified in the ID parameter as the authenticating user.  
    
        The twitter.Api instance must be authenticated and thee
        authenticating user must be the author of the specified status.
    
        Args:
          screen_name :
          id: The numerical ID of the status you're trying to favorite.
    
        Returns:
          loaded, favorited
        '''
        try:
          if id:
            int(id)
        except:
          raise TwClientError("id must be an integer")
        url = 'http://twitter.com/%s/statuses/%s ' % (screen_name, id)
        return self._favoriteLoader.getData(url) 

    def ConvertFavoriteHTML(self, data):
        return data.find('Icon_star_full') > 0
        
    def destroyFavorite(self, screen_name,  id):
        '''Un-favorites the status specified in the ID parameter as the authenticating user.
    
        The twitter.Api instance must be authenticated and thee
        authenticating user must be the author of the specified status.
    
        Args:
          id: The numerical ID of the status you're trying to favorite.
        '''
        try:
          if id:
            int(id)
        except:
          raise TwClientError("id must be an integer")
        url = 'http://twitter.com/favourings/destroy/%s' % id
        json = self.api._FetchUrl(url)
        #update cache 
        url = 'http://twitter.com/%s/statuses/%s ' % (screen_name, id)
        self._cache.Set(url,str(False))
        
    def refresh(self):
        self._getCurrentTimeLine()
        for s in self._statuses :
            self._addUserToCache(s.user)
            atime= s.relative_created_at
#            try:
#                atime= s.relative_created_at.encode('latin-1','replace')
#            except Exception, e:
#                print "Time conversion error:",e
#                atime = "..."
            #print s
            try :
                user_url = s.user.url.encode('latin-1','replace')
            except Exception, e:
                user_url = ""
                
            loaded, favorited = False, False
            if s.type <> 'direct':
                loaded, favorited = self.isFavorite(s.user.screen_name, s.id)
               
            msg = htmlentitydecode(s.text).encode('latin-1','replace')
            if self._filters:
                msg_lower = msg.lower()
                censor = False
                for filter in self._filters:
                    if filter in msg_lower:
                        censor = True
                        break
                if censor:
                    continue

            #remove existing ids : in composite timeline to keep replies 
            if s.id in self.ids:
                continue
                #self.texts.pop()
            else:
                self.ids.append(s.id)
            print s.id
            self.texts.append({"name": s.user.screen_name.encode('latin-1','replace'),
                               "id": s.id,
                               "msg" : msg,
                               "msgunicode" : htmlentitydecode(s.text),
                               "url" : urlExtract(msg),
                               "time": "(%s)" % (atime),
                               "type" : s.type,
                               "user_url" : user_url,
                               "favorite" : favorited,
                               "favorite_updated" : loaded
                              })
        self.texts.sort(key=operator.itemgetter('id'),)# reverse=True)
           
                    
    def sendText(self,aText):
        if aText.lower().strip().startswith(AUTOBLOCK):
            filters = aText.lower().strip()[len(AUTOBLOCK):].strip().split(" ")
            if filters[-1] == 'off':
                filters.pop()
                self.remove_filters(filters)
            elif filters[-1] == 'clear':
                self._filters = []
                self.save_filters()
            else:
                if  filters[-1] == 'on':
                    filters.pop()
                self.add_filters(filters)
            return
        self._statuses = self.api.PostUpdate(aText)
        
    def sendDirectMessage(self, aUser, aText):
        return self.api.PostDirectMessage(aUser, aText)

    def getFriends(self):
        loaded, self._friends = self._deferredLoader.Get("friends:%s" % self.user,
                                                         self.api.GetFriends)
        self.Friends=[]
        if loaded:
            for f in self._friends :
                self._addUserToCache(f)
                friendName= f.screen_name.encode('latin-1','replace')
                self.Friends.append(friendName)
        return loaded

    def get_filters(self):
        self._filters = self._params.load_filters()
        print "loading filters", self._filters

    def add_filters(self,filters):
        for filter in filters:
            if not (filter in self._filters):
                self._filters.append(filter)
        self.save_filters()
    def remove_filters(self,filters):
        for filter in filters:
            try:
                self._filters.remove(filter)
            except ValueError:
                pass
        self.save_filters()

    def save_filters(self):
        print "saving filters", self._filters
        self._params.save_filters(self._filters)



    def getFollowers(self):
        loaded, self._followers = self._deferredLoader.Get("followers:%s" % self.user, 
                                                           self.api.GetFollowers)
        self.Followers=[]
        if loaded:
            for f in self._followers :
                self._addUserToCache(f)
                fName= f.screen_name.encode('latin-1','replace')
                self.Followers.append(fName)
        return loaded
                
    def ConvertImage(self,image):
        returnImage = Image.open(StringIO.StringIO(image))
        returnImage.thumbnail((32,32),Image.ANTIALIAS)
        return returnImage
    
    def imageFromCache(self,name):
        auser = self.userFromCache(name)
        if not auser :                
            return False, self._imageLoading
        imageurl = auser.profile_image_url.encode('latin-1','replace')        
        return self._imageLoader.getData(imageurl)
           
    def _addUserToCache(self, aUser):
        if aUser.screen_name not in self._usercache.keys() :  
            self._usercache[aUser.screen_name]=aUser
        
    def userFromCache(self, name):
        if name not in self._usercache.keys() :  
            userDict = self._cache.GetTimeout('user//'+name, timeout = 3600)
            if userDict :
                aUser = twitter.User.NewFromJsonDict(simplejson.loads(userDict))
            else:
                aUser = self.api.GetUser(name)  
                self._cache.Set('user//'+name,aUser.AsJsonString())
            self._addUserToCache(aUser)       
            return aUser
        else :     
            return self._usercache[name]
