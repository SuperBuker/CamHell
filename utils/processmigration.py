from multiprocessing import Process
import model
from processmodel import Protocam
import sys

class DBMig(Process):
    threadID = 0
    threadName = "DBMig"
    feedingQueue = None

    def __init__(self, tID, q):
        Process.__init__(self)
        self.threadID = tID
        self.feedingQueue = q

    def run(self):
        self.myprint('Thread starting')
        myaddr = model.Address.select()
        print('Results: found %s cameras in DB' % (len(myaddr)))

        if len(myaddr) != 0:
            for addr in myaddr:
                protocam = Protocam.fromAddr(addr)
                if protocam is not None:
                    self.feedingQueue.put(protocam)
        self.myprint('Process terminated')

    def myprint(self, string):
        print('[%s-%s] %s' % (self.threadName, self.threadID, string))
        sys.stdout.flush()
