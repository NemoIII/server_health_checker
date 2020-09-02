from datetime import datetime
from acquisition import  ServerCheck, TimeStampCheck, PingCheck
from configuration import settings
from processor import RawReportProcessor
from report import CreateReport
from sender import Notification
import sys

if __name__ == "__main__":
    PingCheck().check()
    print("Ping... checked...", datetime.now().strftime("%d-%m-%Y %H:%M:%S"))
    ServerCheck().check()
    print("Server... checked...", datetime.now().strftime("%d-%m-%Y %H:%M:%S"))
    TimeStampCheck().check()
    print("TimeStamp... checked...", datetime.now().strftime("%d-%m-%Y %H:%M:%S"))
    RawReportProcessor().colect_info()
    print("Colect Info... checked...", datetime.now().strftime("%d-%m-%Y %H:%M:%S"))
    #if "-g" in sys.argv:
    #    RawReportProcessor().graphic_generate()
    RawReportProcessor().server_health_report()
    print("Health Report... checked...", datetime.now().strftime("%d-%m-%Y %H:%M:%S"))
    CreateReport().colect_report()
    print("Colect Report checked...", datetime.now().strftime("%d-%m-%Y %H:%M:%S"))
    Notification().notify_user()
    print("All services checked. Time:", datetime.now().strftime("%d-%m-%Y %H:%M:%S"))
