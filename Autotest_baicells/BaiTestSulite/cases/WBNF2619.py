'''
    test case no: WB.NF.26.19
    test setup: MMEPOOL open;
                cell active,mme connect
                SA2,SSP7 20M NAT
'''
import os
import logging
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
        self.ipecips = GetConfig.get_config("MMEPOOL","IPSECIP")
        self.logger.info("mmeips is %s" % self.mmeips)
        test = LmtSeting("http://%s" %self.args["chost"])
        test.login_lmt()
        test.mmepool_enable_setting(ipseclist,mmelist,qslist[0])
        test.lgw_setting(["1","NAT"])
        test.linkkeepalive_setting("1","1")
        test.do_reboot()
        test.tear_down()

    def _dotest(self):
        self.logger.info("check ue&cell status")
        test = LmtCheck("http://%s" % self.args["chost"])
        test.login_lmt()
        cellstatus = test.check_cell_state("Active")
        if not cellstatus:
            test.tear_down()
            return False
        mmestatus = test.check_mme_state("2")
        if not mmestatus:
            test.tear_down()
            return False
        test.tear_down()
        test.sleep(30)
        job = TestPerformance()
        self.logger.info("start ping test backroud")
        job.cpe_ping_background(["192.168.9.79"])
        time.sleep(90)
        uenum_ping = job.cpe_ping_pass_num()
        if uenum_ping != "1":
            return False
        self.logger.info("get UE Connections's mme")
        imsimme = job.check_ue_connect_mme(self.imsilist,self.mmeips)
        self.logger.info("down cell net")
        status = job.set_cell_eth_down(self.self.args["chost"])
        if status:
            self.logger.info("cell down sucessfull")
        else:
            self.logger.error("cell down faild")
        time.sleep(360)
        self.logger.info("cell net start")
        self.logger.info("check ue&cell status")
        test = LmtCheck("http://%s" % self.args["chost"])
        test.login_lmt()
        cellstatus = test.check_cell_state("Active")
        if not cellstatus:
            test.tear_down()
            return False
        mmestatus = test.check_mme_state("2")
        if not mmestatus:
            test.tear_down()
            return False
        test.tear_down()
        uenum_ping = job.cpe_ping_pass_num()
        if uenum_ping != "1":
            return False
        self.logger.info("get UE Connections's mme")
        imsimme1 = job.check_ue_connect_mme(self.imsilist,self.mmeips)
        self.logger.info("stop ping")
        job.Signal.put("STOP") 
        if imsimme1 == imsimme:
            self.logger.info("UE Connections's mme is same as before")
            return True
        else:
            self.logger.error("UE Connections's mme is not same as before")
            return False
        
        
    def _runtest(self):
        self._setup()
        times = 1
        failtime = 0
        self._dotest()
        for i in range(times):
            self.logger.info("The No. %s test start" % i)
            status = self._dotest()
            if status:
                self.logger.info("The No. %s test pass" % i)
            else:
                self.logger.info("The No. %s test fail" % i)
                failtime +=1
        if failtime > 0:
            self.logger.error("WB.NF.26.19 is test Fail")
            return "Fail"
        else:
            self.logger.info("WB.NF.26.19 is test Pass")
            return "Pass"
        
        
        
        
    
                                  
        
        


        


	     

