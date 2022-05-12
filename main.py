import sqlite3
from berzus import calc
from thefuzz import fuzz
from datetime import datetime
from flask import Flask, jsonify, request


app = Flask(__name__)

def db_connection():
    conn = None
    try:
        conn = sqlite3.connect('zelle_ops.sqlite')
    except sqlite3.Error as e:
        print(e)
    return conn

#Listar registros
@app.route('/depositos')
def depositos_list():
    try:
        conn = db_connection()
        cursor = conn.cursor()
        sql = "SELECT * FROM depositos"
        cursor.execute(sql)
        datos = cursor.fetchall()
        depositos = []
        for fila in datos:
            deposito = { 
                'msg_id':fila[0], 
                'cuenta':fila[1], 
                'banco':fila[2], 
                'fecha':fila[3],
                'hora':fila[4], 
                'remitente':fila[5], 
                'monto':fila[6],
                'cobro':fila[7]
            }
            depositos.append(deposito)
        return jsonify({'depositos':depositos})
    except Exception as e:
        return jsonify({'mensaje':'error'})

#Ver registro único
@app.route('/depositos/<msg_id>', methods=['GET'])
def depositos_get(msg_id):
    try:
        conn = db_connection()
        cursor = conn.cursor()
        sql = "SELECT * FROM depositos WHERE msg_id = '{0}'".format(msg_id)
        cursor.execute(sql)
        datos = cursor.fetchone()
        if datos != None:
            deposito = {
                'msg_id':datos[0], 
                'cuenta':datos[1], 
                'banco':datos[2], 
                'fecha':datos[3],
                'hora':datos[4], 
                'remitente':datos[5], 
                'monto':datos[6],
                'cobro':datos[7]
            }
            return jsonify({'deposito':deposito})
        else:
            return jsonify({'mensaje': 'Depósito no encontrado'})
    except Exception as e:
        return jsonify({'mensaje':'error'})

#Encontrar match
@app.route('/match')
def depositos_match():
    remitente = str(request.args.get('remitente'))
    monto = float(request.args.get('monto'))
    fecha = str(reques.args.get('monto'))
    try:
        conn = db_connection()
        cursor = conn.cursor()
        sql = "SELECT * FROM depositos WHERE cobro is FALSE".format(remitente,monto)
        cursor.execute(sql)
        datos = cursor.fetchall()
        #Crear lista iterable con depósitos no cobrados
        depositos = []
        for fila in datos:
            deposito = {
                'msg_id':fila[0], 
                'cuenta':fila[1], 
                'banco':fila[2], 
                'fecha':fila[3],
                'hora':fila[4], 
                'remitente':fila[5], 
                'monto':fila[6],
                'cobro':fila[7]
            }
            depositos.append(deposito)

        #Iterar sobre lista buscando coincidencia de nombre y monto
        counter = 0
        for r in depositos:
                #Preparar nombres
                bank_name = str(r['remitente'])
                desk_name = remitente
                #Separar nombres
                bank_name_ls = bank_name.split(' ')
                desk_name_ls = remitente.split(' ')
                #Reordenar si el nombre tiene más de 4 elementos
                if len(str(r['remitente']).split(' ')) >= 4:
                    bank_name = str(bank_name_ls[0])+' '+str(bank_name_ls[2]+' '+str(bank_name_ls[3]))
                    bank_name2 = str(bank_name_ls[0])+' '+str(bank_name_ls[1]+' '+str(bank_name_ls[2]))
                else:
                    bank_name2 = bank_name
                if len(desk_name_ls) >= 4:
                    desk_name = str(desk_name_ls[0])+' '+str(desk_name_ls[2]+' '+str(desk_name_ls[3]))
                    desk_name2 = str(desk_name_ls[0])+' '+str(desk_name_ls[1]+' '+str(desk_name_ls[2]))
                else:
                    desk_name2 = desk_name
                #Parametros de comparación    
                counter+=1
                monto_depositos = float(r['monto'])
                discrepancia = abs((monto-monto_depositos)/monto)
                cascada = calc(monto).tolerance()
                
                if  fuzz.ratio(str(bank_name),str(desk_name))>=69 and r['fecha'] == fecha and discrepancia < cascada and r['cobro']==False:
                    sql = "UPDATE depositos SET cobro = {0} WHERE msg_id = '{1}'".format(True, r['msg_id'])
                    cursor.execute(sql)
                    conn.commit()
                    return jsonify({'mensaje':'Transacción encontrada', 'codigo': '200'},{'datos':r})
                elif fuzz.ratio(str(bank_name2),str(desk_name))>=69 and r['fecha'] == fecha and discrepancia < cascada and r['cobro']==False:
                    sql = "UPDATE depositos SET cobro = {0} WHERE msg_id = '{1}'".format(True, r['msg_id'])
                    cursor.execute(sql)
                    conn.commit()
                    return jsonify({'mensaje':'Transacción encontrada', 'codigo': '200'},{'datos':r})
                elif fuzz.ratio(str(bank_name),str(desk_name2))>=69  and r['fecha'] == fecha and discrepancia < cascada and r['cobro']==False:
                    sql = "UPDATE depositos SET cobro = {0} WHERE msg_id = '{1}'".format(True, r['msg_id'])
                    cursor.execute(sql)
                    conn.commit()
                    return jsonify({'mensaje':'Transacción encontrada', 'codigo': '200'},{'datos':r})
                elif fuzz.ratio(str(bank_name2),str(desk_name2))>=69  and r['fecha'] == fecha and discrepancia < cascada and r['cobro']==False:
                    sql = "UPDATE depositos SET cobro = {0} WHERE msg_id = '{1}'".format(True, r['msg_id'])
                    cursor.execute(sql)
                    conn.commit()
                    return jsonify({'mensaje':'Transacción encontrada', 'codigo': '200'},{'datos':r})
                elif counter == len(depositos):
                    return jsonify({'mensaje': 'Transacción no existe', 'codigo': '204'})
        return jsonify({'depositos':depositos})
    except Exception as e:
        return jsonify({'mensaje':'error'})



#Insertar registro
@app.route('/depositos', methods=['POST'])
def depositos_add():
    try:
        conn = db_connection()
        cursor = conn.cursor()
        sql = """
        INSERT INTO depositos 
        VALUES ('{0}','{1}','{2}','{3}','{4}','{5}', {6}, {7})
        """.format(request.json['msg_id'],
        request.json['cuenta'],
        request.json['banco'],
        request.json['fecha'],
        request.json['hora'],
        request.json['remitente'],
        request.json['monto'],
        False)
        cursor.execute(sql)
        conn.commit()
        return jsonify({'mensaje':'Depósito registrado'}), 201
    except Exception as e:
        return jsonify({'mensaje': 'error'}), 200

#Modificar registro
@app.route('/depositos/<msg_id>', methods=['PUT'])
def depositos_modify(msg_id):
    try:
        conn = db_connection()
        cursor = conn.cursor()
        sql = """
        UPDATE depositos SET cuenta='{0}', banco='{1}', fecha='{2}', 
        hora='{3}', remitente='{4}', monto='{5}', cobro={6} WHERE msg_id='{7}')
        """.format(request.json['cuenta'],
        request.json['banco'],
        request.json['fecha'],
        request.json['hora'],
        request.json['remitente'],
        request.json['monto'],
        request.json['cobro'],
        msg_id)

        cursor.execute(sql)
        conn.commit()
        return jsonify({'mensaje':'Registro modificado'}), 201
    except Exception as e:
        return jsonify({'mensaje': 'error'}), 200


#Eliminar registro
@app.route('/depositos/<id>', methods=['DELETE'])
def depositos_delete(id):
    try:
        conn = db_connection()
        cursor = conn.cursor()
        sql = "DELETE FROM depositos WHERE id = '{0}'".format(id)
        cursor.execute(sql)
        conn.commit()
        return jsonify({'mensaje':'Registro eliminado'})
    except Exception as e:
        return jsonify({'mensaje': 'error'})

def pagina_no_encontrada(error):
    return jsonify({'mensaje':'Lo que estabas buscando no existe...'})


if __name__ == "__main__":
    app.register_error_handler(404, pagina_no_encontrada)
    app.run(debug=True)
