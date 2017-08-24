'''
    test case no: WB.NF.72.6.1
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
        self.logger.info("add route for lgw")
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
        test.lgw_setting(["1","Bridge"])
        test.do_reboot()
        test.tear_down()


    def _dotest(self):
        test.tear_down()
        test.login_lmt()
        test.check_cell_state("Active")
        test.check_mme_state("2")
        uenum = test.ue_count_check()
        test.tear_down()
        if uenum < 32:
            self.logger.info("There is some ue is unconnect,now uecounts is %s" % unnum)
            return False
        job = TestPerformance()
        result = job.uepingtest(self.ftpiplist)
        if result:
            self.logger.info("ftp ping is pass")
        else:
            self.logger.info("ping ftp fail")
            return False
        self.logger.info("get ue ip mac list")
        test = LmtCheck("http://192.168.9.42")
        test.login_lmt()
        maclist = test.get_ue_imsimac_list()
        iplist = test.get_ue_get_ue_imsi_list()
        test.tear_down()
        self.logger.info(maclist)
        self.logger.info(iplist)
        self.logger.info("Check ip and mac in syslog")
        for imsi in self.imsilist:
            ip = iplist[imsi]
            mac = maclist[imsi]
            mac = ":".join(mac[i:i+2] for i in range(0,len(mac),2))
            check = job.check_ip_mac_insyslog(self.args["chost"],ip,mac)
            if not check:
                self.logger.error("There is no %s and %s in syslog" %(ip,mac))
                return False
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
            self.logger.error("WB.NF.72.6.1 is test Fail")
            return "Fail"
        else:
            self.logger.info("WB.NF.72.6.1 is test Pass")
            return "Pass"
        
        
        
        
    
                                  
        
        


        


	     

