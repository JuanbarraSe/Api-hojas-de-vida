import mysql.connector

def conectar_bd():
    conexion = mysql.connector.connect(
        host="",
        user="root",
        password="",
        database="HojaDeVida2026"
    )
    return conexion