from datetime import datetime
from acquisition import  ServerCheck, TimeStampCheck, PingCheck
from configuration import settings
from processor import RawReportProcessor
from report import CreateReport
from sender import Notification, SMS_WhatsApp_Notification, SMS_Notification
import sys

if __name__ == "__main__":
    PingCheck().check()
    print("Ping")
    ServerCheck().check()
    print("Server")
    #TimeStampCheck().check()
    RawReportProcessor().colect_info()
    if "-g" in sys.argv:
        RawReportProcessor().graphic_generate()
        RawReportProcessor().server_health_report()
    CreateReport().colect_report()
    print("CreateReport")
    # Envia sms e mensagem pelo whatsapp pelo Twilio, precisa apenas configurar.
    # SMS_WhatsApp_Notification().sms_whatsapp_user()
    # Envia sms pela API do textbelt, mas precisa ser configurado com a conta já existente da empresa.
    # SMS_Notification().sms_user()
    # print("SMS")
    Notification().notify_user()
    print("All services checked. Time:", datetime.now().strftime("%d-%m-%Y %H:%M:%S"))
