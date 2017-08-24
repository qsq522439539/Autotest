'''
    test case no: mBS1105_BP_001.4
    test setup: MMEPOOL open;
                96UE
                cell active,mme connect
                SA2,SSP7 20M NAT
'''
import os
import logging
import time
from common import *
from webset import *
from config import *

class DoTest():
    def __init__(self,args,ueargs):
        self.args = args
        self.ueargs = ueargs
        self.logger = logging.getLogger('test')
        self.logger.info("Args is %s" % self.args)
        self.logger.info("Ue args is %s" % self.ueargs)
    
    def _setup(self):
        '''
         Setup before starting test
        '''
        self.cpeiplist = GetConfig.get_cpeiplist(self.ueargs)
        self.logger.info("cpeiplist is %s " % self.cpeiplist)
        self.ftpiplist = GetConfig.get_ftpiplist(self.ueargs)
        self.logger.info("ftpiplist is %s" % self.ftpiplist)
        self.logger.info("mmepool enable setting")
        ipseclist = GetConfig.get_config("MMEPOOL","TWOTUNNEL")
        self.logger.info("ipseclist is %s" % ipseclist)
        mmelist = GetConfig.get_config("MMEPOOL","MMEPOOLIP")
        self.logger.info("mmelist is %s" % mmelist)
        qslist = GetConfig.get_config("MMEPOOL","QSMMEPOOL37")
        self.logger.info("qseting args is %s" % qslist)
        self.mmeerrorip = GetConfig.get_config("MMEPOOL","MMEERRORROUTE")
        self.mmeips = GetConfig.get_config("MMEPOOL","MMEIPS")
        self.logger.info("mmeips is %s" % self.mmeips)
        test = LmtSeting("http://%s" %self.args["chost"])
        test.login_lmt()
        test.mmepool_enable_setting(ipseclist,mmelist,qslist[0])
        test.lgw_setting(["1","NAT"])
        test.do_reboot()
        test.tear_down()

    def _dotest(self):
        job = TestPerformance()
        for i in range(3):
            self.logger.info("start %s cpe reboot" % i)
            result = job.rebootcpe(self.args["chost"],[self.cpeiplist[0]],password="Si8a&2vV9")
            if result:
                self.logger.info("cpe is reboot sucessfull")
            else:
                return False
                self.logger.error("some cpe is reboot fail")
        self.logger.info("start 48UE reboot")
        result = job.rebootcpe(self.args["chost"],[self.cpeiplist[0]],password="Si8a&2vV9")
        uenum = job.checkuenum(self.args["chost"])
        if uenum < 1:
            self.logger.error("some cpe is connected fail")
            return False
        else:
            self.logger.info("CPE connected pass")
        self.logger.info("CPE ping backhand")
        job.cpe_ping_background(self.cpeiplist[0])
        self.logger.info("start cell reboot")
        test = LmtCheck("http://%s" % self.args["chost"])
        test.login_lmt()
        test.do_reboot()
        test.tear_down()
        test = LmtCheck("http://%s" % self.args["chost"])
        test.login_lmt()
        test.check_cell_state("Active")
        test.check_mme_state("2")
        test.tear_down()
        time.sleep(60)
        cpepingpassnum = job.cpe_ping_pass_num()
        job.Signal.put("STOP")
        if cpepingpassnum == "1":
            return True
        else:
            return False
    
    def _runtest(self):
        self._setup()
        times = 1
        failtime = 0
        for i in range(times):
            self.logger.info("The No. %s test start" % i)
            status = self._dotest()
            if status:
                self.logger.info("The No. %s test pass" % i)
            else:
                self.logger.info("The No. %s test fail" % i)
                failtime +=1
        if failtime > 0:
            self.logger.error("mBS1105_BP_001.4 is test Fail")
            return "Fail"
        else:
            self.logger.info("mBS1105_BP_001.4 is test Pass")
            return "Pass"
        
        
        
        
    
                                  
        
        


        


	     

