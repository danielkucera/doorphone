#!/usr/bin/python
# $Id$
#
# SIP account and registration sample. In this sample, the program
# will block to wait until registration is complete
#
# Copyright (C) 2003-2008 Benny Prijono <benny@prijono.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
import sys
import ConfigParser
import pjsua as pj
import threading
import time

current_call = None
config = ConfigParser.ConfigParser()
config.readfp(open('doorphone.cfg'))

def log_cb(level, str, len):
    print str,
class MyAccountCallback(pj.AccountCallback):
    sem = None
    def __init__(self, account):
        pj.AccountCallback.__init__(self, account)
    def wait(self):
        self.sem = threading.Semaphore(0)
        self.sem.acquire()
    def on_reg_state(self):
        if self.sem:
            if self.account.info().reg_status >= 200:
                self.sem.release()
    # Notification on incoming call
    def on_incoming_call(self, call):
        global current_call
        if current_call:
            call.answer(486, "Busy")
            return
           
        print "Incoming call from ", call.info().remote_uri
        current_call = call
        call_cb = MyCallCallback(current_call)
        current_call.set_callback(call_cb)
        #current_call.answer(180)
        current_call.answer(200)
#        time.sleep(60)
#        current_call.hangup()
       
# Callback to receive events from Call
class MyCallCallback(pj.CallCallback):
    def __init__(self, call=None):
        pj.CallCallback.__init__(self, call)
    # Notification when call state has changed
    def on_state(self):
        global current_call
        print "Call with", self.call.info().remote_uri,
        print "is", self.call.info().state_text,
        print "last code =", self.call.info().last_code, 
        print "(" + self.call.info().last_reason + ")"
       
        if self.call.info().state == pj.CallState.DISCONNECTED:
            current_call = None
            print 'Current call is', current_call
    # Notification when call's media state has changed.
    def on_media_state(self):
        if self.call.info().media_state == pj.MediaState.ACTIVE:
            # Connect the call to sound device
            call_slot = self.call.info().conf_slot
            pj.Lib.instance().conf_connect(call_slot, 0)
            pj.Lib.instance().conf_connect(0, call_slot)
            print "Media is now active"
        else:
            print "Media is inactive"

    def on_dtmf_digit(self, digits):
        print "on_dtmf_digit (%s)",str(digits)

# Function to make call
def make_call(uri):
    try:
        print "Making call to", uri
        return acc.make_call(uri, cb=MyCallCallback())
    except pj.Error, e:
        print "Exception: " + str(e)
        return None
       

lib = pj.Lib()
try:
    media_cfg=pj.MediaConfig()
    #media_cfg.audio_frame_ptime = 20
    #media_cfg.ptime = 10
    #media_cfg.ec_tail_len = 0 #disable echo cancellation
    media_cfg.no_vad = True #disable VAD

    log_cfg = pj.LogConfig(level=config.getint("general", "loglevel"), callback=log_cb)

    lib.init(log_cfg = log_cfg, media_cfg=media_cfg)
    
#    lib.create_transport(pj.TransportType.TCP, pj.TransportConfig(5080))
    lib.create_transport(pj.TransportType.UDP, pj.TransportConfig(5080))
    lib.start()
    #acc = lib.create_account(pj.AccountConfig(config.get("account", "server"), config.get("account", "user"), config.get("account", "password"), "", "", "sip:"+config.get("account", "server")+"transport=tcp;hide"))
    acc = lib.create_account(pj.AccountConfig(config.get("account", "server"), config.get("account", "user"), config.get("account", "password")))

    acc_cb = MyAccountCallback(acc)
    acc.set_callback(acc_cb)
    acc_cb.wait()
    print "\n"
    print "Registration complete, status=", acc.info().reg_status, \
          "(" + acc.info().reg_reason + ")"
    while True:
        print "Menu:  m=make call, h=hangup call, a=answer call, q=quit"
        input = sys.stdin.readline().rstrip("\r\n")
        if input == "m":
            if current_call:
                print "Already have another call"
                continue
            print "Enter destination URI to call: ", 
            input = "sip:100@185.98.208.25"
            input = "sip:0903588936@185.98.208.25"
            if input == "":
                continue
            lck = lib.auto_lock()
            current_call = make_call(input)
            del lck
        elif input == "q":
            break

    lib.destroy()
    lib = None
except pj.Error, e:
    print "Exception: " + str(e)
    lib.destroy()
