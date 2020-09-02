import os
import csv
from os.path import realpath, dirname, isfile
from dispatcher import Dispatcher

"""
  Classe com a função de recolher informações dos teste, após isso, criar um arquivo csv com essas informações.
  Ainda sendo implementada.

  - def: colect_report
    :param: self
  - def: grafic_generate
    :param: self
"""
class CreateReport:
  # Função que gera o relatório da checagem em csv.
  def colect_report(self):
    alert_parameters = [("Alerta - Ping", "ping_error_report", "html_ping_report"), ("Alerta - Bad Gateway", "provider_timestamp_error_report", "html__timestamp_error"), ("Alerta - 404", "server_error_report", "html_server_report"), ("Alerta - Atraso", "provider_timestamp_report", "html_url_alert"), ("Alerta - Update", "provider_lastUpdate_report", "html_lastUpdate_alert"), ("Alerta - Update At", "provider_updateAt_report", "html_updateAt_alert"), ("Alerta - Sqlite", "provider_sqlite_error_report", "html_sqlite_error"), ("Alerta - Ping Histogram", "provider_image_report", "html_ping_histogram"), ("Alerta - Server Health", "server_health_report", "html_server_health")]

    for (alert_title, message_html, html_report) in alert_parameters:
      # variável que realiza o refresh dos relatórios.
      refresh_alert = Dispatcher().pop(message_html)

      # Relatório de html com o alerta do ping.
      while refresh_alert is not None:
        # Gera um html a ser entregue no email.
        html_to_send = ""

        for (chave, valor) in refresh_alert.items():          
          html_to_send += f"""
                  <li><b>{chave}:</b> {valor}</li>
          """

        html = f"""
        <html>
              <head>
                <title>{alert_title}</title>
              </head>
              <body>
                <h1>Por favor, contacte o responsável e tome as medidas necessárias para restabelecer o servico.</h1>
            <p style="font-size:200%"><b><ol>{html_to_send}</ol></b></p>
          </body>
        </html>
        """
        Dispatcher().push(html_report, html)

        # Após o envio do relatório, os dados são eliminados.
        refresh_alert = Dispatcher().pop(message_html) 
