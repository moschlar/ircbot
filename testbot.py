#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Testing python-irclib as a bot
#

"""Testing python-irclib as a bot

This is an example bot that uses the SingleServerIRCBot class from
ircbot.py.

"""

CONFIG_FILE = "testbot.cfg"
RESPONSES_FILE = "responses.pkl"
MAX_GHOSTS = 10

from ircbot import SingleServerIRCBot
from irclib import nm_to_n, nm_to_h, irc_lower, ip_numstr_to_quad, ip_quad_to_numstr

class TestBot(SingleServerIRCBot):
    
    def __init__(self, server, nickname, realname, channel_list):
        if server.rfind(":") == -1:
            port = 6667
        else:
            port = int(server.rsplit(":",1)[-1])
        SingleServerIRCBot.__init__(self, [(server, port)], nickname, realname)
        self.channel_list = channel_list
        self.channel = channel_list[0]
        self.ghostwriters = [("Nobody","Nothing!")]
        self.loadResponses()
    
    def saveResponses(self):
        """
        Saves (pickles) responses to the file RESPONSES_FILE
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
    
    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")
    
    def on_welcome(self, c, e):
        """
        Handles server welcome
        """
        for chan in self.channel_list:
            c.join(chan)
        #c.privmsg(self.channel,"moschlar Hallo Papa!")
    
    def on_pubmsg(self, c, e):
        """
        Handles public messages.
        """
        a = e.arguments()[0]
        
        # Did someone mention my name?
        if a.find(irc_lower(self.connection.get_nickname())) != -1:
            #print("Whoopie, someones talking to me....")
            c.privmsg(e.target(),"Wat is los?")
        
        # Did someone say something interesting?
        for (keyword,response) in self.responses.items():
            if irc_lower(a).find(irc_lower(keyword)) != -1:
                print("Found %s" % keyword)
                c.privmsg(e.target(), response)
        
        return
    
    def on_privmsg(self, c, e):
        """
        Handles private messages
        """
        a = e.arguments()[0]
        
        cmd = a.split()
        
        # Now what to do?
        if cmd[0] == "debugme":
            self.debugMe(c,e)
            
        elif cmd[0] == "help":
            c.privmsg(e.source(),"Help is on its way!")
            
        elif cmd[0] == "exorcism":
            try:
                n = int(cmd[1])
                self.exorcism(c, e, n)
            except:
                self.exorcism(c, e)
            
        elif (cmd[0] == "say") and (len(cmd) > 1):
            self.sayByProxy(c, e, a.split(None,1)[-1])
            
        elif (cmd[0] == "response") and (len(cmd) > 1):
            self.response(c, e, a.split(None,1)[-1])
            
        return
    
    def response(self,c,e,action):
        cmd = action.split(None,1)[0]
        params = action.split(None,2)[1:]
        
        auth = False
        for chname,chobj in self.channels.items():
            auth = auth or nm_to_n(e.source()) in chobj.opers()
        print ("%s auth: %s" % (nm_to_n(e.source()), auth))
        
        if cmd == "list":
            c.privmsg(e.source(),self.responses.keys())
        elif cmd == "set" and len(params) == 2:
            self.responses[params[0]] = params[1]
            c.privmsg(e.source(),"Set %s to %s" % (params[0],params[1]))
            self.saveResponses()
        elif cmd == "del" and len(params) >= 1:
            # If we don't have the keyword or user is not auth, we must not try to do anything
            if params[0] in self.responses.keys() and auth:
                c.privmsg(e.source(),"%s gelöscht" % params[0])
                del(self.responses[params[0]])
                self.saveResponses()
            else:
                c.privmsg(e.source(), "Des geht nit!")
        elif cmd == "init":
            if auth:
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
    
    def debugMe(self,c,e):
        """
        Prints out debugging information about the bots state and its channels
        """
        print("self.channels.items(): %s" % self.channels.items())
        for chname, chobj in self.channels.items():
            print("chname: %s chobj: %s" % (chname, chobj))
            c.privmsg(e.source(), "--- Channel statistics ---")
            c.privmsg(e.source(), "Channel: " + chname)
            users = chobj.users()
            users.sort()
            c.privmsg(e.source(), "Users: " + ", ".join(users))
            opers = chobj.opers()
            opers.sort()
            c.privmsg(e.source(), "Opers: " + ", ".join(opers))
            voiced = chobj.voiced()
            voiced.sort()
            c.privmsg(e.source(), "Voiced: " + ", ".join(voiced))
    
    def exorcism(self,c,e,*n):
        """
        Writes a list of the history of ghostwriters that used sayByProxy
        """
        if (not n) or (n[0] > len(self.ghostwriters)):
            n = len(self.ghostwriters)
        else:
            n = n[0]
        
        for (who,what) in self.ghostwriters[:n]:
            c.privmsg(e.source(),"%s said %s" % (who,what))
        return
    
    def sayByProxy(self,c,e,msg):
        """
        Makes the bot say something as it were his own words
        
        Keeps MAX_GHOSTS entries as history of ghostwriters.
        """
        if len(self.ghostwriters) >= MAX_GHOSTS:
            self.ghostwriters = self.ghostwriters[1:]
        self.ghostwriters.append((nm_to_n(e.source()),msg))
        
        msgsplit = msg.split(None,1)
        if msg.startswith("#") and len(msgsplit) > 1:
            chan = msgsplit[0]
            msg = msgsplit[1]
        else:
            chan = self.channel
        
        c.privmsg(chan,msg)
        return
    
def main():
    
    # Parsing the bot's configuration
    from ConfigParser import SafeConfigParser
    config = SafeConfigParser()
    config.read(CONFIG_FILE)
    
    nickname = config.get("global", "nickname")
    realname = config.get("global", "realname")
    server = config.get("global", "server")
    channel_list = config.get("global", "channel_list").split(",")
    print("I'm %s (%s) at %s%s" %(nickname, realname, server, channel_list))
    
    testbot = TestBot(server, nickname, realname, channel_list)
    testbot.start()
    
    return

if __name__ == "__main__":
    main()