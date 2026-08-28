import mysql.connector

class Conexao:

    @staticmethod
    def conectar():
        mydb = mysql.connector.connect(
            user="root",
            password="988430466",
            host="localhost",
            database="bd_ss"
        )
        
        return mydb