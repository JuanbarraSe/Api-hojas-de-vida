from database import conectar_bd
from werkzeug.security import generate_password_hash
from getpass import getpass

def crear_administrador():

    nombre = input("Ingresar nombre del rol reclutador:")
    correo = input("Ingresar correo del rol reclutador:")
    password = getpass("Contraseña: ")

    if len(password) < 8:
        print("Debe tener 8 caracteres")
        return

    conexion = conectar_bd()
    cursor = conexion.cursor()
    
    try:
        cursor.execute("SELECT id FROM Usuarios WHERE Correo = %s", (correo,))
        existente = cursor.fetchone()

        if existente:
            print("Este correo ya esta registrado")
            return

        password_hash = generate_password_hash(password)

        sql = "INSERT INTO Usuarios(Nombre,Correo,password,rol,Estado) VALUES (%s,%s,%s,'Reclutador',1)"
        cursor.execute(sql,(nombre,correo,password_hash))

        conexion.commit()
        print("Reclutador creado satisfactoriamente")

    except Exception as error:
        conexion.rollback()
        print("Error:",error)
    finally:
        cursor.close()
        conexion.close()

if __name__== "__main__":
    crear_administrador()