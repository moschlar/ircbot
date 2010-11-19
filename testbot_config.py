# -*- coding: utf-8 -*-

SERVER = '134.93.63.201'
CHANNEL = '#spielplatz'

NICKNAME = 'testbot'
REALNAME = 'Test Bot'

RESPONSES = {'döner':'Du bekomme Döner? - Mit Swiebel, Knoblauchsoße und scharf?',
             'umlaute':'Umlaute? Du willst Umlaute? Geh doch nach China und kauf dir welche! Hier gibt es keine Umlaute!'}


class config():
    def __init__(self):
        self.server = SERVER
        self.channel = CHANNEL
        self.nickname = NICKNAME
        self.realname = REALNAME
        self.responses = RESPONSES

    def get_server(self):
        return self.__server


    def get_channel(self):
        return self.__channel


    def get_nickname(self):
        return self.__nickname


    def get_realname(self):
        return self.__realname


    def get_responses(self):
        return self.__responses

    server = property(get_server, None, None, None)
    channel = property(get_channel, None, None, None)
    nickname = property(get_nickname, None, None, None)
    realname = property(get_realname, None, None, None)
    responses = property(get_responses, None, None, None)
    
