'''
    test case no: WB.PF.22.3
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
        qslist = GetConfig.get_config("MMEPOOL","QSCA223")
        self.logger.info("qseting args is %s" % qslist)
        self.mmeerrorip = GetConfig.get_config("MMEPOOL","MMEERRORROUTE")
        self.mmeips = GetConfig.get_config("MMEPOOL","MMEIPS")
        self.logger.info("mmeips is %s" % self.mmeips)
        test = LmtSeting("http://%s" %self.args["chost"])
        test.login_lmt()
        test.mmepool_enable_setting(ipseclist,mmelist,qslist[0])
        test.lgw_setting(["1","Bridge"])
        test.omc_setting("192.168.9.32:8080//smallcell/AcsService")
        test.do_reboot()
        test.tear_down()

    def _dotest(self):
        self.logger.info("check ue&cell status")
        test = LmtCheck("http://%s" % self.args["chost"])
        test.login_lmt()
        cellstatus = test.check_cell_state("Active")
        if not cellstatus:
            self.logger.error("CELL is not active")
            test.tear_down()
            return False
        mmestatus = test.check_mme_state("2")
        if not mmestatus:
            test.tear_down()
            self.logger.error("MME is not connect by expeced")
            return False
        test.tear_down()
        job = TestPerformance()
        i = 0
        while i < 5:
            uenum = job.checkuenum(self.args["chost"])
            if uenum == "1":
                break
            else:
                time.sleep(30)
                i+=1
        if uenum != "1":
            self.logger.error("UE is atatch by expectd") 
            return False
        self.ftpiplist = GetConfig.get_ftpiplist(self.ueargs)
        result = job.uepingtest([self.ftpiplist[0]]) # one cpe
        if result:
            self.logger.info("ftp ping is pass")
        else:
            self.logger.error("ping ftp fail")
            return False
        # omc detach
        self.logger.info("omc set deact cell")
        omc=OmcSeting("http://192.168.9.71:6080/cloudcore/")
        omc.login_omc("iframeMain","autotest","abc123")
        omc.omc_atach_set("12020000511696P0530",False)
        omc.tear_down()
        test = LmtCheck("http://%s" % self.args["chost"])
        test.login_lmt()
        time.sleep(30)
        cellstatus = test.check_cell_state("Inactive")
        if not cellstatus:
            test.tear_down()
            self.logger.error("cell is active now,it is unexpectd")
            return False
        test.tear_down()
        self.logger.info("omc set deact cell sucessfull")
        # OMC atach
        time.sleep(30)
        self.logger.info("omc set act cell")
        omc=OmcSeting("http://192.168.9.71:6080/cloudcore/")
        omc.login_omc("iframeMain","autotest","abc123")
        omc.omc_atach_set("12020000511696P0530",True)
        omc.tear_down()
        test = LmtCheck("http://%s" % self.args["chost"])
        test.login_lmt()
        time.sleep(30)
        cellstatus = test.check_cell_state("Active")
        if not cellstatus:
            test.tear_down()
            self.logger.error("cell is Inactive, it is unexpectd")
            return False
        test.tear_down()
        i = 0
        while i < 5:
            uenum = job.checkuenum(self.args["chost"])
            if uenum == "1":
                break
            else:
                time.sleep(30)
                i+=1
        if uenum != "1":
            return False
        self.logger.info("UE count is %s now" % uenum)
        result = job.uepingtest([self.ftpiplist[0]]) # one cpe
        if result:
            self.logger.info("ftp ping is pass")
        else:
            self.logger.info("ping ftp fail")
            return False
        self.logger.info("omc set act cell sucessfull")
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
            self.logger.error("WB.PF.22.3 is test Fail")
            return "Fail"
        else:
            self.logger.info("WB.PF.22.3 is test Pass")
            return "Pass"

    def _tear_down(self,browser):
        browser._tear_down()
        
        
        
        
    
                                  
        
        


        


	     

