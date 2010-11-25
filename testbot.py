#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Testing python-irclib as a bot

This is an example bot that uses the SingleServerIRCBot class from
ircbot.py.

@version: beta 0.1
@author: moschlar
"""

CONFIG_FILE = "testbot.cfg"

from socket import gethostbyname

from ConfigParser import SafeConfigParser
from ircbot import SingleServerIRCBot
from irclib import nm_to_n, nm_to_h, is_channel

import dbstuff, responder

class TestBot(SingleServerIRCBot):
    
    def __init__(self):
        
        # Parsing the bot's configuration
        
        config = SafeConfigParser()
        config.read(CONFIG_FILE)
        
        server = config.get("global", "server")
        login = config.get("global","login")
        password = config.get("global","password")
        nickname = config.get("global", "nickname")
        realname = config.get("global", "realname")
        channel_list = config.get("global", "channel_list").split(",")
        print("I'm %s (%s) at %s in %s" %(nickname, realname, server, channel_list))
        
        self.max_ghosts = config.get("global","maximum ghosts")
        self.hello_message = config.get("global","hello message")
        
        # Check if server:port or only server is given
        if server.rfind(":") == -1:
            port = 6667
        else:
            port = int(server.rsplit(":",1)[-1])
            server = server.rsplit(":",1)[0]
        
        # Initialization
        SingleServerIRCBot.__init__(self, [(server, port)], nickname, realname)
        self.login = login
        self.password = password
        self.levels = {}
        
        self.channel_list = channel_list
        self.main_channel = channel_list[0]
        
        self.ghostwriters = []
        
        self.responder = responder.Responder()
    
    def on_nicknameinuse(self, c, e):
        """
        Callback function on using an already used nickname
        
        e.source() = server
        e.arguments() = [nickname, message]
        """
        
        print("What the hell is going on here? Who is claiming my name???")
        c.send_raw("KILL %s :Klau nicht meinen Nick" % e.arguments()[0])
        c.nick(e.arguments()[0])
    
    def on_welcome(self, c, e):
        """
        Callback function on getting welcome message from server
        
        Lets get oper rights!
        Joining channels and saying Hello
        """
        
        if self.login and self.password:
            c.oper(self.login,self.password)
        
        for chan in self.channel_list:
            c.join(chan)
            c.who(chan)
        if self.hello_message:
            c.privmsg(self.main_channel, self.hello_message)
    
    def on_pubmsg(self, c, e):
        """
        Callback function for public messages.
        """
        a = e.arguments()[0]
        
        # Did someone mention my name?
        if a.lower().find(self.connection.get_nickname().lower()) != -1:
            #print("Whoopie, someones talking to me....")
            c.privmsg(e.target(),"Wat is los?")
        
        if a.lower().startswith("calc "):
            self.doMath(c, e, a.split(None,1)[1])
            
        # Did someone say something interesting to respond to?
        self.responder.respondTo(c, e, a)
        return
    
    def on_privmsg(self, c, e):
        """
        Callback function for private messages
        """
        a = e.arguments()[0]
        
        cmd = a.split()
        
        # Now what to do?
        if cmd[0].lower() == "debugme":
            self.debugMe(c,e)
            
        elif cmd[0].lower() == "update":
            for chan in self.channel_list:
                c.who(chan)
                
        elif cmd[0].lower() == "help":
            c.privmsg(e.source(),"Help is on its way!")
            self.help(c,e)
            
        elif cmd[0].lower() == "exorcism":
            try:
                n = int(cmd[1])
                self.exorcism(c, e, n)
            except:
                self.exorcism(c, e)
            
        elif (cmd[0].lower() == "say") and (len(cmd) > 1):
            self.sayByProxy(c, e, a.split(None,1)[-1])
            
        elif (cmd[0].lower() == "response") and (len(cmd) > 1):
            self.responder.doCommand(c,e,a.split(None,1)[-1])
            #self.response(c, e, a.split(None,1)[-1])
        return
    
    def doMath(self,c,e,expr):
        import urllib
        url = "http://www.wolframalpha.com/input/?i=%s" % urllib.quote(expr)
        c.privmsg(e.target(),"I'm not that good at maths... Try it here: %s" % url)
        return
    
    def help(self,c,e):
        """
        Display help message
        """
        c.privmsg(e.source(),"IRCBot Version 0.1 alpha")
        c.privmsg(e.source(),"Commands:")
        c.privmsg(e.source(),"(<> indicate parameters, [] are optional parameters, * commands require op rights)")
        c.privmsg(e.source(),"help: Displays this help text")
        c.privmsg(e.source(),"update: Update user modes from database now")
        c.privmsg(e.source(),"say [channel] <something>: Makes the bot say <something> in channel or its main channel %s" % self.main_channel)
        c.privmsg(e.source(),"exorcism [n]: Displays the last n (or max_ghosts=%d) invokations of \"say\"" % self.max_ghosts)
        c.privmsg(e.source(),"response list: Lists all available response keywords")
        c.privmsg(e.source(),"response set <keyword> <response>: Sets the response for <keyword> to <response> (overwrites already set keywords)")
        c.privmsg(e.source(),"*response del <keyword>: Deletes response entry for <keyword>")
        c.privmsg(e.source(),"*response init: Re-initializes the response dictionary with default values from config file")
        return
    
    
    # But here we should immediately check for the user's mode
    def on_join(self,c,e):
        """
        Handles the servers JOIN messages
        
        Here the bot eventually says Hello to a new user (not himself)
        
        And the bot queries the database for getting the highest mode for
        the new user and applies it
        """
        nick = nm_to_n(e.source())
        host = nm_to_h(e.source())
        channel = e.target()
        print nick
        print c.get_nickname()
        
        if nick != c.get_nickname():
            c.privmsg(channel,"Hello %s" % nick)
            level = dbstuff.getLevel(channel,host)
            print("level: %s on %s in %s has %s" % (nick, host, channel, level))
            if (level == "v") or (level == "o"):
                c.mode(channel,"+%s %s" % (level,nick))
    
    # We use the PING command as a hook to get the new who list from the server
    # and to check whether all user's modes are set correctly
    # Because whoreply gets called multiple times, we get the dictionary of
    # modes from the database in this step and store it
    def on_ping(self,c,e):
        
        for channel in self.channel_list:
            c.who(channel)
    
    # Now here needs to be checked if the rights are set correctly for each user
    def on_whoreply(self,c,e):
        """
        Handles the servers whoreplies
        
        We do the periodic check for for user modes here.
        
        e.source = <server>
        e.target = <nickname>
        e.arguments = [channel, ~nickname, host, server, nickname, H*, 0 realname]
        """
        
        channel = e.arguments()[0]
        nick = e.arguments()[4]
        host = e.arguments()[2]
        ip = gethostbyname(host)
        
        level = dbstuff.getLevel(channel,host)
        
        print("whoreply with %s %s (%s) in %s has %s" % (nick, host, ip, channel, level))
        
        if (level == "v") or (level == "o"):
            c.mode(channel,"+%s %s" % (level,nick))
    
    def debugMe(self,c,e):
        """
        Prints out debugging information about the bots state and its channels
        """
        # DebugMe can be used as manual hook to perform a WHO request
        for chan in self.channel_list:
            c.who(chan)
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
        
        Keeps max_ghosts entries as history of ghostwriters.
        """
        if len(self.ghostwriters) >= self.max_ghosts:
            self.ghostwriters = self.ghostwriters[1:]
        self.ghostwriters.append((nm_to_n(e.source()),msg))
        
        msgsplit = msg.split(None,1)
        if is_channel(msgsplit[0]) and len(msgsplit) > 1:
            chan = msgsplit[0]
            msg = msgsplit[1]
        else:
            chan = self.main_channel
        
        c.privmsg(chan,msg)
        return
    
    
def main():
    
    testbot = TestBot()
    testbot.start()
    
    return

if __name__ == "__main__":
    main()
