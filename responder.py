#! /usr/bin/env python
# -*- coding: utf-8 -*-
'''
This class provides reponding functionality for ircbot.

Not yet finished!
To dirty, this whole stuff!

@author: moschlar
@version: 0.1 alpha
'''

import pickle
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
        self.load_responses()
        return
    
    def save_responses(self):
        """
        Saves pickled responses to the file RESPONSES_FILE
        """
        storage = file(RESPONSES_FILE, "wb")
        pickle.dump(self.responses,storage,protocol=pickle.HIGHEST_PROTOCOL)
        storage.close()
        return
    
    def load_responses(self):
        """
        Loads pickled responses from the file RESPONSES_FILE
        """
        storage = file(RESPONSES_FILE, "rb")
        self.responses = pickle.load(storage)
        storage.close()
        return
    
    def respond_to(self,line):
        for (keyword,response) in self.responses.items():
            if line.lower().find(keyword.lower()) != -1:
                print("Found %s" % keyword)
                return response
        
    
    def do_command(self,c,e,a):
        pass

    def get_auth(self,c,e,nick):
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
        
        authOp = self.get_auth(c, e, e.source()) == "o"
        
        if cmd == "list":
            c.privmsg(e.source(),self.responses.keys())
        elif cmd == "set" and len(params) == 2:
            self.responses[params[0]] = params[1]
            c.privmsg(e.source(),"Set %s to %s" % (params[0],params[1]))
            self.save_responses()
        elif cmd == "del" and len(params) >= 1:
            # If we don't have the keyword or user is not auth, we must not try to do anything
            if params[0] in self.responses.keys() and authOp:
                c.privmsg(e.source(),"%s gel�scht" % params[0])
                del(self.responses[params[0]])
                self.save_responses()
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
                self.save_responses()
        return
