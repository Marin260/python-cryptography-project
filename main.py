from time import *
import threading
import getpass
import socket
import os
import re

def upis_u_dat(var, ime_dat): #upis naredbi u dat
    dat = open(ime_dat, 'a')
    dat.write(var)
    dat.write('\n')
    dat.close()

trenutno_vrijeme = strftime("%d.%m.%Y. %H:%M:%S", localtime()) #Vrijeme

print('Pozdrav, dobro dosao...')
print('Datum i vrijeme vaseg pristupa: {}'.format(trenutno_vrijeme))

kucni_dir = os.getenv("HOME")

povijest = kucni_dir + '/.povijest'
while True: #Petlja koja vrti prompt
    korisnik, host, adresa = os.getlogin(), socket.gethostname(), os.path.abspath(os.getcwd())
    naredba = input('[{0}@{1}:{2}]$ '.format(korisnik, host, adresa)) #Prompt/odzivni znak
    if naredba == 'exit' or naredba == 'logout':
        break;
    lista_sa_naredbom = naredba.split()
    if naredba != "":
        print(lista_sa_naredbom)
        
    if re.match(r"(pwd\s+.*)|(pwd$)", naredba): #pwd naredba
        if re.match(r"pwd\s*$", naredba):
            print(os.path.abspath(os.getcwd()))
            upis_u_dat(naredba, povijest)
        else:
            print('Naredba ne prima parametre ni argumente')
            
    elif re.match(r"(ps\s+.*)|(ps$)", naredba): #ps naredba
        if re.match(r"ps\s*$", naredba):
            print(os.getpid())
            upis_u_dat(naredba, povijest)
        else:
            print('Nepostojeci parametar ili argument')
            
    elif re.match(r"(echo\s+.*)|(echo$)", naredba): #echo naredba
        if re.match(r"echo\s*$", naredba):
            print('Naredba prima barem jedan argument')
        else:
            upis_u_dat(naredba, povijest)
            for word in lista_sa_naredbom[1:]:
                if re.match(r'^\"(.*\".*)*\"$', word):
                    word = word[1:-1]
                    print(word, end=" ")
                elif re.match(r'(^\"[^"]+)|([^"]+\"$)|(^\"[^"]+\"$)|(^\"$)', word):
                    izmjena = word.replace('"', '')
                    print(izmjena, end=" ")
                else:
                    print(word, end=" ")
            print()
            
        
        
    elif naredba == "kill":
        print(naredba)
    elif re.match(r"(cd\s+.*)|(cd$)", naredba): #cd naredba
        def korak_nazad(adresa):
            trenutna = adresa.split('/')
            nova_adresa = ""
            for ele in trenutna[1:-1]:
                nova_adresa += "/"
                nova_adresa += ele
            return nova_adresa
            
        if re.match(r"^cd\s*$", naredba):
            os.chdir(kucni_dir)
        elif re.match(r"cd\s\.{1}\s*$", naredba):
            continue
        elif re.match(r"cd\s\.{2}\s*", naredba):
            os.environ['prethodna'] = korak_nazad(adresa)
            os.chdir(os.environ['prethodna'])

            
        
    elif re.match(r"(date\s.*)|(date\s*$)", naredba): #date naredba
        if re.match(r"date\s*$", naredba):
            print (strftime("%H::%M::%S  %A  %d/%m/%Y"))
            upis_u_dat(naredba, povijest)
        elif re.match(r"date -r\s*$", naredba):
            print (strftime("%d/%m/%Y  %A  %H::%M::%S"))
            upis_u_dat(naredba, povijest)
        elif re.match(r"date -[^r]\s*$", naredba):
            print('Nepostojeci parametar')
        else:
            print('Nepostojeci argument')
    
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
        print('pogresna naredba')
