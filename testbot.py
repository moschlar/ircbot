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
        for r in self.responses.keys():
            if irc_lower(a).find(irc_lower(r)) != -1:
                print("Found %s" % r)
                c.privmsg(e.target(),self.responses.get(r))
        
        return
    
    def on_privmsg(self, c, e):
        """
        Handles private messages
        """
        a = e.arguments()[0]
        
        cmd = a.split()
        
        # Now what to do?
        if cmd[0] == "help":
            c.privmsg(e.source(),"Help is on its way!")
            
            
        elif cmd[0] == "exorcism":
            try:
                n = int(cmd[1])
                self.exorcism(c, e, n)
            except:
                self.exorcism(c, e)
            
        elif cmd[0] == "keywords":
            c.privmsg(e.source(),self.responses.keys())
            
        elif (cmd[0] == "say") and (len(cmd) > 1):
            self.sayByProxy(c, e, a.split(None,1)[-1])
            
        elif (cmd[0] == "response") and (len(cmd) > 1):
            if cmd[1] == "list":
                c.privmsg(e.source(),self.responses.keys())
            elif cmd[1] == "set" and len(cmd) > 3:
                self.responses[cmd[2]] = cmd[3]
                c.privmsg(e.source(),"Set %s to %s" % (cmd[2],cmd[3]))
                self.saveResponses
            elif cmd[1] == "del" and len(cmd) > 2:
                if self.channels[self.channel].is_voiced(nm_to_n(e.source())):
                    c.privmsg(e.source(),"%s gelöscht" % cmd[2])
                    del(self.responses[cmd[2]])
                else:
                    c.privmsg(e.source(),"Nah, des geht nit!")
            
        return
    
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