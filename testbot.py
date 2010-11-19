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
        self.lastuser = "Nobody."
    
    def setResponses(self,responses):
        self.responses = responses
    
    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")
    
    def on_welcome(self, c, e):
        for chan in self.channel_list:
            c.join(chan)
        #c.privmsg(self.channel,"moschlar Hallo Papa!")
    
    def on_pubmsg(self, c, e):
        
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
        a = e.arguments()[0]
        
        cmd = a.split()
        
        # Now what to do?
        if cmd[0] == "help":
            c.privmsg(e.source(),"Help is on its way!")
            
            
        elif cmd[0] == "exorcism":
            c.privmsg(e.source(),self.lastuser)
            
        elif cmd[0] == "keywords":
            c.privmsg(e.source(),self.responses.keys())
            
        elif (cmd[0] == "say") and (len(cmd) > 1):
            if cmd[1].startswith("#"):
                chan = cmd[1]
            else:
                chan = self.channel
            self.lastuser = nm_to_n(e.source())
            c.privmsg(chan,a.split(None,2)[-1])
        
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
    
    # Make dictionary of responses
    responses = {}
    for i in config.items("responses"):
        responses[i[0]] = i[1]
    print("I respond to: %s" % responses)
    
    testbot = TestBot(server, nickname, realname, channel_list)
    testbot.setResponses(responses)
    testbot.start()
    
    return

if __name__ == "__main__":
    main()