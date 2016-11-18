import sys
import re
import os
import os.path
import argparse
import socket
import json
import urllib2
import time
import threading
from slacker import Slacker

'''
    Watchdog dropping a notification to Slack once the handin server is 
    no longer reachable.

'''
class Notifier(object):
    def __init__(self, posturl):
        '''
            posturl: URL to send message in JSON format to (Slack Webhook)
        '''
        self.posturl = posturl
        
    def _notify(self, text):
        ''' Sends the specified text to the Slack channel, specified by self.posturl '''
        req = urllib2.Request(self.posturl)
        req.add_header('Content-Type', 'application/json')
        urllib2.urlopen(req, json.dumps({"text" : text}))

    def notifyDown(self):
        ''' Notifies the channel that the server is unreachable '''
        self._notify("@channel: Handin-server unerachable!")

    def notifyUp(self):
        ''' Notifies the channel that the server is back up '''
        self._notify("Server back up. Thank you! :)")

class Prober(object):
    def __init__(self, ip, port):
        ''' 
            ip: IP or hostname where the handin server is running
            port: port on which the handin server is listening
        '''
        self.ip = ip
        self.port = port

    def probe(self):
        ''' Checks, whether a connection to the handin server could be established. '''
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        status = s.connect_ex((args.ip, args.port))
        s.close()
        return status == 0

class Watchdog(object):
    '''
        Watches the server and notifies Slack if needed.
        Basically a state machine with two states:
            - watching and notifying
            - just watching
    '''
    def __init__(self, prober, notifier, interval):
        self.prober = prober
        self.notifier = notifier
        self.interval = interval
        self.running = False
        self.action = self._watchAndNotify

    def watch(self):
        ''' 
            Starts watching the server in an interval specified in the constructor.
            Encountering connection problems will post a notification to Slack once.
            The Watchdog will continue to try connecting to the server.
            Once the connection is successfully re-established he will resume his work.
        '''
        self.running = True
        while self.running:
            self.action()
            time.sleep(self.interval)

    def _watchAndNotify(self):
        '''
            In this state the Watchdog will post a notification to Slack once he encounters
            connectivity issues and switch to _waitForReset.
        '''
        if not self.prober.probe():
            self.action = self._waitForReset
            self.notifier.notifyDown()


    def _waitForReset(self):
        '''
           In this state the Watchdog will continue to monitor the server but won't post
           any notifications. He will switch back to _watchAndNotify as soon as a connection
           can be established again.
        '''
        if self.prober.probe():
            self.action = self._watchAndNotify
            self.notifier.notifyUp()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Watchdog for the Info1 Handinserver.")
    parser.add_argument("--ip", default="dbworld.informatik.uni-tuebingen.de", help="IP or hostname of the server.")
    parser.add_argument("--port", type=int, default=7979, help="port for the server.")
    parser.add_argument("--probeinterval", type=float, default=10, help="interval in seconds in which the server is checked.")
    parser.add_argument("--posturl", default="https://hooks.slack.com/services/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", help="URL to which the notifications are sent (Slack Webhook).")
    args = parser.parse_args()

    watchdog = Watchdog(Prober(args.ip, args.port), Notifier(args.posturl), args.probeinterval)
    watchdog.watch()

