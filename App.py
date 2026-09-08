from flask import Flask, request
from database import conectar_bd
app = Flask(__name__)

@app.route("/")
def inicio():
    return "Api hoja de vida funcionando"

@app.route("/probar")
def probar_data():
    conexion = conectar_bd()
    if conexion.is_connected():
        conexion.close()
        return{
            "Mensaje":"Conexion ok"
        }
    
@app.route("/api/registrohv", methods = ["POST"])
def registrohojavida():
    conexion = conectar_bd()
    cursor = conexion.cursor()
    datos = request.json
    #Consultar si el correo ya existe
    buscar = "SELECT id,Nombre  from hojas_vida where Correo = %s"
    cursor.execute(buscar,(datos["Correo"],))
    usu = cursor.fetchone()
    if usu:
        cursor.close()
        conexion.close()

        return{
            "Mensaje" : "El usuario ya existe"
        }
    
    sql = "INSERT INTO hojas_vida(Nombre,Ciudad,Edad,Correo,Fotografia,Programa,Ficha,Jornada) values (%s,%s,%s,%s,%s,%s,%s,%s)"
    valor = (datos["Nombre"],
             datos["Ciudad"],
             datos["Edad"],
             datos["Correo"],
             datos.get("Fotografia"),
             datos["Programa"],
             datos["Ficha"],
             datos["Jornada"])

    cursor.execute(sql,valor)
    conexion.commit()

    #Manejo del id de la hoja de vida
    id_generado = cursor.lastrowid

    cursor.close()
    conexion.close()
    return{
        "Mensaje":"Hoja de vida creada correctamente","id":id_generado
    }

@app.route("/api/hojas-vida/<int:id>")
def obtener_hojasvidaid(id):
    return{
        "Mensaje":"Hoja de vida encontrada","id":id
    }

@app.route("/api/hoja-vida")
def obtener_hojasvida():
    #return{
        #  "Mensaje":"Listado de hojas de vida"
    #}
    hojas_vida =[{
        "id":1,
        "Nombre":"Sebastian Barragan",
        "Ciudad":"Bogota",
        "Edad" : 19,
        "Correo" : "sebas@gmail.com",
        "Fotografia" : "foto",
        "Programa" : "ADSO",
        "Ficha" : 3262320,
        "Jornada" : "Diurna"
    },
    {
        "id":2,
        "Nombre":"Oscar Barragan",
        "Ciudad":"Bogota",
        "Edad" : 50,
        "Correo" : "oscarr23@gmail.com",
        "Fotografia" : "foto",
        "Programa" : "Multimedia",
        "Ficha" : 2320,
        "Jornada" : "Diurna"   
    },
    {
        "id":3,
        "Nombre":"Marcela Rodriguez",
        "Ciudad":"Barranquilla",
        "Edad" : 26,
        "Correo" : "marce.barraqui@gmail.com",
        "Fotografia" : "foto",
        "Programa" : "Actividad Fisica",
        "Ficha" : 254891,
        "Jornada" : "Noche"  
    },
    {
        "id":4,
        "Nombre":"Duvan Gomez",
        "Ciudad":"Bogota",
        "Edad" : 19,
        "Correo" : "duvancho@gmail.com",
        "Fotografia" : "foto",
        "Programa" : "Enfermeria",
        "Ficha" : 301574,
        "Jornada" : "Diurna"
    }

    ]
    return hojas_vida

@app.route("/api/listarhv")
def listar_hojasvida():
    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)

    sql = "SELECT * FROM Hojas_vida"
    cursor.execute(sql)

    hojas_vida = cursor.fetchall()
    cursor.close()
    conexion.close()

    return hojas_vida

@app.route("/api/consultahv/<int:id>", methods=["GET"])
def obtener_hvida(id):
    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)

    sql = "SELECT * FROM hojas_vida where id = %s"
    cursor.execute(sql,(id,))

    datos = cursor.fetchone()

    cursor.close()
    conexion.close()

#Que pasa cuando es nulo
    if datos is None:
        return{
            "No se encontro la hoja de vida"
        }
    return datos

@app.route("/api/eliminarhv/<int:id>", methods=["DELETE"])
def eliminarhojavida(id):
    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)

    sql = "DELETE FROM hojas_vida where id = %s"
    cursor.execute(sql,(id,))

    if cursor.rowcount == 0:
        cursor.close()
        conexion.close()
        return{
            "Mensaje": "No se encontro la hoja de vida"
        }
    conexion.commit()
    cursor.close()
    return{
        "Mensaje" : "hoja de vida eliminada satisfactoriamente"
    }

@app.route("/api/actualizarhv/<int:id>", methods=["PUT"])
def actualizarhojavida(id):
    datos = request.get_json()
    conexion = conectar_bd()
    cursor = conexion.cursor(buffered=True)

    #Verificar que la hoja exista
    buscar = "SELECT id FROM hojas_vida where id = %s"
    cursor.execute(buscar,(id,))
    resultado = cursor.fetchone()

    if resultado is None:
        cursor.close()
        conexion.close()
        return{
            "Mensaje" : "No se encontro la hoja de vida"
        }
    sqlcorreo = "SELECT id FROM hojas_vida where Correo = %s and id != %s"
    cursor.execute(sqlcorreo,(datos["Correo"], id))
    resultado = cursor.fetchone()

    if resultado is not None:
            cursor.close()
            conexion.close()
            return{
                "Mensaje" : "correo electronico ya esta registrado en otra hoja de vida"
            }
    sqlactualizar = "UPDATE hojas_vida SET Nombre = %s, Ciudad = %s, Edad = %s, Correo = %s, Fotografia = %s, Programa = %s, Ficha = %s, Jornada = %s WHERE id = %s"
    valores = (datos["Nombre"],
                 datos["Ciudad"],
                 datos["Edad"],
                 datos["Correo"],
                 datos.get("Fotografia"),
                 datos["Programa"],
                 datos["Ficha"],
                 datos["Jornada"],
                 id)
    
    cursor.execute(sqlactualizar,valores)
    conexion.commit()
    cursor.close()
    
    return{
        "Mensaje" : "hoja de vida actualizada",
        "id":id
    }

if __name__=="__main__":
    app.run(debug=True)