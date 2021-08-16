
# Verifica daca utilizatorul este logat
def checkLoggedReturnUserID(session):
    if 'logged' in session:
        if session['logged'] == True:
            return session['userID']
        return -1
    return -1