# importare biblioteca pentru criptare
import hashlib


# Realizeaza criptarea parolei
def make_pw_hash(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# Verifica daca o parola introdusa este identica cu o criptare existenta
def check_pw(password, hash):
    
    return make_pw_hash(password) == hash
    

