from flask import Flask, render_template, request, redirect, make_response, url_for, session, flash
import pyodbc
from sendMail import sendEmail, generateSecretKey
from formatData import checkFormData, formatLineToDict, checkPassword, checkPhone, formatToListOfDict
from formatData import datetimeToDate, returnListFormData, splitZones, blankPadding, scrambled
from datetime import datetime
from handle import checkLoggedReturnUserID
from hashutils import make_pw_hash
from querryTools import insertData, getID, updateData
import os

# Variabile globale 

secretKeySent = "Codul de siguranta a fost trimis la adresa de email"
incorrectSecretKey = "Codul secret este incorect"
passwordMismatch = 'Parolele nu corespund'
passwordMustContain = """Parola trebuie sa contina cel putin un caracter special, o litera mare,
                         una mica si o cifra, iar lungimea sa fie mai mare ca 8"""
invalidEmailUser = 'Adresa de email sau numele de utilizator este deja utilizat'
incorrectUsernamePassword = 'Parola sau Nume de utilizator gresit'

userClientData = ['UtilizatorID', 'NumeUtilizator', 'pw', 'Email', 
    'admin', 'DataInscriere', 'ClientID', 'u_id', 'Nume', 'Prenume', 'Telefon', 'Adresa']
headerUserClient = ['UtilizatorID', 'ClientID', 'NumeUtilizator',  'Nume', 'Prenume', 'Email',
    'Telefon', 'Adresa', 'DataInscriere', 'Stergere']

productFields = ['Denumire', 'Greutate', 'Memorie_interna', 'Stoc', 'Pret', 'Sep', 'Categorie', 'Sep', 'Frecventa',
    'Capacitate', 'Tip_memorie', 'Sep', 'Producator', 'Model', 'Arhitectura', 'Numar_nuclee', 'Frecventa_procesor', 'Cache',
    'Sep',  'Diagonala', 'Format', 'Tehnologie_display', 'Rata_refresh', 'Rezolutie', 'Sep', 'Producator_placa_video',
    'Model_placa_video', 'Memorie_grafica', 'Tip_memorie_grafica']

productFieldsOrder = ['produsID', 'categorieID', 'memorieID', 'procesorID', 'afisareID', 'placaVideoID', 'Denumire', 
    'Greutate', 'Memorie_interna', 'Stoc', 'Pret', 'Imagine', 'Sep', 'Categorie', 'Sep', 'Frecventa', 'Capacitate', 'Tip_memorie',
    'Sep', 'Producator', 'Model', 'Arhitectura', 'Numar_nuclee', 'Frecventa_procesor', 'Cache', 'Sep','Diagonala', 'Format', 'Tehnologie_display',
    'Rata_refresh', 'Rezolutie', 'Sep', 'Producator_placa_video', 'Model_placa_video', 'Memorie_grafica', 'Tip_memorie_grafica']

unitOfMeasure = {'Greutate':'Kg', 'Memorie_interna':'Gb', 'Stoc':'buc', 'Pret':'RON', 'Frecventa':'MHz', 'Capacitate':'Gb',
     'Frecventa_procesor':'MHz', 'Cache':'Kb', 'Diagonala':'inch', 'Rata_refresh':'Hz',  'Memorie_grafica':'Gb'}

productZones = ['Categorie', 'Memorie', 'Procesor', 'Display', 'Placa video']
productZones.reverse() # Le prelucram in ordine inversa in HTML
product = []

# Mesaje 
msgProductAdded = ''
msgProductUpdated = ''
msgBuy = ''
ENV = 'dev'
app = Flask(__name__,template_folder='templates', static_folder='static')

app.config["IMAGE_UPLOADS"] = os.path.join(os.path.join(os.getcwd(),'static'), 'images')
# app.config["IMAGE_UPLOADS"] = os.path.join(os.getcwd(),'images')

# Conexiune cu baza de date
conn = pyodbc.connect(
    "Driver={SQL Server Native Client 11.0};"
    "Server=DESKTOP-21OV0R0\SQLEXPRESS;"
    "Database=Comercializare;"
    "Trusted_Connection=yes;"
)

sKey = ''
app.config['SECRET_KEY'] = 'Thisissupposedtobesecret!'

if ENV == 'dev':
    app.debug = True
else:
    pass

# Pagina de start
@app.route('/')
def index(): 
    if 'logged' in session:
        if session['logged'] == True:
            return redirect('/front_page')
        else: return redirect('/login')
    else:
        return redirect('/login')

# Pagina de login
@app.route('/login', methods = ['POST', 'GET'])
def redirectLogin():
    global incorrectUsernamePassword
    
    if(request.method == 'GET'):
        return render_template('login.html')
    else:
        username = checkFormData('username', request)
        password = checkFormData('password', request)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Utilizatori WHERE utilizator = ? AND parola = ? ", (username, make_pw_hash(password)))
        user = cursor.fetchone()
        cursor.close()
        # Setare date sesiune
        if user != None:
            session['userID'] = user[0]
            session['logged'] = True
            session['admin'] = user[4]
            session['username'] = user[1]
            return redirect('/front_page')
        return render_template('login.html', msg =  incorrectUsernamePassword)

@app.route('/register', methods = ['POST', 'GET'])
def register():

    global sKey, incorrectSecretKey, passwordMismatch, secretKeySent
    global invalidEmailUser, passwordMustContain

    if request.method == 'GET':
        return render_template('register.html', data = {})
    else:
        # Preluare date formular
        username = checkFormData('username', request)
        email = checkFormData('email', request)
        password = checkFormData('password', request)
        cpassword = checkFormData('cpassword', request)
        secretKey = checkFormData('secretKey', request)

        # Verificare corespondenta parole
        if(password != cpassword):
            return render_template('register.html', msg = passwordMismatch)

        # Verificare unicitate username
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Utilizatori WHERE utilizator = ?', username)
        utilizatorGasit = cursor.fetchone()

        # Verificare unicitate email
        cursor.execute('SELECT * FROM Utilizatori WHERE email = ?', email)
        mailGasit = cursor.fetchone()
        
        # email si username unic
        if(mailGasit == None and utilizatorGasit == None):

            # Verificare corectitudine parola
            if not checkPassword(password):
                return render_template( 'register.html',msg = passwordMustContain)
            
            dictFormat = ['username', 'email', 'password', 'cpassword', 'secretKey']
            dataToFormat = [username, email, password, cpassword, secretKey]
            data = formatLineToDict(dataToFormat, dictFormat)
            
            
            if(len(secretKey) == 0):
                # Generare cheie secreta si trimitere email
                sKey = generateSecretKey()
                print(sKey)
                sendEmail(sKey, email)
                return render_template('register.html', data = data, msg = secretKeySent)
            else:
                # Verificare corespondeta cheie secreta
                if(str(sKey) == secretKey):
                    cursor.execute("""INSERT INTO Utilizatori(utilizator, email, parola, dataCreare)
                     VALUES(?, ?, ?, GETDATE())""", [username, email, make_pw_hash(password)])
                    cursor.commit()
                    cursor.close()
                    return redirect('/')
                else:
                    return render_template('register.html', data = data, msg = incorrectSecretKey )
        else:
            return render_template('register.html', msg = invalidEmailUser)


@app.route('/front_page', methods = ['POST', 'GET'])
def loginSucces():
    if checkLoggedReturnUserID(session) != -1:
        global productFieldsOrder
        # Extragere date produse
        cursor = conn.cursor()
        cursor.execute("""SELECT * FROM Produs """)
        qData = cursor.fetchall()
        allFields = formatToListOfDict(qData, productFieldsOrder[0:12])
        
        # Schimbare ordine produse
        allFields = scrambled(allFields)
        
        return render_template('home.html', session = session, data = allFields, header = productFieldsOrder)
    else:
        return redirect('/login')

@app.route('/detalii_produs<id>')
def productDetails(id):
    
    global productFields
    cursor = conn.cursor()
    # JOIN
    
    # Extragere detalii produs
    cursor.execute("""SELECT * FROM Produs AS P, Categorie AS C, Memorie AS M, Procesor AS Pr, Afisare AS A, 
        Placavideo AS Pv WHERE P.categorieID = C.categorieID AND P.memorieID = M.memorieID AND P.procesorID = Pr.procesorID
        AND P.afisareID = A.afisareID AND P.placaVideoID = PV.placaVideoID AND P.produsID = ?""", id)
    qData = cursor.fetchall()
    # Formatare date produs
    allFields = formatToListOfDict(qData, productFieldsOrder)
    return render_template('productDetails.html', data = allFields, header = productFields[1:], zones = productZones,
        unit = unitOfMeasure)

@app.route('/profile')
def getProfile():
    global msgBuy
    msgProfile = msgBuy
    # Verificare user conectat
    if 'logged' in session:
        if session['logged']:
            data = {}
            
            # JOIN + SUBCERERE
            cursor = conn.cursor()
            cursor.execute("""SELECT * FROM Clienti AS C, Utilizatori AS Ut WHERE C.utilizatorID = 
                (SELECT U.utilizatorID FROM Utilizatori AS U WHERE U.utilizatorID = ? ) 
                AND C.utilizatorID = Ut.utilizatorID""", session['userID'])
            clientData = cursor.fetchone()
            
            
            if clientData == None:
                data['firstname'] = ''
                data['lastname'] = ''
                data['address'] = ''
                data['phone'] = ''
                # Extragere nume utilizator in cazu' in care cererea de mai sus nu a returnat date valide pentru
                # ca utilizatoru' nu a completat si datele de client inca
                cursor.execute("""SELECT U.utilizator FROM Utilizatori AS U WHERE U.utilizatorID = ?""", session['userID'])
                userData = cursor.fetchone()
                data['username'] = userData[0]
            else:
                data['firstname'] = clientData[3]
                data['lastname'] = clientData[2]
                data['address'] = clientData[5]
                data['phone'] = clientData[4]
                data['username'] = clientData[7]
            cursor.close()
            # Verificam daca nr de telefon introdus este unic
            if 'phoneNotUnique' in session:
                
                if session['phoneNotUnique'] == True:
                    session['phoneNotUnique'] = False
                    msgProfile += '</br>Numarul de telefon este atribuit unui client existent!'
                    
            # Veridicam daca numele de utilizator este unic
            if 'usernameTaken' in session:
                
                if session['usernameTaken'] == True:
                    session['usernameTaken'] = False
                    msgProfile += '</br>Numele de utilizator este atribuit unui alt utilizator!'
                    
            msgBuy = ''
            return render_template('clientProfile.html', data = data, msg = msgProfile)
    else:
        return redirect('/')

@app.route('/redirectProfile', methods = ['POST'])
def modifyData():
    
    redirectProfile = False

    cursor = conn.cursor()
    
    # Preluare date client
    cursor.execute('SELECT * FROM Clienti WHERE utilizatorID = ?', session['userID'])
    clientData = cursor.fetchone()

    # Clientul nu avea datele trecute
    username = checkFormData('username', request)
    lastname = checkFormData('lastname', request)
    firstname = checkFormData('firstname', request)
    phone = checkFormData('phone', request)
    address = checkFormData('address', request)
    # Verificare date
    if not checkPhone(phone):
        return redirect('/profile')

    # Verificare unicitate username
    cursor.execute("""SELECT utilizatorID FROM Utilizatori WHERE utilizator = ?""", username)
    userID = cursor.fetchall()
    
    # Setare flag nume utilizator nu e unic
    if userID[0][0] != session['userID']:
        session['usernameTaken'] = True
        redirectProfile = True
    else:
        session['usernameTaken'] = False
        

    # Verificare unicitate nr de telefon
    if clientData != None:
        cursor.execute("SELECT * FROM Clienti WHERE telefon like ? AND clientID NOT LIKE ?", [phone, clientData[0]]);
        checkUniquePhone = cursor.fetchone();
        # Setare flag numar de telefon nu este unic
        if checkUniquePhone != None:
            session['phoneNotUnique'] = True
            redirectProfile = True
    
    if redirectProfile:
        return redirect('/profile')
    # Daca clientul nu avea date in BD le adaugam, daca nu le updatam
    if clientData == None:
        cursor.execute("""INSERT INTO Clienti(utilizatorID, nume, prenume, telefon, adresa)
        VALUES(?, ?, ?, ?, ?)""", [session['userID'], lastname, firstname, phone, address ])
        cursor.commit()
    else:
        cursor.execute("""UPDATE Clienti SET nume = ?, prenume = ?, telefon = ?, adresa = ?
        WHERE utilizatorID = ?""" , [lastname, firstname, phone, address, session['userID'] ])
        cursor.execute("""UPDATE Utilizatori SET utilizator = ? WHERE utilizatorID = ?""",
        [username, session['userID']])

        cursor.commit()
    return redirect('/profile')

@app.route('/manage_users')
def manageUsers():
    global userClientData
    if 'admin' in session:
        if session['admin'] == True:
            cursor = conn.cursor()
            # JOIN
            # Extragere date utilizator + client
            cursor.execute("""SELECT * FROM Utilizatori as U LEFT JOIN Clienti as C ON 
            U.utilizatorID = C.utilizatorID WHERE U.utilizatorID != ?""", session['userID'])
            userClient = cursor.fetchall()
            
            userClient = formatToListOfDict(userClient, userClientData)

            userClient = datetimeToDate(userClient, 'DataInscriere')
            return render_template('manage_users.html', data = userClient, header = headerUserClient)
    return redirect('/front_page')

@app.route('/delete_user<id>')
def deleteUser(id):
    
    # Stergere utilizator
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Utilizatori WHERE utilizatorID = ?", int(id))
    cursor.commit()
    return redirect('/manage_users')

@app.route('/manage_products')
def manageProducts():
    global productFieldsOrder
    # Verificare rol
    if 'admin' in session:
        if session['admin'] == True:
            
            # Extragere date produs
            cursor = conn.cursor()
            cursor.execute("""SELECT * FROM Produs""")
            productData = cursor.fetchall()
            productData = formatToListOfDict(productData, productFieldsOrder[0:11])
            
            filedsToUse = productFieldsOrder[0:11] + ['Updatare', 'Stergere']
            return render_template('manageProducts.html', data = productData, header = filedsToUse)
    
    return redirect('/front_page')

@app.route('/delete_product<id>')
def deleteProducts(id):
    # Verificare rol
    if 'admin' in session:
        if session['admin'] == True:
            # Stergere produs
            cursor = conn.cursor()
            cursor.execute("""DELETE FROM Produs WHERE produsID = ?""", id)
            cursor.commit()
            cursor.close()
            return redirect('/manage_products')
    return redirect('/front_page')

@app.route('/update_produs<id>', methods = ['POST', 'GET'])
def updateProduct(id):
    global productFields
    global msgProductUpdated
    # Verificare rol
    if 'admin' in session:
        if session['admin'] == True:  
            if request.method == 'GET':
                
                cursor = conn.cursor()
                # JOIN
                # Extragere detalii produs
                cursor.execute("""SELECT * FROM Produs AS P, Categorie AS C, Memorie AS M, Procesor AS Pr, Afisare AS A, 
                    Placavideo AS Pv WHERE P.categorieID = C.categorieID AND P.memorieID = M.memorieID AND P.procesorID = Pr.procesorID
                    AND P.afisareID = A.afisareID AND P.placaVideoID = PV.placaVideoID AND P.produsID = ?""", id)
                qData = cursor.fetchall()
                # Formatare date
                allFields = formatToListOfDict(qData, productFieldsOrder)
                
                localMsg = msgProductUpdated
                msgProductUpdated = ''
                return render_template('updateProduct.html', data = allFields[0], header = productFields,
                    zones = productZones, msg = localMsg)
            else:
                # Verificam daca o noua imagine a fost adaugata
                image = False
                if request.files:
                    image = request.files["image"]
                    pathToFile = image.filename
                    if pathToFile:
                        image.save(os.path.join(app.config["IMAGE_UPLOADS"], pathToFile))
                        image = pathToFile
            
                msgProductUpdated = None
                product = returnListFormData(productFields, request)
                [zonesList, row] = splitZones(product)

                # Order: date generale, categorie, memorie, procesor, display

                # Verificare unicitate produs
                cursor = conn.cursor()
                cursor.execute(""" SELECT * FROM Produs WHERE denumire = ? AND produsID != ?""", zonesList[0][0], id)
                productNameFound = cursor.fetchone()
                
                if productNameFound == None:
                    msgProductUpdated = ''
                else:
                    msgProductUpdated = '<br>Un produs cu aceasta denumire se afla deja in baza de date!'
                    return redirect('/update_produs' + id)
                

                # Inserare date + preluare ID pentru updatarea in cadrul produsului
                # Pentru datele legate de specificatii se incearca un insert pentru ca unicitatea
                # este setata per ansamblu' in cadrul acestora nu pe un camp in parte

                msgProductUpdated += insertData(cursor, 'Categorie', ['numeCategorie'], zonesList[1],
                    '<br>Categoria exista deja, nu am modificat nimic')
               
                categoryID = getID(cursor, 'Categorie', 'categorieID', ['numeCategorie'], zonesList[1][0])
                if not categoryID:
                    msgProductUpdated = 'Verificati datele despre categorie'
                    return redirect('/update_produs' + id)
                
                
                msgProductUpdated += insertData(cursor, 'Memorie', ['frecventa', 'capacitate', 'tip_memorie'],
                     zonesList[2], '<br>Memoria exista deja in baza de date, nu am modificat nimic')

                memoryID = getID(cursor, 'Memorie', 'memorieID', ['frecventa', 'capacitate',
                    'tip_memorie'], zonesList[2])
                if not memoryID:
                    msgProductUpdated = 'Verificati datele despre memorie'
                    return redirect('/update_produs' + id)

                msgProductUpdated += insertData(cursor, 'Procesor', ['producator', 'model', 'arhitectura', 'nr_nuclee',
                    'frecventa', 'cache'], zonesList[3], '<br>Modelul de procesor se alfa in baza de date, nu am modificat nimic')
                
                procesorID = getID(cursor, 'Procesor', 'procesorID', ['producator', 'model', 'arhitectura', 'nr_nuclee',
                    'frecventa', 'cache'], zonesList[3])
                if not procesorID:
                    msgProductUpdated = 'Verificati datele despre procesor'
                    return redirect('/update_produs' + id)

                msgProductUpdated += insertData(cursor, 'Afisare', ['diagonala', 'format', 'tehnologie_display', 'rata_refresh',
                    'rezolutie'], zonesList[4], '<br>Modelul de display se alfa in baza de date, nu am modificat nimic')

                displayID = getID(cursor, 'Afisare', 'afisareID', ['diagonala', 'format', 'tehnologie_display', 'rata_refresh',
                    'rezolutie'], zonesList[4])
                if not displayID:
                    msgProductUpdated = 'Verificati datele despre display'
                    return redirect('/update_produs' + id)

            
                msgProductUpdated += insertData(cursor, 'Placavideo', ['producator', 'model', 'memorie', 'tip_memorie'],
                    zonesList[5], '<br>Modelul de placa video se alfa in baza de date, nu am modificat nimic')

                videoCardID = getID(cursor, 'Placavideo', 'placaVideoID', ['producator', 'model', 'memorie', 'tip_memorie'],
                    zonesList[5])
                if not videoCardID:
                    msgProductUpdated = 'Verificati datele despre placa video'
                    return redirect('/update_produs' + id)
                
                # Verificam daca administratorul a introdus o poza noua pentru produsul respectiv
                if image:
                    productData = [categoryID, memoryID, procesorID, displayID, videoCardID, image] + zonesList[0] + [id]
                    msgProductUpdated = updateData(cursor, 'Produs', ['categorieID', 'memorieID', 'procesorID', 'afisareID',
                        'placaVideoID', 'cale_imagine', 'denumire', 'greutate', 'memorie_interna', 'stoc', 'pret' ],
                        productData, ['produsID'], '<br>Eroare la updatare!')
                else:
                    productData = [categoryID, memoryID, procesorID, displayID, videoCardID] + zonesList[0] + [id]
                    msgProductUpdated += updateData(cursor, 'Produs', ['categorieID', 'memorieID', 'procesorID', 'afisareID',
                        'placaVideoID', 'denumire', 'greutate', 'memorie_interna', 'stoc', 'pret' ],
                        productData, ['produsID'], '<br>Eroare la updatare!')
                
                return redirect('/update_produs' + id)

    return redirect('/front_page')

@app.route('/cumpara_produs<id>')
def buyProduct(id):
    global msgBuy
    if checkLoggedReturnUserID(session):
        
        # Etapa 1: Verificare integritate date client
        cursor = conn.cursor()
        cursor.execute("""SELECT clientID FROM Clienti WHERE utilizatorID = ?""", session['userID'])
        clientID = cursor.fetchone()
        if clientID == None:
            msgBuy = 'Completati datele aferente profilului de client!'
            return redirect('/profile')

        # Etapa 2: Updatare stoc
        cursor.execute("""SELECT Stoc FROM Produs WHERE produsID = ?""", id)
        stock = cursor.fetchone()
        stock = stock[0]
        updateData(cursor, 'Produs', ['Stoc'], [stock - 1, id], ['produsID'], '')

        # Etapa 3: Verificare cantitate 
        # SUBCERERE
        cursor.execute("""SELECT CP.cantitate FROM ClientiProdus AS CP WHERE clientID = 
             (SELECT C.clientID FROM Clienti as C WHERE C.utilizatorID = ? )
             AND produsID = ?""", session['userID'], id)
        quantity = cursor.fetchone()
        print(quantity)
        if quantity != None:
            quantity = quantity[0]
        else:
            quantity = 0
        
        # Etapa 4: Adaugare date in tabela clientiProdus
        if not quantity:
            insertData(cursor, 'ClientiProdus', ['clientID', 'produsID', 'dataVanzare', 'cantitate'],
                [clientID[0], id, datetime.today(), 1], '')
        else:
            quantity = quantity + 1
            updateData(cursor, 'ClientiProdus', ['dataVanzare', 'cantitate'],
                [datetime.today(), quantity, clientID[0], id], ['clientID', 'produsID'], '')

    return redirect('/detalii_produs' + id)

@app.route('/achizitii')
def boughtProducts():

    if checkLoggedReturnUserID(session):
        
        msg = ''
        
        # Etapa 1: Verificare integritate date client
        cursor = conn.cursor()
        cursor.execute("""SELECT clientID FROM Clienti WHERE utilizatorID = ?""", session['userID'])
        clientID = cursor.fetchone()
        if clientID == None:
            msg = 'Nu ati cumparat produse!'
            return render_template('productsBought.html', msg = msg)
        clientID = clientID[0]

        # Etapa 2: Selectare produse cumparate
        
        # JOIN
        cursor.execute("""SELECT * FROM Produs AS P, ClientiProdus AS CP 
            WHERE P.produsID = CP.produsID AND clientID = ?""", clientID)
        
        boughtProducts = cursor.fetchall()
        
        fields = productFieldsOrder[0:12] + ['blank_1', 'blank_2', 'blank_3', 'Cumparate']
        boughtProducts = formatToListOfDict(boughtProducts, fields)
        
        cursor.close()
        return render_template('productsBought.html', msg = msg, data = boughtProducts)

@app.route('/needing_restock')
def needingRestock():
    global productFieldsOrder

    if 'admin' in session:
        if session['admin'] == True:
            
            # SUBCERERE
            cursor = conn.cursor()
            cursor.execute("""SELECT * FROM Produs AS P WHERE 5 * P.Stoc <= (SELECT
                AVG(PP.Stoc) FROM Produs AS PP WHERE PP.Stoc > 0)""")
            needRestock = cursor.fetchall()
            needRestock = formatToListOfDict(needRestock, productFieldsOrder[0:12]) 
            
            cursor.close()
            return render_template('needingRestock.html', data = needRestock)
            
    return redirect('/')

@app.route('/statistici')
def statistics():
    global productFieldsOrder
    if checkLoggedReturnUserID(session) != -1:
        
        # Cel(e) mai vandut(e) produs(e) all time
        # SUBCERERE
        cursor = conn.cursor()
        cursor.execute("""SELECT * FROM Produs AS P WHERE (SELECT SUM(CP.cantitate) FROM ClientiProdus AS CP
            WHERE P.produsID = CP.produsID GROUP BY CP.produsID ) = (SELECT TOP 1 SUM(CP.cantitate)
            FROM ClientiProdus AS CP GROUP BY CP.produsID ORDER BY SUM(CP.cantitate) DESC) """)
        mostSoldEver = cursor.fetchall()
        mostSoldEver = formatToListOfDict(mostSoldEver, productFieldsOrder[0:12])
        # Cel(e) mai vandut(e) produse(e) de pe stoc
        # SUBCERERE
        cursor.execute("""SELECT * FROM Produs AS P WHERE (SELECT SUM(CP.cantitate) FROM ClientiProdus AS CP
            WHERE P.produsID = CP.produsID GROUP BY CP.produsID ) = (SELECT TOP 1 SUM(CP.cantitate)
            FROM ClientiProdus AS CP WHERE P.stoc != 0 GROUP BY CP.produsID ORDER BY SUM(CP.cantitate) DESC)""")
        mostSoldOnStock = cursor.fetchall()
        mostSoldOnStock = formatToListOfDict(mostSoldOnStock, productFieldsOrder[0:12])

        data = [mostSoldEver, mostSoldOnStock]
        zones = ['', '']
        # In functie de nr de produse ce respecta cerinta setam mesajul din interfata
        if len(mostSoldEver) > 1:
            zones[0] = 'Cele mai vandute produse'
        else:
            zones[0] = 'Cel mai vandut produs'
        
        if len(mostSoldOnStock) > 1:
            zones[1] = 'Cele mai vandute produse ce sunt pe stoc'
        else:
            zones[1] = 'Cel mai vandut produs ce este pe stoc'

        cursor.close()

        return render_template('statistics.html', data = data, zones = zones)

    return redirect('/')

@app.route('/adaugare_produse', methods = ['POST', 'GET'])
def addProduct():
    global productFields
    global msgProductAdded
    global product

    if 'admin' in session:
        if session['admin'] == True:
            if request.method == 'GET':
                
                try:
                    if msgProductAdded:
                        msgProductAdded = msgProductAdded
                except:
                    msgProductAdded = None
                # Bordare cu blank-uri
                product = blankPadding(product, len(productFields))
                fields = zip(productFields, product)
                return render_template('addProduct.html', fields = fields, zones = productZones,
                     msg = msgProductAdded)
            else:
                
                msgProductAdded = None
                product = returnListFormData(productFields, request)
                [zonesList, row] = splitZones(product)

                # Order: date generale, categorie, memorie, procesor, display
                # print(zonesList)
                cursor = conn.cursor()
                
                # Verificare unicitate denumire produs
                cursor.execute(""" SELECT * FROM Produs WHERE denumire = ?""", zonesList[0][0])
                productNameFound = cursor.fetchone()
                # print(productNameFound)
                if productNameFound == None:
                    msgProductAdded = ''
                else:
                    msgProductAdded = '<br>Un produs cu aceasta denumire se afla deja in baza de date!'
                    return redirect('/adaugare_produse')
                
                # Adaugare cale imagine :)
                # Nu se afla in header-ul modificabil pentru ca ar complica putin lucrurile :)
                image = request.files["image"]
                pathToFile = image.filename
                image.save(os.path.join(app.config["IMAGE_UPLOADS"], pathToFile))
                image = pathToFile
                # Adaugare date in fiecare tabela corelata cu produsul si extragerea indexului elementului
                # corespunzator din acea tabela, daca se incearca introducerea unui set de date ce nu este
                # valid, adica componentele non-unique sunt diferite, dar cea unique se afla deja in tabela
                # atunci utilizatorul o sa fie avertizat ca nu a introdus corect datele pentru zona respectiva,
                # ramane ca acesta sa-si dea seama de ce apare acea eroare, avand ca si posibilitati:
                #   1. Datele numerice sunt introduse gresit
                #   2. Pentru un camp de tipul UNIQUE constrangerile n-au fost respectate
                
                msgProductAdded += insertData(cursor, 'Categorie', ['numeCategorie'], zonesList[1],
                    '<br>Categoria exista deja, nu am modificat nimic')
               
                categoryID = getID(cursor, 'Categorie', 'categorieID', ['numeCategorie'], zonesList[1][0])
                if not categoryID:
                    msgProductAdded = 'Verificati datele despre categorie'
                    return redirect('/adaugare_produse')
                
                
                msgProductAdded += insertData(cursor, 'Memorie', ['frecventa', 'capacitate', 'tip_memorie'],
                     zonesList[2], '<br>Memoria exista deja in baza de date, nu am modificat nimic')

                memoryID = getID(cursor, 'Memorie', 'memorieID', ['frecventa', 'capacitate',
                    'tip_memorie'], zonesList[2])
                if not memoryID:
                    msgProductAdded = 'Verificati datele despre memorie'
                    return redirect('/adaugare_produse')

                msgProductAdded += insertData(cursor, 'Procesor', ['producator', 'model', 'arhitectura', 'nr_nuclee',
                    'frecventa', 'cache'], zonesList[3], '<br>Modelul de procesor se alfa in baza de date, nu am modificat nimic')
                
                procesorID = getID(cursor, 'Procesor', 'procesorID', ['producator', 'model', 'arhitectura', 'nr_nuclee',
                    'frecventa', 'cache'], zonesList[3])
                if not procesorID:
                    msgProductAdded = 'Verificati datele despre procesor'
                    return redirect('/adaugare_produse')

                msgProductAdded += insertData(cursor, 'Afisare', ['diagonala', 'format', 'tehnologie_display', 'rata_refresh',
                    'rezolutie'], zonesList[4], '<br>Modelul de display se alfa in baza de date, nu am modificat nimic')

                displayID = getID(cursor, 'Afisare', 'afisareID', ['diagonala', 'format', 'tehnologie_display', 'rata_refresh',
                    'rezolutie'], zonesList[4])
                if not displayID:
                    msgProductAdded = 'Verificati datele despre display'
                    return redirect('/adaugare_produse')

                msgProductAdded += insertData(cursor, 'Placavideo', ['producator', 'model', 'memorie', 'tip_memorie'],
                    zonesList[5], '<br>Modelul de placa video se alfa in baza de date, nu am modificat nimic')

                videoCardID = getID(cursor, 'Placavideo', 'placaVideoID', ['producator', 'model', 'memorie', 'tip_memorie'],
                    zonesList[5])
                if not videoCardID:
                    msgProductAdded = 'Verificati datele despre placa video'
                    return redirect('/adaugare_produse')
               
                
                productData = [categoryID, memoryID, procesorID, displayID, videoCardID, image] + zonesList[0]
                cursor.execute("""INSERT INTO Produs(categorieID, memorieID, procesorID, afisareID, placaVideoID, cale_imagine,
                     denumire, greutate, memorie_interna, stoc, pret) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", productData)
                cursor.commit()

                return redirect('/adaugare_produse')

    return redirect('/front_page')

@app.route('/clasament_clienti')
def bestClients():

    if 'admin' in session:
        if session['admin'] == True:

            cursor = conn.cursor()
            # JOIN
            # Extragere clienti ordonati dupa numarul de produse cumparate
            cursor.execute("""SELECT C.nume, C.prenume, C.telefon, U.dataCreare, (SELECT SUM(CP.cantitate) FROM 
                ClientiProdus AS CP WHERE CP.clientID = C.ClientID GROUP BY CP.clientID ) FROM Clienti AS C,
                Utilizatori AS U WHERE U.utilizatorID = C.utilizatorID ORDER BY (SELECT SUM(CP.cantitate) FROM 
                ClientiProdus AS CP WHERE CP.clientID = C.ClientID GROUP BY CP.clientID ) DESC""")
            bestBuyers = cursor.fetchall()
            bestBuyers = formatToListOfDict(bestBuyers, ['Nume', 'Prenume', 'Telefon', 'DataInscriere', 'Produse_Cumparate'])
            bestBuyers = datetimeToDate(bestBuyers, 'DataInscriere')
            
            # JOIN
            cursor.execute("""SELECT C.nume, C.prenume, C.telefon, U.dataCreare, SUM(P.Pret * CP.cantitate) 
                FROM Clienti AS C, Utilizatori AS U, ClientiProdus AS CP, Produs AS P WHERE U.utilizatorID = C.utilizatorID 
                AND P.produsID = CP.produsID AND C.clientID = CP.clientID GROUP BY C.nume, C.prenume, C.telefon, U.dataCreare 
                ORDER BY 5 DESC""")

            biggestSpenders = cursor.fetchall();
            biggestSpenders = formatToListOfDict(biggestSpenders, ['Nume', 'Prenume', 'Telefon', 'DataInscriere', 'Suma cheltuita (RON)'])
            biggestSpenders = datetimeToDate(biggestSpenders, 'DataInscriere')
            

            cursor.close()
            
            return render_template('bestClients.html', data = bestBuyers,
                 header = ['Nume', 'Prenume', 'Telefon', 'DataInscriere', 'Produse_Cumparate'],
                 data_spend = biggestSpenders, header_spend = ['Nume', 'Prenume', 'Telefon', 
                 'DataInscriere', 'Suma cheltuita (RON)'])

    return redirect('/')

# Stergere date sesiune
@app.route('/logout')
def logout():
    if 'logged' in session:
        session['logged'] = False
    if 'userID' in session:
        session['userID'] = -1
    if 'admin' in session:
        session['admin'] = False
    if 'username' in session:
        session['username'] = ''

    return redirect('/login')


if '__main__' == __name__:
    app.run();