from dispatcher import Dispatcher
from os.path import realpath, dirname, isfile
import json
from report import CreateReport
from datetime import datetime, timedelta
from configuration import settings
import pytz

"""
    Classe que gera relatorios cru, no casode a perda 'loss' esteja ruim

    - def: __init__
		:param: self
	- def colect_info
		:param: self
    - def: graphic_generate
        :param: self
    - def: server_health_report
        :param: self
"""

class RawReportProcessor:
    def __init__(self):
        self.reportRaw = {}
        
    def colect_info(self):
        # Dentro do processing_parameters é realidado a recepção dos dados vindos do acquisition.py e, de acordo com os teste aqui realiados, gerados relatórios e passados ao report.py, tudo feito com lambda.
        processing_parameters = [
        ("provider_ping", lambda info: Dispatcher().push("ping_error_report", {"failure": "Perda de Ping", "severity": "ALTA", "host": info["host"], "loss": info["loss"], "day": datetime.now()}) if info['loss'] > settings["loss_rate"] else None),
        ("provider_server_status", lambda info: Dispatcher().push("server_error_report", {"failure": "404, Client Error", "severity": "ALTA", "server": info["server"], "server_status": info["status"], "day": datetime.now()}) if info['server'] else None),
        ("provider_timestamp", lambda info: Dispatcher().push("provider_timestamp_report", {"id": info["id"], "name": info["name"], "last_message": info["last_message"], "day": datetime.now()}) if info['last_message'] < delay_time else None),
        ("provider_lastUpdate", lambda info: Dispatcher().push("provider_lastUpdate_report", {"state": info["state"], "GS": info["GS"], "GR": info["GR"], "OL": info["OL"], "OP": info["OP"], "GU": info["GU"], "GL": info["GL"], "day": datetime.now()}) if info['lastupdate_message'] < delay_time else None),
        ("provider_updateAt", lambda info: Dispatcher().push("provider_updateAt_report", {"id": info["id"], "name": info["name"], "base": info["base"], "updateAt": info["updateAt"],}) if info['updateAt'] < delay_time_updateAt else None),
        ("provider_sqlite", lambda info: Dispatcher().push("provider_sqlite_error_report", {"error": info["error"], "date": info["date"]})),
        ("provider_timestamp_error", lambda info: Dispatcher().push("provider_timestamp_error_report", {"server": info["server"], "error": info["status"], "day": info["day"]}))
        ]

        # Aqui está feito o teste de delay.
        delay_time = datetime.now() - timedelta(seconds=settings["max_lastUpdate_delay"])

        # Aqui está feito o teste de delay específico para o Last UpdateAt, por conta da formatação da hora.
        delay_time_updateAt = datetime.utcnow().replace(tzinfo=pytz.UTC) - timedelta(hours=settings["max_hour_delay"])

        # Realiza a verificação dos providers até qui sejam None.
        for (provider, proc_func) in processing_parameters:
            refresh_processing = Dispatcher().pop(provider)

            while refresh_processing is not None:

                proc_func(refresh_processing)

                refresh_processing = Dispatcher().pop(provider)

    def graphic_generate(self):
        import os
        import matplotlib as mpl
        if os.environ.get('DISPLAY','') == '':
            print('no display found. Using non-interactive Agg backend')
            mpl.use("Agg")
        import matplotlib.pyplot as plt

        # Usado para fazer cálculo do datetime para determinar período de 24h.
        date_past = datetime.now() - timedelta(days=settings["days_to_subtract_ping"])
        ping_histogram = Dispatcher().fetch_all("provider_ping", date_past, datetime.now())
        
        date_hist = {}
        host_legend = []

        for infodata in ping_histogram:
            if infodata["host"] not in date_hist:
                date_hist[infodata["host"]] = ([infodata["day"].hour + infodata["day"].minute/60.0 + infodata["day"].second/3600.0], [infodata["loss"]], [infodata["avg"]])
            else:
                date_hist[infodata["host"]][0].append(infodata["day"].hour + infodata["day"].minute/60.0 + infodata["day"].second/3600.0)
                date_hist[infodata["host"]][1].append(infodata["loss"])
                date_hist[infodata["host"]][2].append(infodata["avg"])

        fig, axs = plt.subplots(2,1, constrained_layout=True)

        # Aqui é gerado o gráfico.
        fig.suptitle("Ping Historigram", fontsize=16)
        axs[0].set_title('Ips')
        axs[0].set_xlabel("Hora")
        axs[0].set_ylabel("Loss")
        axs[1].set_xlabel('Hora')
        axs[1].set_title('Milisegundos')
        axs[1].set_ylabel('Latência')

        # Aqui é adicionado as informações no gráfico.
        for host in date_hist.keys():
            host_legend.append(host)

            axs[0].grid(True, linestyle="-.")
            axs[0].plot(date_hist[host][0], date_hist[host][1], ".-")
            axs[0].legend(host_legend, loc='upper center', bbox_to_anchor=(1.20, 1.0), fontsize="small", frameon=False)
            axs[1].grid(True, linestyle="-.")
            axs[1].plot(date_hist[host][0], date_hist[host][2], ".-")
            axs[1].legend(host_legend, loc='upper center', bbox_to_anchor=(1.20, 1.0), fontsize="small", frameon=False)

        # Caso o diretório não existir, ele cria um novo.
        if not os.path.exists("images"):
            os.mkdir("images")

        # Salva o gráfico em uma imagen o formato png.
        plt.savefig("images/ping_historigram.png", bbox_inches='tight')

        image_to_send = {
            "Generation Date": datetime.now()
        }

        Dispatcher().push("provider_image_report", image_to_send)
    
    # ToDo: Otimizar essa def, reduzindo a quantidade de for na mesma.
    def server_health_report(self):
        date_past = datetime.now() - timedelta(days=settings["days_to_subtract_server"])
        server_histogram = Dispatcher().fetch_all("provider_server_status", date_past, datetime.now())
        timestamp_histogram = Dispatcher().fetch_all("provider_timestamp_report", date_past, datetime.now())

        # ToDo: transformar os itens vazios abaixo em um dict, para otimizar.
        server_hist = {}
        timestamp_hist = {}
        error_server = []
        status_of_server = []
        count_error = 0

        # Usa as informações que vem diretamente do Provider TimeStamp.
        for timeinfo in timestamp_histogram:
            if timeinfo["last_message"] not in timestamp_hist:
                timestamp_hist[timeinfo["id"]] = ([timeinfo["name"]], [timeinfo["last_message"]])
            else:
                timestamp_hist[timeinfo["id"]][0].append(timeinfo["name"])
                timestamp_hist[timeinfo["id"]][1].append(timeinfo["last_message"])

        # Essa list comprehension verifica se o timeinfo["id"] está no timestamp_hist e adiciona no error_timestamp caso esteja.
        error_timestamp = [', '.join(val[0]) for (timeinfo, val) in timestamp_hist.items()]
        
        # Usa as informações que vem diretamente do Provider Server Status.
        for infodata in server_histogram:
            if infodata["server"] not in server_hist:
                server_hist[infodata["server"]] = ([infodata["server"]], [infodata["status"]], [infodata["day"]])
                status_of_server.append(infodata["status"])
            else:
                server_hist[infodata["server"]][0].append(infodata["server"])
                server_hist[infodata["server"]][1].append(infodata["status"])
                server_hist[infodata["server"]][2].append(infodata["day"])
                status_of_server.append(infodata["status"])

        # Faz a contagem do de erros no Server Hist e caso haja algum erro no servidor, ele adiciona.
        if len(status_of_server) > 0:
            if status_of_server[0].find("Errno -2"):
                if(status_of_server[0].find("Errno -2") != -1):
                    error_server.append(infodata["server"])
                    status_err = "Name or service not known"
                    count_error += 1
            elif status_of_server[0].find("Errno 111"):
                if(status_of_server[0].find("Errno -2") != -1):
                    error_server.append(infodata["server"])
                    status_err = "Conection refused"
                    count_error += 1
        else:
            status_err = "Não houveram erros."

        result_server = " " if error_server is None else error_server
        result_timestamp = " " if error_timestamp is None else error_timestamp
        count_error_time = 0 if error_timestamp is None else len(error_timestamp)
        
        server_health = {
            "Relatório do dia": datetime.today(),
            "Server": "\n",
            f"{count_error} falha(s): {status_err}": ", ".join(map(str, result_server)),
            "Timestamp": "\n",
            f"{count_error_time} falha(s)": ", ".join(map(str, result_timestamp)),
            }

        Dispatcher().push("server_health_report", server_health)