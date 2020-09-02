from json import load
from os.path import realpath, dirname, isfile

"""
	Busca o arquivo Json, abre para leitura e captura de informações.

	- def: __init__
		:param: self
	- def read_json
		:param: self
		:param: file
"""
class JsonManager:
	
	def __init__(self):
		self.path = dirname(realpath(__file__)) + '/'

	def read_json(self, file):
		# Vai em busca do arquivo.
		if isfile(self.path + file):
			with open(self.path + file) as f:
				data = load(f)
			return data
		else:
			return False

list_of_server = JsonManager()
# Variável que mantém a localização do arquivo com as informações para testes.
settings = list_of_server.read_json("config/info.json")