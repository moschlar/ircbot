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
HELLO_MESSAGE = "Hi!"

import socket

from ircbot import SingleServerIRCBot
from irclib import nm_to_n, nm_to_h, irc_lower, ip_numstr_to_quad, ip_quad_to_numstr, is_channel

import dbstuff

class TestBot(SingleServerIRCBot):
    
    def __init__(self, server, password, nickname, realname, channel_list):
        # Check if server:port or only server is given
        if server.rfind(":") == -1:
            port = 6667
        else:
            port = int(server.rsplit(":",1)[-1])
            server = server.rsplit(":",1)[0]
        
        # Initialization
        SingleServerIRCBot.__init__(self, [(server, port)], nickname, realname)
        self.password = password
        self.levels = {}
        
        self.channel_list = channel_list
        self.main_channel = channel_list[0]
        
        self.ghostwriters = []
        self.loadResponses()
    
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
    
    # Not sure what to do here... 
    # Better restart the whole IRC server to get my name again! :D
    def on_nicknameinuse(self, c, e):
        """
        Callback function on logging in with already used nickname
        """
        print("What the hell is going on here? Who is claiming my name???")
        c.nick(c.get_nickname() + "_")
    
    def on_welcome(self, c, e):
        """
        Callback function on getting welcome message from server
        
        Lets get oper rights!
        Joining channels and saying Hello
        """
        
        if self.password:
            c.oper(self.nickname,self.password)
        
        for chan in self.channel_list:
            c.join(chan)
        if HELLO_MESSAGE:
            c.privmsg(self.main_channel, HELLO_MESSAGE)
    
    def on_pubmsg(self, c, e):
        """
        Callback function for public messages.
        """
        a = e.arguments()[0]
        
        # Did someone mention my name?
        if a.find(irc_lower(self.connection.get_nickname())) != -1:
            #print("Whoopie, someones talking to me....")
            c.privmsg(e.target(),"Wat is los?")
        
        if a.startswith("calc "):
            self.doMath(c, e, a.split(None,1)[1])
            
        # Did someone say something interesting to respond to?
        for (keyword,response) in self.responses.items():
            if irc_lower(a).find(irc_lower(keyword)) != -1:
                print("Found %s" % keyword)
                c.privmsg(e.target(), response)
        
        return
    
    def on_privmsg(self, c, e):
        """
        Callback function for private messages
        """
        a = e.arguments()[0]
        
        cmd = a.split()
        
        # Now what to do?
        if cmd[0] == "debugme":
            self.debugMe(c,e)
            
        elif cmd[0] == "update":
            for chan in self.channel_list:
                c.who(chan)
                
        elif cmd[0] == "help":
            c.privmsg(e.source(),"Help is on its way!")
            self.help(c,e)
            
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
        elif (cmd[0] == "modetest"):
            self.userModes(c,e)
        return
    
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
    
    def doMath(self,c,e,expr):
        import urllib
        url = "http://www.wolframalpha.com/input/?i=%s" % urllib.quote(expr)
        c.privmsg(e.target(),"I'm not that good at maths... Try it here: %s" % url)
        return
    
    def help(self,c,e):
        """
        Display help message
        """
        c.privmsg(e.source(),"Commands:")
        c.privmsg(e.source(),"(<> indicate parameters, [] are optional parameters, * commands require op rights)")
        c.privmsg(e.source(),"help: Displays this help text")
        c.privmsg(e.source(),"update: Update user modes from database now")
        c.privmsg(e.source(),"say [channel] <something>: Makes the bot say <something> in channel or its main channel %s" % self.main_channel)
        c.privmsg(e.source(),"exorcism [n]: Displays the last n (or MAX_GHOSTS=%d) invokations of \"say\"" % MAX_GHOSTS)
        c.privmsg(e.source(),"response list: Lists all available response keywords")
        c.privmsg(e.source(),"response set <keyword> <response>: Sets the response for <keyword> to <response> (overwrites already set keywords)")
        c.privmsg(e.source(),"*response del <keyword>: Deletes response entry for <keyword>")
        c.privmsg(e.source(),"*response init: Re-initializes the response dictionary with default values from config file")
        return
    
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
                c.privmsg(e.source(),"%s gelöscht" % params[0])
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
        
        if nick == c.get_nickname():
            self.levels[channel] = dbstuff.getChannelLevels(channel)
            print("levels: In %s we have %s" % (channel,self.levels[channel]))
        else:
            c.privmsg(channel,"Hello %s" % nick)
            level = dbstuff.getLevel(channel,host)
            print("level: %s on %s in %s has %s" % (nick, host, channel, level))
    
    # We use the PING command as a hook to get the new who list from the server
    # and to check whether all user's modes are set correctly
    # Because whoreply gets called multiple times, we get the dictionary of
    # modes from the database in this step and store it
    def on_ping(self,c,e):
        
        for channel in self.channel_list:
            self.levels[channel] = dbstuff.getChannelLevels(channel)
            print("levels: In %s we have %s" % (channel,self.levels[channel]))
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
        ip = socket.gethostbyname(host)
        
        #levels = dbstuff.getChannelLevels(channel)
        if self.levels[channel].has_key(nick):
            level = self.levels[channel][nick]
        else:
            level = "n"
            #return
        
        print("whoreply with %s %s (%s) in %s has %s" % (nick, host, ip, channel, level))
    
    def debugMe(self,c,e):
        """
        Prints out debugging information about the bots state and its channels
        """
        
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
        
        Keeps MAX_GHOSTS entries as history of ghostwriters.
        """
        if len(self.ghostwriters) >= MAX_GHOSTS:
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
    
    # Parsing the bot's configuration
    from ConfigParser import SafeConfigParser
    config = SafeConfigParser()
    config.read(CONFIG_FILE)
    
    server = config.get("global", "server")
    password = config.get("global","password")
    nickname = config.get("global", "nickname")
    realname = config.get("global", "realname")
    channel_list = config.get("global", "channel_list").split(",")
    print("I'm %s (%s) at %s in %s" %(nickname, realname, server, channel_list))
    
    testbot = TestBot(server, password, nickname, realname, channel_list)
    testbot.start()
    
    return

if __name__ == "__main__":
    main()