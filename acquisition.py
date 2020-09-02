import os
import sys
from datetime import datetime
from configuration import settings
import requests
from requests.exceptions import HTTPError, ConnectionError
import subprocess, time, re
from dispatcher import Dispatcher
import urllib.request, json

"""
    Classe responsável por realizar testes de forma mais automatizada.

    - def: check
        :param: self
"""
class BaseCheck:
	def check(self):
		pass

"""
    Classe que tem por função checar o ping do servidor

    - def: check
        :param: self
"""
class PingCheck(BaseCheck):

    def check(self):
        # Busca os ips que devem ser testados.
        self.hostnames = settings["ips"]
        ping = settings["num_pings"]

        for ip in self.hostnames:
            try:
                # Começa a usar o comando de teste de ping.
                proc = subprocess.Popen(
                ['ping', '-q', '-c', str(ping), ip],
                stdout=subprocess.PIPE)
                
                # Bloqueie até que os resultados estejam prontos e depois devolva-os.
                try:
                    out, err = proc.communicate()
                except:
                    return None
                if err is not None:
                    return None

                # Colocando as informacoes de saida do teste e codifica a string usando o codec registrado para codificação
                output = out.decode("utf-8").splitlines()

                if len(output) >= 5:
                    output = out.decode("utf-8").splitlines()[4]
                    output_rtt = output.split("/")[4] if len(output) > 0 else 0

                output_normal = out.decode("utf-8").splitlines()[3]

                if output is None:
                    return None
                # Recebe o output e a função divide a string original
                output_res = output_normal.split()[:10]

                # Dicionário que recebe os valores que devem ser passados, para que possam ser processados porteriormente.
                output_result = {
                    "host": ip,
                    "transmitted": int(output_res[0]),
                    "received": int(output_res[3]),
                    "loss": int(output_res[5].replace("%","")),
                    "time": int(output_res[9].replace("ms","")),
                    "day": datetime.now(),
                    "avg": float(output_rtt)
                }
                # Envia como chave o "provider_ping" e valor o "output_result ao modulo Dispatcher atraves do push."
                Dispatcher().push("provider_ping", output_result)

            except subprocess.CalledProcessError as err:
                return None
        return output_result
    
    
"""
    Realiza a verificação do status do servidor.

    - def: check
        :param: self
"""
class ServerCheck(BaseCheck):
    def check(self):
        
        # Verifica os servidores no info.json para serem testados.
        for server in settings["servers"]:
            try:
                # Se tudo estiver ok com os servidores não faz nada.
                servers = requests.get(server, timeout=settings["max_timeout"])

                """server_ok = {
                    "server": servers,
                    "date": datetime.now()
                }
                Dispatcher().push("provider_server_ok", server_ok)"""

            except requests.exceptions.ConnectionError as err:
                # Os servidores que estiverem com problemas, gera um dicionário com as informações abaixo.
                checked_server = {
                    "server": server,
                    "status": str(err),
                    "day": datetime.now()
                }

                # As informações geradas no caso de algo ruim, envia para o Dispatcher atraves do push o "provider_server_status" como chave e "checked_server" como valor.
                Dispatcher().push("provider_server_status", checked_server)

        return 

"""
    Realiza o checagem da url, para pegar a atualização das odds

    - def: check
        :param: self
"""
class TimeStampCheck(BaseCheck):
    def check(self):
        try:
            # Verifica item por item no timestampcheck_urls.
            for timestamp_url in settings["timestampcheck_urls"]:
                # Abre a url que tem a informação que se busca.
                with urllib.request.urlopen(timestamp_url[0]) as requestcheck_urls:
                    # Faz uma decodificação de string que foi lido no json.
                    data = json.loads(requestcheck_urls.read().decode())

                    # Faz a verificação de ultima atualização do status.
                    if timestamp_url[1] in data and timestamp_url[1] == "lastUpdate":
                        data_checked = {
                            "state": data["state"],
                            "GS": data["GS"],
                            "GR": data["GR"],
                            "OL": data["OL"],
                            "OP": data["OP"],
                            "GU": data["GU"],
                            "GL": data["GL"],
                            "lastupdate_message": datetime.fromisoformat(data[timestamp_url[1]]).replace(tzinfo=None),
                            }
                        # Envia ao Dispatcher um relatório com as informações acima.
                        Dispatcher().push("provider_lastUpdate", data_checked)
                    else:
                        # olha uma a uma a informacao de 'last_message_timestamp'.
                        for message in data:
                            # Se nao for None ele pega as informações e as colocam no data_checked.
                            if message[timestamp_url[1]] is not None:
                                if timestamp_url[1] in message and timestamp_url[1] == "last_message_timestamp":
                                    
                                    data_checked = {
                                        "id": message["id"],
                                        "name": message["name"],
                                        "last_message": datetime.fromisoformat(message["last_message_timestamp"]).replace(tzinfo=None),
                                        "processing_delay": message["processing_delay"]
                                    }
                                    # Envia ao Dispatcher um relatório com as informações acima.
                                    Dispatcher().push("provider_timestamp", data_checked)
                        
                                elif timestamp_url[1] in message and timestamp_url[1] == "updatedAt": 
                                    data_checked = {
                                        "id": message["id"],
                                        "base": message["base"],
                                        "name": message["name"],
                                        "updateAt": datetime.fromisoformat(message[timestamp_url[1]].replace("Z", "+00:00"))
                                    }
                                    Dispatcher().push("provider_updateAt", data_checked)
        
        except urllib.request.HTTPError as err:
            checked_timestamp = {
                    "server": timestamp_url[0],
                    "status": str(err),
                    "day": datetime.now()
                }

                # As informações geradas no caso de algo ruim, envia para o Dispatcher atraves do push o "provider_server_status" como chave e "checked_server" como valor.
            Dispatcher().push("provider_timestamp_error", checked_timestamp)

if __name__ == "__main__":
    ping = PingCheck()
    server_checked = ServerCheck()
    TimeStampCheck().check()

    ping_results = ping.check()
    if ping_results is None:
        print("Ping failed")
        exit()
    