# *-*coding=utf-8*-*
'''
   Implementation test drive
'''
import os
import shutil
import sys
import logging
import time
from config import *
from parxls import *

sys.path.append(os.path.abspath('cases'))

class TestDrive(ParXls):
    def _get_args(self):
        self.ftpargs = GetConfig.specific_elements('comonlabel', 'args.xml')
        parxml= GetConfig()
        self.ueargs= parxml.get_xml_data('args.xml')
        self.testsuite = self._gettestlist()
        self.logger.info(self.testsuite)
         

    def _runtest(self,casename,resultindex):
        self.logger.info("%s case is start test" % casename)
        casenamenew = casename.split(".")
        casenamenew = "".join(casenamenew)
        job = __import__('%s' % casenamenew)
        try:
            runjob = job.DoTest(self.ftpargs,self.ueargs)
            result = runjob._runtest()
        except:
            result = "Fail"
        resultindex.append(result)
        self.logger.info(resultindex)
        self._write_xls(resultindex)

    def _Run(self):
        self._get_args()
        testlist = self.testsuite.keys()
        print testlist
        testlist.sort()
        for casename in testlist:
            self._runtest(casename,self.testsuite[casename])


def setloger():
    timenow = time.strftime('%Y_%m_%d_%H_%M_%S')
    logger = logging.getLogger('test')
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler('log/testlog_%s.txt'%timenow)
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)
    formatter = logging.Formatter('%(asctime)s - %(name)s -%(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)
    
if __name__ == "__main__":
    setloger()
    logger = logging.getLogger('test')
    logger.info("Test Start")
    Test = TestDrive()
    Test._Run()
