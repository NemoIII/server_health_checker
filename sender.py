import os
import smtplib
from datetime import datetime, timedelta
from configuration import settings
from dispatcher import Dispatcher
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import base64
from email.utils import make_msgid
from twilio.rest import Client, TwilioException


receivers = settings["notify"] 
sender = settings["notifing_email"]
pwd = settings["password"]
smtp_connection = settings["smtp_to_connect"]
port_connection = settings["port"]

"""
	Classe que notifica aos usuários registrados no info.json, mas apenas os que apresentarem erro.

	- def: notify_user
		:param: self
"""
class Notification:
	def notify_user(self):
			# Recebe os pops vindo do Dispatcher, para poder rodar no 'for'.
			parameters = [("html_ping_histogram", "Alerta - Ping Histogram"), ("html_server_health", "Alerta - Server Health"), ("html__timestamp_error", "Alerta - Bad Gateway"), ("html_ping_report", "Alerta - Ping"), ("html_server_report", "Alerta - 404"), ("html_url_alert", "Alerta - Atraso"), ("html_lastUpdate_alert", "Alerta - Update"), ("html_updateAt_alert", "Alerta - Update At"), ("html_sqlite_error", "Alerta - Sqlite")]

			img_data = []

			# Atualente realiza a conexão com o smtp do gmail, pela porta 587, e nomeado como sender_smtp.
			with smtplib.SMTP(smtp_connection, port_connection) as sender_smtp:
				try:
					sender_smtp.starttls()
				except smtplib.SMTPNotSupportedError:
					pass
				sender_smtp.ehlo()

				if pwd is not None:# terminar essa verificação.
					sender_smtp.login(sender, pwd)

				# Verifica na lista de parâmetros acima e para buscar os relatórios.
				for (body, alert_subject) in parameters:
					# variável que realiza o refresh dos relatórios.
					refresh_report = Dispatcher().pop(body)

					# Enquanto o refresh_report não for nulo.
					while refresh_report is not None:
						msg = MIMEMultipart()

						# Remetente.
						msg["From"] = sender
						# Destinatários.
						msg["To"] = ", ".join(receivers)
						# Assuntos que variam de acordo com relatório que está carregado.
						msg["Subject"] = alert_subject
						body_html = MIMEText(refresh_report, "html")
						
						msg.attach(body_html)

						if body == "html_ping_histogram":
							# Busca a imagem e a abre realizando a leitura da mesma.
							img_data = open("images/ping_historigram.png", 'rb').read()
							cid = make_msgid()[1:-1]
							# Coloca a imagem no corpo do email.
							body_img = MIMEText(f'<br><img src="cid:{cid}"/><br>', "html")
							# Pega a imagem gerada no processor e anexa no email.
							image = MIMEImage(img_data, name=os.path.basename("images/ping_historigram.png"))
							image.add_header('Content-ID', f'<{cid}>')
							# Aqui ocorre a anexação dos textos e imagens no corpo do email.
							msg.attach(image)
							msg.attach(body_img)
												
						sender_smtp.sendmail(sender, receivers, msg.as_string())

						refresh_report = Dispatcher().pop(body)

"""
	Classe que notifica aos usuários registrados no info.json, mas apenas os que apresentarem erro.

	- def: sms_whatsapp_user
		:param: self
"""
class SMS_WhatsApp_Notification:
	def sms_whatsapp_user(self):
		try:
			# Recebe os pops vindo do Dispatcher, para poder rodar no 'for'.
			parameters_sms = [("provider_ping", "Urgente - Ping"), ("provider_server_status", "Urgente - Servidor"), ("provider_timestamp", "Urgente - TimesStamp"), ("provider_lastUpdate", "Urgente - Last Update"), ("provider_updateAt", "Urgente - Update At"), ("provider_sqlite", "Urgente - Base de Dados")]

			# Realiza a autenticação do serviço do Twilio e de usuário.
			client = Client(settings["account_sid_twilio"], settings["auth_token_twilio"])

			for (sms_message, alert) in parameters_sms:
				# Verifica qual problema repetiu por mais de 3 vezes no tempo (configurável) de 5 minutos (default).
				alert_search = Dispatcher().fetch_all(sms_message, (datetime.now() - timedelta(minutes=settings["sms_time_check"])), datetime.now())

				# Se o número de recorreência for superior ao valor estabelecido no info.json, ele dispara o sms.
				if len(alert_search) > settings["sms_time_check"]:
					Dispatcher().pop("sms_twilio_sended")
					if alert_search is not None:
						"""
							Para enviar mensagens com o WhatsApp em produção, o WhatsApp precisa aprovar formalmente sua conta. No https://www.twilio.com/console/sms/whatsapp/learn você confirma a conta com o WhatsApp. Enquanto não aprovar a conta, ligada ao número, dará o erro que está aqui https://www.twilio.com/docs/errors/21211.
						"""
						message = client.messages.create(
							body = (f"Temos um problema {alert}!"),
							from_= settings["from_mobile"], # para envio de mensagem por WhatsApp, basta colocar settings["from_whatsapp"]
							to = settings["to_mobile"] # para envio de mensagem por WhatsApp, basta colocar settings["to_whatsapp"]
						)
						message.sid
						sms_sended = {
						"alert": alert,
						"date": datetime.now()
						}
						Dispatcher().push("sms_twilio_sended", sms_sended)

		except TwilioException as tw:
			twilio_fail = {
				"falha": tw,
				"date": datetime.now()
			}
			Dispatcher().push("twilio_error_report", twilio_fail)

"""
	Classe que notifica aos usuários registrados no info.json, mas apenas os que apresentarem erro.

	- def: sms_user
		:param: self
"""
class SMS_Notification:
	def sms_user(self):
		import requests
		try:
			# Recebe os pops vindo do Dispatcher, para poder rodar no 'for'.
			parameters_sms = [("provider_ping", "Urgente - Ping"), ("provider_server_status", "Urgente - Servidor"), ("provider_timestamp", "Urgente - TimesStamp"), ("provider_lastUpdate", "Urgente - Last Update"), ("provider_updateAt", "Urgente - Update At"), ("provider_sqlite", "Urgente - Base de Dados")]

			for (sms_message, alert) in parameters_sms:
				# Verifica qual problema repetiu por mais de 3 vezes no tempo (configurável) de 5 minutos (default).
				alert_search = Dispatcher().fetch_all(sms_message, (datetime.now() - timedelta(minutes=settings["sms_time_check"])), datetime.now())

				# Se o número de recorreência for superior ao valor estabelecido no info.json, ele dispara o sms.
				if len(alert_search) > settings["sms_time_check"]:
					Dispatcher().pop("sms_textbelt_sended")
					if alert_search is not None:
						message = requests.post(settings["textbelt_end_point"],{
							"phone": settings["from_textbelt_mobile"],
							"body": (f"Temos um problema {alert}!"),
							"key": settings["textbelt_key"]
						})
						message.json()
						sms_sended = {
						"alert": alert,
						"date": datetime.now()
						}
						Dispatcher().push("sms_textbelt_sended", sms_sended)

		except Exception as ex:
			textbelt_fail = {
				"falha": ex,
				"date": datetime.now()
			}
			Dispatcher().push("textbelt_error_report", textbelt_fail)