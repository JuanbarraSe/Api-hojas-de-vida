from flask import Flask, request, jsonify
from database import conectar_bd
from flask_cors import CORS
from dotenv import load_dotenv
import os
load_dotenv()
from flask_jwt_extended import(
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from werkzeug.security import(
    generate_password_hash,
    check_password_hash)
from functools import wraps
app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
if not app.config["JWT_SECRET_KEY"]:
    raise RuntimeError("NO SE ENCONTRO LA LLAVE JWT")
jwt = JWTManager(app)
CORS(app)

def rol_requerido(rol):
    def decorador(funcion):
        @wraps(funcion)
        @jwt_required()
        def wrapper(*arg,**kwargs):
            claims = get_jwt()

            if claims.get("rol") != rol:
                return jsonify({"Mensaje": "No tiene permiso para ingresar"}), 403
            return funcion(*arg,**kwargs)
        return wrapper
    return decorador

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
    
@app.route("/api/registrarusuario", methods=["POST"])
def registroUsuario():
    datos = request.get_json()

    nombre = datos.get("nombre")
    correo = datos.get("correo")
    password = datos.get("password")

    conexion = conectar_bd()
    cursor = conexion.cursor()

    # Verificar si el correo ya existe
    sqlbuscar = "SELECT id FROM usuarios WHERE Correo = %s"
    cursor.execute(sqlbuscar, (correo,))
    usuario = cursor.fetchone()

    if usuario:
        cursor.close()
        conexion.close()

        return jsonify({
            "mensaje": "El correo ya está registrado"
        })

    # Guardar usuario
    sql = """INSERT INTO usuarios (Nombre, Correo, password, rol, estado) VALUES (%s, %s, %s, %s, %s)"""

    password_hash = generate_password_hash(password)
    valores = (nombre, correo, password_hash, "usuario", 1)

    cursor.execute(sql, valores)
    conexion.commit()

    cursor.close()
    conexion.close()

    return jsonify({
        "mensaje": "Usuario registrado correctamente"
    })

@app.route("/api/login/", methods=["POST"])
def login():
    datos = request.get_json()
    if not datos:
        return jsonify({"Mensaje":"Datos incompletos"}), 400

    Correo = datos.get("Correo","").strip().lower()
    password = datos.get("password","")

    if not Correo or not password:
        return jsonify ({"Mensaje": "Ingrese correo y contraseña"}), 400

    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)
    try:
        #Buscar usuario por correo
        sql = "SELECT id, Nombre, Correo, password, rol, Estado FROM Usuarios WHERE LOWER(TRIM(Correo)) = %s"
        cursor.execute(sql,(Correo,))
        usuario = cursor.fetchone()

        print("Correo buscado:", repr(Correo))
        print("Usuario encontrado:", usuario is not None)
        if usuario:
            print("Clave coincide:", check_password_hash(usuario["password"], password))
            
        # Verificar si existe el usuario
        if not usuario:
            return jsonify({"Mensaje": "Correo y/o contraseña incorrecta"}), 401

        # Verificar el estado
        if not usuario["Estado"]:
            return jsonify({"Mensaje":"La cuenta esta desactivada"}), 403

        # Verificar contraseña cifrada
        if not check_password_hash(usuario["password"], password):
            return jsonify({"Mensaje":"Correo y/o contraseña incorrecta"}), 401

        # Generar el token
        token = create_access_token(identity=str(usuario["id"]),
                                    additional_claims={"rol":usuario["rol"]})

        # Respuesta
        return jsonify({"Mensaje":"Inicio de sesion correcto",
                       "token":token,
                       "usuario":{"id":usuario["id"],
                                  "Nombre":usuario["Nombre"],
                                  "Correo":usuario["Correo"],
                                  "rol":usuario["rol"]} }), 200

    finally:
        cursor.close()
        conexion.close()

@app.route("/api/registrohv", methods = ["POST"])
def registrohojavida():
    conexion = conectar_bd()
    cursor = conexion.cursor()
    datos = request.json

    #Consultar si el correo ya existe
    buscar = "SELECT id,Nombre  from hojas_vida where correo = %s"
    cursor.execute(buscar,(datos["correo"],))
    usu = cursor.fetchone()
    if usu:
        cursor.close()
        conexion.close()

        return{
            "Mensaje" : "El usuario ya existe"
        }
    
    sql = "INSERT INTO hojas_vida(nombre,ciudad,edad,correo,fotografia,programa,ficha,jornada) values (%s,%s,%s,%s,%s,%s,%s,%s)"
    valor = (datos["nombre"],
             datos["ciudad"],
             datos["edad"],
             datos["correo"],
             datos.get("fotografia"),
             datos["programa"],
             datos["ficha"],
             datos["jornada"])

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
@jwt_required()
def obtener_hojasvidaid(id):
    return{
        "Mensaje":"Hoja de vida encontrada","id":id
    }

@app.route("/api/hoja-vida")
@jwt_required()
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

@app.route("/api/listarhv", methods=["GET"])
@jwt_required()
def listar_hojasvida():
    usuario_id = get_jwt_identity()
    rol = (get_jwt().get("rol") or "").lower()

    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)
    try:
        # El reclutador ve todas (igual que ya te funciona)
        if rol == "reclutador":
            cursor.execute("SELECT * FROM hojas_vida")
            return jsonify(cursor.fetchall()), 200

        # El aprendiz ve su hoja completa
        if rol == "aprendiz":
            cursor.execute("""
                SELECT h.*
                FROM hojas_vida h
                JOIN Usuarios u ON LOWER(TRIM(u.Correo)) = LOWER(TRIM(h.correo))
                WHERE u.id = %s
            """, (usuario_id,))
            hoja_vida = cursor.fetchone()

            if not hoja_vida:
                return jsonify({"Mensaje": "No tienes hoja de vida registrada"}), 404

            hv_id = hoja_vida["id"]

            cursor.execute("SELECT * FROM Estudios WHERE hoja_vida_id = %s", (hv_id,))
            estudios = cursor.fetchall()

            cursor.execute("SELECT * FROM Cursos WHERE hoja_vida_id = %s", (hv_id,))
            cursos = cursor.fetchall()

            cursor.execute("SELECT * FROM Experiencias WHERE hoja_vida_id = %s", (hv_id,))
            experiencias = cursor.fetchall()

            # Cada experiencia lleva sus habilidades
            for exp in experiencias:
                cursor.execute("SELECT * FROM Habilidades WHERE experiencia_id = %s", (exp["id"],))
                exp["Habilidades"] = cursor.fetchall()

            return jsonify({
                "Datos_personales": hoja_vida,
                "Estudios": estudios,
                "Cursos": cursos,
                "Experiencias": experiencias
            }), 200

        return jsonify({"Mensaje": "Rol no autorizado"}), 403
    finally:
        cursor.close()
        conexion.close()

@app.route("/api/consultahv/<int:id>", methods=["GET"])
@rol_requerido("Reclutador")
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


@app.route("/api/registrarestudios/<int:id>/estudios", methods=["POST"])
def registrarestudios(id):

    datos = request.get_json()

    Nivel = datos["Nivel"]
    Institucion = datos["Institucion"]
    Titulo = datos["Titulo"]
    Anio = datos["Anio_graduacion"]

    conexion = conectar_bd()
    cursor = conexion.cursor()

    sql = "INSERT INTO Estudios (hoja_vida_id, Nivel, Institucion, Titulo, Anio_graduacion) VALUES (%s, %s, %s, %s, %s)"
    valor = (id,
            Nivel,
            Institucion,
            Titulo,
            Anio)
    
    cursor.execute(sql,valor)
    conexion.commit()

    cursor.close()
    conexion.close()

    return{
        "Mensaje" : "Estudio registrado correctamente"
    }

@app.route("/api/consultarestudios/<int:id>/estudios", methods=["GET"])
def obtenerEstudioshvid(id):
    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)

    sql = "SELECT * FROM Estudios WHERE hoja_vida_id = %s"
    cursor.execute(sql,(id,))

    estudios = cursor.fetchall()

    cursor.close()
    conexion.close()

    return{
        "Mensaje" : estudios
    }

@app.route("/api/estudios/<int:id>", methods=["GET"])
def obtenerestudio(id):
    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)

    sql = "SELECT * FROM Estudios WHERE id = %s"

    cursor.execute(sql,(id,))

    estudio = cursor.fetchone()

    cursor.close()
    conexion.close()
    if estudio:
        return{
        "Mensaje" : "Estudio encontrado",
        "Estudio" : estudio
    }
    return{
        "Mensaje" : "No se encontro el estudio"
    }

@app.route("/api/actualizarestudio/<int:id>", methods=["PUT"])
def actualizarEstudio(id):
    datos = request.get_json()

    conexion = conectar_bd()
    cursor = conexion.cursor()

    sql = "UPDATE Estudios SET Nivel = %s, Institucion = %s, Titulo = %s, Anio_graduacion = %s WHERE id = %s"
    valores = (
        datos["Nivel"],
        datos["Institucion"],
        datos["Titulo"],
        datos["Anio_graduacion"],
        id
    )
    cursor.execute(sql,valores)

    conexion.commit()

    cursor.close()
    conexion.close()
    return{
        "Mensaje" : "Estudio actualizado",
        "id":id
    }

@app.route("/api/eliminarestudio/<int:id>", methods=["DELETE"])
def eliminarEstudio(id):
    conexion = conectar_bd()
    cursor = conexion.cursor()

    sql = "DELETE FROM Estudios WHERE id = %s"
    cursor.execute(sql,(id,))

    if cursor.rowcount == 0:
        cursor.close()
        conexion.close()
        return{
            "Mensaje" : "No se encontro el estudio"
        }
    conexion.commit()

    cursor.close()
    conexion.close()

    return{
        "Mensaje" : "Estudio eliminado correctamente"
    }



@app.route("/api/consultarexperiencia/<int:id>/experiencias", methods=["GET"])
def obtenerexperiencia(id):  # <-- Agrega 'id' aquí como argumento de la función
    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)

    sql = "SELECT * FROM Experiencias WHERE hoja_vida_id = %s"
    cursor.execute(sql, (id,))
    experiencia = cursor.fetchall()

    cursor.close()
    conexion.close()

    return {
        "Mensaje": experiencia
    }
@app.route("/api/experiencia/<int:id>", methods=["GET"])
def obtenerExperiencia(id):
    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)

    sql = "SELECT * FROM Experiencias WHERE id = %s"

    cursor.execute(sql,(id,))

    experiencia = cursor.fetchone()

    cursor.close()
    conexion.close()

    if experiencia:
        return{
            "Mensaje" : "Experiencia encontrada",
            "Experiencia" : experiencia
        }

    return{
        "Mensaje" : "No se encontro la experiencia"
    }

@app.route("/api/actualizarexperiencia/<int:id>", methods=["PUT"])
def actualizarExperiencia(id):
    datos = request.get_json()

    conexion = conectar_bd()
    cursor = conexion.cursor()

    sql = "UPDATE Experiencias SET Empresa = %s, Cargo = %s, Tiempo = %s, Funciones = %s WHERE id = %s"
    valores = (
        datos["Empresa"],
        datos["Cargo"],
        datos["Tiempo"],
        datos["Funciones"],
        id
    )

    cursor.execute(sql, valores)

    conexion.commit()

    cursor.close()
    conexion.close()

    return {
        "Mensaje": "Experiencia actualizada",
        "id": id
    }

@app.route("/api/eliminarexperiencia/<int:id>", methods=["DELETE"])
def eliminarExperiencia(id):

    conexion = conectar_bd()
    cursor = conexion.cursor()

    sql = "DELETE FROM Experiencias WHERE id = %s"

    cursor.execute(sql, (id,))

    if cursor.rowcount == 0:
        cursor.close()
        conexion.close()
        return {
            "Mensaje": "No se encontro la experiencia"
        }

    conexion.commit()

    cursor.close()
    conexion.close()

    return {
        "Mensaje": "Experiencia eliminada correctamente"
    }

@app.route("/api/consultarhabilidades/<int:id>/habilidades", methods=["GET"])
def obtenerHabilidades(id):

    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)

    sql = "SELECT * FROM Habilidades WHERE experiencia_id = %s"

    cursor.execute(sql, (id,))

    habilidades = cursor.fetchall()

    cursor.close()
    conexion.close()

    return {
        "Habilidades": habilidades
    }

@app.route("/api/registrarexperiencia/<int:id>/experiencias", methods=["POST"])
def registrarExperienciahv(id):

    datos = request.get_json()

    Empresa = datos["Empresa"]
    Cargo = datos["Cargo"]
    Tiempo = datos["Tiempo"]
    Funciones = datos["Funciones"]

    conexion = conectar_bd()
    cursor = conexion.cursor()

    sql = "INSERT INTO Experiencias (hoja_vida_id, Empresa, Cargo, Tiempo, Funciones) VALUES (%s, %s, %s, %s, %s)"

    valores = (
        id,
        Empresa,
        Cargo,
        Tiempo,
        Funciones
    )

    cursor.execute(sql, valores)
    conexion.commit()

    experiencia_id = cursor.lastrowid

    print("🔥 ID DE EXPERIENCIA CREADA:", experiencia_id)

    cursor.close()
    conexion.close()

    return {
    "Mensaje": "Experiencia registrada satisfactoriamente",
    "id": experiencia_id
}

@app.route("/api/registrarhabilidad/<int:id>/habilidades", methods=["POST"])
def registrarHabilidad(id):

    datos = request.get_json()

    Nombre = datos.get("Nombre")
    if not Nombre:
        return {
            "Mensaje": "No se recibio el nombre de la habilidad"
        }

    conexion = conectar_bd()
    cursor = conexion.cursor()

    sql = """
        INSERT INTO Habilidades (experiencia_id, Nombre)
        VALUES (%s, %s)
    """

    valores = (id, Nombre)

    cursor.execute(sql, valores)
    conexion.commit()

    habilidad_id = cursor.lastrowid

    cursor.close()
    conexion.close()

    return {
        "Mensaje": "Habilidad registrada correctamente",
        "id": habilidad_id
    }

@app.route("/api/actualizarhabilidad/<int:id>", methods=["PUT"])
def actualizarHabilidad(id):

    datos = request.get_json()

    conexion = conectar_bd()
    cursor = conexion.cursor()

    sql = "UPDATE Habilidades SET Nombre = %s WHERE id = %s"
    valores = (
        datos["Nombre"],
        id
    )

    cursor.execute(sql, valores)

    conexion.commit()

    cursor.close()
    conexion.close()

    return {
        "Mensaje": "Habilidad actualizada",
        "id": id
    }

@app.route("/api/eliminarhabilidad/<int:id>", methods=["DELETE"])
def eliminarHabilidad(id):

    conexion = conectar_bd()
    cursor = conexion.cursor()

    sql = "DELETE FROM Habilidades WHERE id = %s"

    cursor.execute(sql, (id,))

    if cursor.rowcount == 0:
        cursor.close()
        conexion.close()
        return {
            "Mensaje": "No se encontro la habilidad"
        }

    conexion.commit()

    cursor.close()
    conexion.close()

    return {
        "Mensaje": "Habilidad eliminada correctamente"
    }

@app.route("/api/consultarcursos/<int:id>/cursos", methods=["GET"])
def obtenerCursos(id):

    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)

    sql = "SELECT * FROM cursos WHERE hoja_vida_id = %s"

    cursor.execute(sql, (id,))

    cursos = cursor.fetchall()

    cursor.close()
    conexion.close()

    return {
        "Cursos": cursos
    }

@app.route("/api/registrarcurso/<int:id>/cursos", methods=["POST"])
def registrarCurso(id):

    datos = request.get_json()

    Nombre = datos["Nombre"]

    conexion = conectar_bd()
    cursor = conexion.cursor()

    sql = "INSERT INTO cursos (hoja_vida_id, Nombre) VALUES (%s, %s)"
    valores = (
        id,
        Nombre
    )

    cursor.execute(sql, valores)
    conexion.commit()

    cursor.close()
    conexion.close()

    return {
        "Mensaje": "Curso registrado correctamente"
    }

@app.route("/api/cursos/<int:id>", methods=["GET"])
def obtenerCurso(id):

    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)

    sql = "SELECT * FROM cursos WHERE id = %s"

    cursor.execute(sql, (id,))

    curso = cursor.fetchone()

    cursor.close()
    conexion.close()

    if curso:
        return {
            "Mensaje": "Curso encontrado",
            "Curso": curso
        }

    return {
        "Mensaje": "No se encontro el curso"
    }

@app.route("/api/actualizarcurso/<int:id>", methods=["PUT"])
def actualizarCurso(id):

    datos = request.get_json()

    conexion = conectar_bd()
    cursor = conexion.cursor()

    sql = "UPDATE cursos SET Nombre = %s WHERE id = %s"
    valores = (
        datos["Nombre"],
        id
    )
    cursor.execute(sql, valores)

    conexion.commit()

    cursor.close()
    conexion.close()

    return {
        "Mensaje": "Curso actualizado",
        "id": id
    }

@app.route("/api/eliminarcurso/<int:id>", methods=["DELETE"])
def eliminarCurso(id):

    conexion = conectar_bd()
    cursor = conexion.cursor()

    sql = "DELETE FROM cursos WHERE id = %s"

    cursor.execute(sql, (id,))

    if cursor.rowcount == 0:
        cursor.close()
        conexion.close()

        return {
            "Mensaje": "No se encontro el curso"
        }

    conexion.commit()

    cursor.close()
    conexion.close()

    return {
        "Mensaje": "Curso eliminado correctamente"
    }

@app.route("/api/hojadevida/<int:id>", methods=["GET"])
def consultarHojaVidaCompleta(id):

    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)

    sql = "SELECT * FROM Hojas_Vida WHERE id = %s"
    cursor.execute(sql, (id,))
    hoja_vida = cursor.fetchone()

    if not hoja_vida:
        cursor.close()
        conexion.close()
        return {
            "Mensaje": "No se encontro la hoja de vida"
        }
    
    sql = "SELECT * FROM Estudios WHERE hoja_vida_id = %s"
    cursor.execute(sql, (id,))
    estudios = cursor.fetchall()

    sql = "SELECT * FROM Cursos WHERE hoja_vida_id = %s"
    cursor.execute(sql, (id,))
    cursos = cursor.fetchall()


    sql = "SELECT * FROM Experiencias WHERE hoja_vida_id = %s"
    cursor.execute(sql, (id,))
    experiencias = cursor.fetchall()

    for experiencia in experiencias:

        sql = "SELECT * FROM Habilidades WHERE experiencia_id = %s"
        cursor.execute(sql, (experiencia["id"],))

        habilidades = cursor.fetchall()

        experiencia["Habilidades"] = habilidades

    cursor.close()
    conexion.close()

    return {
        "Datos_personales": hoja_vida,
        "Estudios": estudios,
        "Cursos": cursos,
        "Experiencias": experiencias
    }

if __name__=="__main__":
    app.run(debug=True)