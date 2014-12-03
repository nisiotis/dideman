# -*- coding: utf-8 -*-
from twisted.internet import reactor
from twisted.python import log
import sys, time, os
from twisted.internet.task import LoopingCall, deferLater
from subprocess import Popen, PIPE

 
iterVal = 0
asec = 30
f_path = '/home/user/Desktop/Vasilis/dideman/media/pdffiles'

orig_set = dict([(f, None) for f in os.listdir (f_path)])

def loopedFunction():
    global iterVal, orig_set
    iterVal = iterVal + 1
    now = time.localtime(time.time())
    timeStr = str(time.strftime("%y/%m/%d %H:%M:%S",now))
    print timeStr + " : iteration : " + str(iterVal)
    new_set = dict ([(f, None) for f in os.listdir (f_path)])
    added = [f for f in new_set if not f in orig_set]
    if added:
        print "New Files Added: %s" % added
        for f in added:
            if f[-4:] == '.pdf':
                p = Popen(['%s/reader' %f_path,'%s.csv' % f[:-4],'%s.pdf' % f[:-4]],  stdout=PIPE)
                output = p.communicate()[0]
                print output
    orig_set = new_set

now = time.localtime(time.time())
timeStr = str(time.strftime("%y/%m/%d %H:%M:%S",now))
print "will call loopedFunction, every %s second" % asec


loopObj = LoopingCall(loopedFunction)
loopObj.start(asec, now=True)
 
reactor.run()

