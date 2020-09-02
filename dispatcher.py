import os
from datetime import datetime, timedelta
import sqlite3
import json
from pathlib import Path
from json_parser import BSEncoder
from configuration import settings

"""
    Recebe e envia todos os relatórios e informações geradas pelos outros módulos.

    - def: __init__
        :param: self
    - def: push
        :param: self
        :param: key
        :param: value
    - def: pop
        :param: self
        :param: key
    - def: fetch_all
        :param: self
        :param: key
        :param: from_date
        :param: to_date

"""
class Dispatcher(object):
    def __init__(self):
        # Aqui cria-se a conexão com o DB.
        self.sqliteConnection = sqlite3.connect("dispatcher.sqlite")
        # Estabelece conexão.
        self.data_base_conn = self.sqliteConnection.cursor()
        # Cria uma tabela no database chamada de dispatcher_storage.
        self.data_base_conn.execute("CREATE TABLE IF NOT EXISTS dispatcher_storage (chave text, timestamp datetime, valor json)")
        # Cria uma tabela no database chamada de search_storage.
        self.data_base_conn.execute("CREATE TABLE IF NOT EXISTS search_storage (chave text PRIMARY KEY, timestamp datetime)")
        # self.fetch_all("provider_ping", "2020-07-29T09:00:00", datetime.now())
        
    def push(self, key, value):
        try:
            # Comando de inserção dos dados no banco de dados.
            insert_report = "insert into dispatcher_storage values (?, ?, ?)"
            # Aqui, o self.data_base_conn usa o comando execute para inserir os dados.
            self.data_base_conn.execute(insert_report, (key, datetime.now().isoformat(), json.dumps(value, cls=BSEncoder())))
            # Registra as mudanças no banco de dados.
            self.sqliteConnection.commit()
        except sqlite3.OperationalError as sql_error:
            error = {
                "sql_error": str(sql_error),
                "date": datetime.now()
            }
            self.push("provider_sqlite", error)
            
    def pop(self, key):
        try:
            # Realiza uma pesquisa no DB juntando as duas tabelas.
            sql_inner_join = """
                select * 
                from dispatcher_storage
                left join search_storage
                on dispatcher_storage.chave = search_storage.chave
                where dispatcher_storage.chave = ? and (dispatcher_storage.timestamp > search_storage.timestamp or search_storage.timestamp is null)
                order by timestamp limit 1;
            """
            self.data_base_conn.execute(sql_inner_join, (key,))
            sql_join_result = self.data_base_conn.fetchone()
            # Se o sql_join_result não for None, ele já realiza o update.
            if sql_join_result is not None:
                sql_update = """
                    insert into search_storage values (?, ?) on conflict(chave) do update set timestamp = excluded.timestamp
                """
                self.data_base_conn.execute(sql_update, (key, sql_join_result[1]))
            # Registra as mudanças no DB.
            self.sqliteConnection.commit()

            if sql_join_result is not None:
                obj = json.loads(sql_join_result[2])
                field_map = {"provider_ping": "day",
                             "provider_server_status": "day",
                             "provider_timestamp": "last_message",
                             "provider_lastUpdate": "lastupdate_message",
                             "provider_updateAt": "updateAt"}
                if key in field_map:
                    obj[field_map[key]] = datetime.fromisoformat(obj[field_map[key]])
                return obj
            else:
                return None
                        
        except sqlite3.Error as sql_error:
            error = {
                "sql_error": str(sql_error),
                "date": datetime.now()
            }
            self.push("provider_sqlite", error)

    def fetch_all(self, key, from_date, to_date):
        """
            O propósito é filtrar o histórico do ping, colocando datas diferentes para poder pesquisar, uma data de início e uma de fim. Escolher a chave que será retirada o histórico.
        """
        try:
            if from_date is None and to_date is None:
                from_date = datetime.now()
                ping_select = """
                    select valor
                    from dispatcher_storage
                    where chave = "provider_ping"
                """
                self.data_base_conn.execute(ping_select)
                sql_time_history = self.data_base_conn.fetchall()
            self.sqliteConnection.commit()

            if from_date is not None and to_date is None:
                ping_select = """
                    select valor
                    from dispatcher_storage
                    where timestamp > ? and chave = ?
                """
                self.data_base_conn.execute(ping_select, (datetime.isoformat(from_date), key))
                sql_time_history = self.data_base_conn.fetchall()
            self.sqliteConnection.commit()

            if from_date is None and to_date is not None:
                ping_select = """
                    select valor
                    from dispatcher_storage
                    where timestamp < ? and chave = ?
                """
                self.data_base_conn.execute(ping_select, (datetime.isoformat(to_date), key))
                sql_time_history = self.data_base_conn.fetchall()
            self.sqliteConnection.commit()
            
            if from_date is not None and to_date is not None:
                ping_select = """
                    select valor
                    from dispatcher_storage
                    where timestamp between ? and ? and chave = ?
                """
                self.data_base_conn.execute(ping_select, (datetime.isoformat(from_date), datetime.isoformat(to_date), key))
                sql_time_history = self.data_base_conn.fetchall()

            self.sqliteConnection.commit()

            # ToDo: Transformar esse if e for loop em def, para ser usada no Fetch_all e no Pop.
            if sql_time_history is not None:
                retorno  = []
                for linha in sql_time_history:
                    obj = json.loads(linha[0])
                    field_map = {"provider_ping": "day",
                             "provider_server_status": "day",
                             "provider_timestamp": "last_message",
                             "provider_lastUpdate": "lastupdate_message",
                             "provider_updateAt": "updateAt"}
                    if key in field_map:
                        obj[field_map[key]] = datetime.fromisoformat(obj[field_map[key]])
                        retorno.append(obj)
                return retorno
            else:
                return None

        except sqlite3.Error as sql_error:
            error = {
                "sql_error": str(sql_error),
                "date": datetime.datetime.now()
            }
            self.push("provider_sqlite", error)
    
if __name__ == "__main__":
    print("Testando módulo dispatcher...")

    print("Criando classe Dispatcher ", end='')
    dispatcher = Dispatcher()
    print("OK")

    print("Inserindo e retirando um evento ", end='')
    dispatcher.push("teste", {"teste": "valor"})
    val = dispatcher.pop("teste")
    if val != {"teste": "valor"}:
        print("ERRO!")
        os.abort()
    print("OK")

    print("Inserindo e retirando dois eventos ", end='')
    dispatcher.push("teste", {"teste": "valor1"})
    dispatcher.push("teste", {"teste": "valor2"})
    val = dispatcher.pop("teste")
    if val != {"teste": "valor1"}:
        print("ERRO!")
        os.abort()
    val = dispatcher.pop("teste")
    if val != {"teste": "valor2"}:
        print("ERRO!")
        os.abort()
    print("OK")

    print("Inserindo e retirando evento inexistente", end='')
    dispatcher.push("teste", {"teste": "valor"})
    val = dispatcher.pop("teste")
    if val != {"teste": "valor"}:
        print("ERRO!")
        os.abort()
    val = dispatcher.pop("teste")
    if val != None:
        print("ERRO!")
        os.abort()
    print("OK")

    print("Inserindo e retirando eventos de tipos diferentes", end='')
    dispatcher.push("teste1", {"teste": "valor"})
    dispatcher.push("teste2", {"teste": "valor"})
    val = dispatcher.pop("teste1")
    if val != {"teste": "valor"}:
        print("ERRO!")
        os.abort()
    val = dispatcher.pop("teste2")
    if val != {"teste": "valor"}:
        print("ERRO!")
        os.abort()
    print("OK")

    print("Inserindo e retirando um evento persistido", end='')
    dispatcher.push("teste_persistencia", {"teste": "valor"})
    del dispatcher

    dispatcher = Dispatcher()
    val = dispatcher.pop("teste_persistencia")
    if val != {"teste": "valor"}:
        print("ERRO!")
        os.abort()
    print("OK")
