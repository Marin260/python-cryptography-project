import os
import socket
from cryptography.fernet import Fernet


def upis_u_dat(var, lista): #upis naredbi u listu
    #1.arg je string koji dodajemo listi
    #2.arg je lista u koju dodajemo string
    lista.append(var) #dodajemo novi element u list
    
def dat(lista, ime_dat): #upis liste u datoteku
    #1.arg lista koju upisujemo u datoteku
    #2.arg datoteka u koju spremamo elemente iz liste
    dat = open(ime_dat, 'a')
    for ele in lista: #svaki element liste upisujemo u datoteku kao novi red
        dat.write(ele)
        dat.write('\n')
    dat.close()

def korak_nazad(put):
    # argument je lista sa naredbom
    nova_adresa = ""
    if len(put) == 2 and put[1] == '/': # Ako je 2 elem liste / onda je to root
        nova_adresa = "/"
    else:
        trenutna = ""
        trenutna = trenutna.join(put[1]) # string koji sadrzi samo adresu
        trenutna = trenutna.split('/') 
        absolutna = os.path.abspath(os.getcwd())# absolutna adresa do radnog direktorija direktorija
        absolutna = absolutna.split('/')
        iste = False
        if len(trenutna) > 1: 
            if absolutna[1] == trenutna[1]: # ako su prvi elementi isti onda smatramo da je adresa abs
                iste = True
        if iste == False:
            for x in absolutna:
                if x == "." or x == '':
                    continue
                nova_adresa += "/"
                nova_adresa += x
        for ele in trenutna: # stvara adresu
            if ele == "." or ele == '':
                continue
            nova_adresa += "/"
            nova_adresa += ele
    return nova_adresa #vraca stvorenu adresu

def sendComand(naredba: str, key, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', port))
    msg = naredba.encode()
    
    f = Fernet(key)
    token = f.encrypt(msg)
    sock.send(token)

    primljeni_podaci = sock.recv(4096)
    if not primljeni_podaci:
        return
    to_dec = f.decrypt(primljeni_podaci)
    try:
        to_dec = eval(to_dec)                   #stvaranje direktorija
        for podatak in to_dec:
            print(podatak)
    except SyntaxError:                     #ako direktorij postoji, javi ovu gresku
        to_dec = to_dec.decode()
        print(to_dec)
    
    sock.close()