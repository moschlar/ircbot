#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""This is an IRC bot with powerful administration and entertainment functions.

Configuration has to be in script_name.cfg (e.g. if this script is "testbot.py"
configuration has to be in "testbot.cfg").

This bot will try to become server operator, if username and password are specified.
It can use a database to get the modes for users depending on their hostnames 
and/or ip addresses.

It has a say_by_proxy command that lets you make the bot say your words like it were his own;
although he keeps track of those usages which you can see by do_exorcism.

The bot can also respond to everything/something someone said in the channels. This responding
options are outsourced to a Responder class, that gets imported (or not) and uses respond_to 
to handle responses.

This bot uses ircbot.py and irclib.py from python-irclib <http://python-irclib.sourceforge.net/>

Author: Moritz Schlarb <mail@moritz-schlarb.de>
"""

import sys
from os.path import exists, splitext
from socket import gethostbyname
from urllib import quote
#import logging # will use logging somewhere in the future...

from ConfigParser import SafeConfigParser
from ircbot import SingleServerIRCBot
from irclib import nm_to_n, nm_to_h, is_channel

import dbstuff, responder

DEBUG = 1
VERSION = "0.2 beta"

class TestBot(SingleServerIRCBot):
    
    def __init__(self):
        
        # Parsing the configuration
        config_file = splitext(sys.argv[0])[0] + ".cfg"
        if not exists(config_file):
            raise
        config = SafeConfigParser({'username': None, 'password': None, 'realname':'IRCBot','channel_list':'#public','max_ghosts':'10','hello_message':'Hi!'})
        config.read(config_file)
        
        server = config.get("global", "server")
        username = config.get("global","username")
        password = config.get("global","password")
        nickname = config.get("global", "nickname")
        realname = config.get("global", "realname")
        channel_list = config.get("global", "channel_list").split(",")
        if DEBUG: print("I'm %s (%s) at %s in %s" %(nickname, realname, server, channel_list))
        
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
        self.username = username
        self.password = password
        
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
        
        if DEBUG: print("What the hell is going on here? Who is claiming my name???")
        c.send_raw("KILL %s :Klau nicht meinen Nick" % e.arguments()[0])
        c.nick(e.arguments()[0])
    
    def on_welcome(self, c, e):
        """
        Callback function on getting welcome message from server
        
        If username and password were given we authenticate here and get op rights
        Joining configured channels
        """
        
        if self.username and self.password:
            c.oper(self.username,self.password)
        
        for chan in self.channel_list:
            c.join(chan)
            # WHO request initiates user level checking
            c.who(chan)
            if self.hello_message:
                c.privmsg(chan, self.hello_message)
    
    def on_pubmsg(self, c, e):
        """
        Callback function for public messages.
        """
        # Just to make the next functions easier
        line = e.arguments()[0]
        
        # Did someone mention my name?
        if line.lower().find(self.connection.get_nickname().lower()) != -1:
            if DEBUG: print("Whoopie, someone said my name!!!")
            c.privmsg(e.target(),"Wie kann ich dienen?")
        
        # Shall I do some maths?
        if line.lower().startswith("calc "):
            self.do_math(c, e, line.split(None,1)[1])
        
        # Did someone say something interesting to respond to?
        self.responder.respond_to(c, e, line)
        return
    
    def on_privmsg(self, c, e):
        """
        Callback function for private messages
        """
        
        line = e.arguments()[0]
        cmd = line.split()
        
        if cmd[0].lower() == "debugme":
            self.debug_me(c,e)
            
        elif cmd[0].lower() == "update":
            for chan in self.channel_list:
                c.who(chan)
            
        elif cmd[0].lower() == "help":
            c.privmsg(e.source(),"Help is on its way!")
            self.help(c,e)
            
        elif cmd[0].lower() == "exorcism":
            try:
                n = int(cmd[1])
                self.do_exorcism(c, e, n)
            except:
                self.do_exorcism(c, e)
            
        elif (cmd[0].lower() == "say") and (len(cmd) > 1):
            self.say_by_proxy(c, e, line.split(None,1)[-1])
            
        elif (cmd[0].lower() == "response") and (len(cmd) > 1):
            self.responder.do_command(c,e,line.split(None,1)[-1])
            
        return
    
    def do_math(self,c,e,expr):
        """
        Just generate a link to Wolfram Alpha containing the given expression
        """
        url = "http://www.wolframalpha.com/input/?i=%s" % quote(expr)
        c.privmsg(e.target(),"I'm not that good at maths... Try it here: %s" % url)
        return
    
    def help(self,c,e):
        """
        Display help message
        
        Shall be generated dynamically by checking all the functions somewhere in the future...
        """
        c.privmsg(e.source(),"IRCBot Version %s" % VERSION)
        c.privmsg(e.source(),"Commands:")
        c.privmsg(e.source(),"(<> indicate parameters, [] are optional parameters, * commands require op rights)")
        c.privmsg(e.source(),"help: Displays this help text")
        c.privmsg(e.source(),"update: Update user modes from database now")
        c.privmsg(e.source(),"say [channel] <something>: Makes the bot say <something> in channel or its main channel %s" % self.main_channel)
        c.privmsg(e.source(),"do_exorcism [n]: Displays the last n (or max_ghosts=%d) invokations of \"say\"" % self.max_ghosts)
        c.privmsg(e.source(),"response list: Lists all available response keywords")
        c.privmsg(e.source(),"response set <keyword> <response>: Sets the response for <keyword> to <response> (overwrites already set keywords)")
        c.privmsg(e.source(),"*response del <keyword>: Deletes response entry for <keyword>")
        c.privmsg(e.source(),"*response init: Re-initializes the response dictionary with default values from config file")
        return
    
    def on_join(self,c,e):
        """
        Handles the servers JOIN messages
        
        Here the bot eventually welcomes a new user (but not to himself)
        
        And the bot queries the database for getting the highest mode for
        the new user and applies it
        """
        nick = nm_to_n(e.source())
        host = nm_to_h(e.source())
        channel = e.target()
        if DEBUG: print nick + " joined"
        
        if nick != c.get_nickname():
            c.privmsg(channel,"Hello %s" % nick)
            level = dbstuff.getLevel(channel,host)
            if DEBUG: print("level: %s on %s in %s has %s" % (nick, host, channel, level))
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
    
    def debug_me(self,c,e):
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
    
    def do_exorcism(self,c,e,*n):
        """
        Writes a list of the history of ghostwriters that used say_by_proxy
        """
        if (not n) or (n[0] > len(self.ghostwriters)):
            n = len(self.ghostwriters)
        else:
            n = n[0]
        
        for (who,what) in self.ghostwriters[:n]:
            c.privmsg(e.source(),"%s said %s" % (who,what))
        return
    
    def say_by_proxy(self,c,e,msg):
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
