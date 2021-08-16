# Compunere insert
# cursor = cursorul catre BD
# table = tabla in care inseram
# fields = numele campurilor inserate
# values = valorile pe care le inseram
# msgToAdd = mesajul de eroare returnat 
def insertData(cursor, table, fields, values, msgToAdd):

    insertString = "INSERT INTO " + table + " ("
    insertString += ','.join(fields)
    insertString +=  ')'

    insertString += ' VALUES('
    insertString += ','.join(['?' for item in fields])
    insertString +=  ')'
    
    try:
        cursor.execute(insertString, values)
        cursor.commit()
    except:
        return msgToAdd

    return ''

# Compunere update
# cursor = cursorul catre BD
# table = tabla in care inseram
# fields = numele campurilor inserate
# values = valorile pe care le inseram
# indexName = ID-ul pentru care are loc update-ul
# msgToAdd = mesajul de eroare returnat 
# ID-ul este ultimul camp din VALUES
def updateData(cursor, table, fields, values, indexName, msgToAdd):

    updateString = 'UPDATE ' + table + ' SET '
    updateString += ' = ?, '.join(fields)
    updateString += ' = ?'
    updateString += ' WHERE ' 
    updateString += ' = ? AND '.join(indexName)
    updateString += ' = ?'

    # print(updateString)
    try:
        cursor.execute(updateString, values)
        cursor.commit()
    except:
        return msgToAdd

    return ''

# Returnare ID 
# cursor = cursorul catre BD
# table = tabla in care inseram
# fields = numele campurilor inserate
# values = valorile pe care le inseram
# indexName = ID-ul pentru care are loc update-ul

def getID(cursor, table, indexName, fields, values):

    queryString = "SELECT " +  indexName + " FROM " + table + " WHERE "
    queryString += '= ? AND '.join(fields)
    queryString += ' = ?'

    try:
        cursor.execute(queryString, values)
        ID = cursor.fetchone()
        ID = ID[0]
       
    except:
        ID = 0

    return ID

