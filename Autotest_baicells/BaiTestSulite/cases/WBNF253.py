'''
    test case no: mBS1105_DD_031.4
    test setup: MMEPOOL open;
                96UE switch
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
        self.imsilist = GetConfig.get_imsilist(self.ueargs)
        self.logger.info("imsilist is %s" % self.imsilist)
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
        self.logger.info("cpe web set enable https")
        self.cpeiplist=["109.10.10.7"]
        for cpeip in self.cpeiplist:
            cpe = LmtSeting("http://%s" % cpeip)
            cpe.login_cpe()
            cpe.cpe_webenable_setting()
            cpe.tear_down()          

    def _dotest(self):
        self.logger.info("login cpe by cellip and port")
        for port in self.imsilist:
            url = "https://%s:5%s" %(self.args["chost"],port[-4:])
            cpe = LmtSeting(url)
            cpe.login_cpe()
            cpe.tear_down()
        return True
    
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
            self.logger.error("mBS1105_DD_031.4 is test Fail")
            return "Fail"
        else:
            self.logger.info("mBS1105_DD_031.4 is test Pass")
            return "Pass"
        
        
        
        
    
                                  
        
        


        


	     

