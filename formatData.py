import re 
import random

def checkFormData(filedName, request):
    try:
        field = request.form[filedName]
    except:
        field = ''
    
    return field

def returnListFormData(nameList, request):
    listToReturn = []
    for item in nameList:
        listToReturn.append(checkFormData(item, request))
    return listToReturn

def splitZones(listToSplit):

    row = 0
    col = 0
    listOutput = [[]]
    for item in listToSplit:
        if item != '':
            listOutput[row].append(item)
        else:
            listOutput.append([])
            row += 1
    return [listOutput, row]

def blankPadding(initialList, maxSize):

    while len(initialList) < maxSize:
        initialList.append('')
    
    return initialList

def formatLineToDict(dataToFormat, dictFormat):

    output = {}
    index = 0
    for element in dictFormat: 
        output[element] = dataToFormat[index]       
        index += 1
    return output

def checkPassword(password):

    flag = True
    
    if (len(password)<8): 
        flag = False
    elif not re.search("[a-z]", password): 
        flag = False
    elif not re.search("[A-Z]", password): 
        flag = False
    elif not re.search("[0-9]", password): 
        flag = False
    elif not re.search("[@!#$%^&*()?><:\||\=_]", password): 
        flag = False
    elif re.search("\s", password): 
        flag = False

    return flag

def checkPhone(phone):

    if not re.search("[0-9]", phone):
        return False
    if len(phone) != 10:
        return False
    return True


    
def formatToListOfDict(dataToFormat, dictItems):

    emptyDict = {}
    dataToSend = []

    # Cream un model de dictionar pentru stocarea datelor
    for dictItem in dictItems:
        emptyDict[dictItem] = ''
        
    # Parcurgem datele de adaugat in lista de dictionare
    i = 0
    for data in dataToFormat:
        #Creare dictionar copiat
        eDict = dict(emptyDict)
        # Adaugam un dictionar gol pe care-l vom umple cu date
        dataToSend.append(eDict)
        # Adaugare date in dictionar
        index = 0;
        for dictItem in dictItems:
            try:
                dataToSend[i][dictItem] = dataToFormat[i][index]
                index += 1
            except:
                pass
        i += 1

    return dataToSend


def datetimeToDate(listOfDict, dictElement):

    for row in listOfDict:
        row[dictElement] = row[dictElement].date() 

    return listOfDict


def scrambled(orig):
    dest = orig[:]
    random.shuffle(dest)
    return dest