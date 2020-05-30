from time import *
import threading
import getpass
import socket
import os
import re

trenutno_vrijeme = strftime("%d.%m.%Y. %H:%M:%S", localtime()) #Vrijeme

print('Pozdrav, dobro dosao...')
print('Datum i vrijeme vaseg pristupa: {}'.format(trenutno_vrijeme))

korisnik, host, adresa = os.getlogin(), socket.gethostname(), os.path.abspath(os.getcwd())
while True: #Petlja koja vrti prompt
    naredba = input('[{0}@{1}:{2}]$ '.format(korisnik, host, adresa)) #Prompt/odzivni znak
    if naredba == 'exit' or naredba == 'logout':
        break;
    lista_sa_naredbom = naredba.split()
    if naredba != "":
        print(lista_sa_naredbom)
        
    if re.match(r"(pwd\s+.*)|(pwd$)", naredba): #pwd naredba
        if re.match(r"pwd\s*$", naredba):
            print(os.path.abspath(os.getcwd()))
        else:
            print('Naredba ne prima parametre ni argumente')
            
    elif re.match(r"(ps\s+.*)|(ps$)", naredba): #ps naredba
        if re.match(r"ps\s*$", naredba):
            print(os.getpid())
        else:
            print('Nepostojeci parametar ili argument')
            
    elif re.match(r"(echo\s+.*)|(echo$)", naredba):
        print(naredba)
    elif naredba == "kill":
        print(naredba)
    elif naredba == "cd":
        print(naredba)
    elif naredba == "date":
        print(naredba)
    elif naredba == "ls":
        print(naredba)
    elif naredba == "mkdir":
        print(naredba)
    elif naredba == "rmdir":
        print(naredba)
    elif naredba == "kub":
        print(naredba)
    elif re.match(r"\s*$", naredba):
        continue
    else:
        print('pogrsna naredba')
