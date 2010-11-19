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
    
    def __init__(self, nickname, realname, channel, server, port=6667):
        SingleServerIRCBot.__init__(self, [(server, port)], nickname, realname)
        self.channel = channel
    
    def setResponses(self,responses):
        self.responses = responses
    
    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")
    
    def on_welcome(self, c, e):
        c.join(self.channel)
        c.notice(self.channel,"moschlar Hallo Papa!")
    
    def on_pubmsg(self, c, e):
        
        print e.eventtype()
        print e.source()
        print e.target()
        print e.arguments()
        
        a = e.arguments()[0]
        
        for r in self.responses:
            if a.find(r[0]) != -1:
                c.notice(self.channel,r[1])
        
        b = a.split(":", 1)
        if len(b) > 1 and irc_lower(b[0]) == irc_lower(self.connection.get_nickname()):
            print("Whoopie, someones talking to me....")
            c.notice(self.channel,"Cookies?")
            #self.do_command(e, a[1].strip())
        return
    
def main():
    
    # Parsing the bot's configuration
    
    from ConfigParser import SafeConfigParser
    import codecs
    
    config = SafeConfigParser()
    config.read(CONFIG_FILE)
    #with codecs.open(CONFIG_FILE, "r", encoding="utf-8") as f:
    #    config.readfp(f)
    
    nickname = config.get("global", "nickname")
    realname = config.get("global", "realname")
    server_list = config.get("global", "server_list").split(",")
    channel = config.get("global", "channel")
    print("I'm %s (%s) at %s" %(nickname, realname, server_list))
    
    responses = config.items("responses")
    #responses = {}
    #for i in config.items("responses"):
    #    responses[i[0]] = i[1]
    print("I respond to: %s" % responses)
    
    testbot = TestBot(nickname, realname, channel, server_list[0])
    testbot.setResponses(responses)
    testbot.start()
    
    return

if __name__ == "__main__":
    main()