from time import *
import threading
import getpass
import socket
import os
import re

trenutno_vrijeme = strftime("%d.%m.%Y. %H:%M:%S", localtime()) #Vrijeme

print('Pozdrav, dobro dosao...')
print('Datum i vrijeme vaseg pristupa: {}'.format(trenutno_vrijeme))

korisnik, host, adresa, kucni_dir = os.getlogin(), socket.gethostname(), os.path.abspath(os.getcwd()), os.getenv("HOME")

povijest = kucni_dir + '/.povijest'
print(povijest)
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
            dat = open(povijest, 'a')
            dat.write(naredba)
            dat.write('\n')
            dat.close()
        else:
            print('Naredba ne prima parametre ni argumente')
            
    elif re.match(r"(ps\s+.*)|(ps$)", naredba): #ps naredba
        if re.match(r"ps\s*$", naredba):
            print(os.getpid())
            dat = open(povijest, 'a')
            dat.write(naredba)
            dat.write('\n')
            dat.close()
            
        else:
            print('Nepostojeci parametar ili argument')
            
    elif re.match(r"(echo\s+.*)|(echo$)", naredba):
        if re.match(r"echo\s*$", naredba):
            print('Naredba prima barem jedan argument')
        else:
            for word in lista_sa_naredbom[1:]:
                if re.match(r'"^[^\s\"]+\"[^\s\"]+$"', word):
                    print(word)
                else:
                    izmjena = word.replace('"', '')
                    print(izmjena)
        
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
