#! /usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 25.11.2010

@author: moschlar
'''
from irclib import nm_to_n

RESPONSES_FILE = "responses.pkl"
CONFIG_FILE = "testbot.cfg"

class Responder(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        self.responses = {}
        self.loadResponses()
        return
    
    def saveResponses(self):
        """
        Saves pickled responses to the file RESPONSES_FILE
        """
        import pickle
        storage = file(RESPONSES_FILE, "wb")
        pickle.dump(self.responses,storage,protocol=pickle.HIGHEST_PROTOCOL)
        storage.close()
        return
    
    def loadResponses(self):
        """
        Loads pickled responses from the file RESPONSES_FILE
        """
        import pickle
        storage = file(RESPONSES_FILE, "rb")
        self.responses = pickle.load(storage)
        storage.close()
        return
    
    def respondTo(self,c,e,line):
        for (keyword,response) in self.responses.items():
            if line.lower().find(keyword.lower()) != -1:
                print("Found %s" % keyword)
                c.privmsg(e.target(), response)
        
    
    def doCommand(self,c,e,a):
        pass

    def getAuth(self,c,e,nick):
        """
        Determines highest current user level of nick
        
        Result: n: normal users, v: voiced users, o: op users
        """
        auth = "n"
        for chname,chobj in self.channels.items():
            if nm_to_n(nick) in chobj.opers():
                auth = "o"
                break
            if nm_to_n(nick) in chobj.voiced():
                auth = "v"
        print ("%s has +%s" % (nm_to_n(nick),auth))
        return auth

    def response(self,c,e,action):
        """
        Handles response actions
        """
        cmd = action.split(None,1)[0]
        params = action.split(None,2)[1:]
        
        authOp = self.getAuth(c, e, e.source()) == "o"
        
        if cmd == "list":
            c.privmsg(e.source(),self.responses.keys())
        elif cmd == "set" and len(params) == 2:
            self.responses[params[0]] = params[1]
            c.privmsg(e.source(),"Set %s to %s" % (params[0],params[1]))
            self.saveResponses()
        elif cmd == "del" and len(params) >= 1:
            # If we don't have the keyword or user is not auth, we must not try to do anything
            if params[0] in self.responses.keys() and authOp:
                c.privmsg(e.source(),"%s gel�scht" % params[0])
                del(self.responses[params[0]])
                self.saveResponses()
            else:
                c.privmsg(e.source(), "Des geht nit!")
        elif cmd == "init":
            if authOp:
                from ConfigParser import SafeConfigParser
                config = SafeConfigParser()
                config.read(CONFIG_FILE)
                
                responses = {}
                for i in config.items("responses"):
                    responses[i[0]] = i[1]
                c.privmsg(e.source(),"Now I'm back responding to: %s" % responses.keys())
                self.responses = responses
                self.saveResponses()
        return