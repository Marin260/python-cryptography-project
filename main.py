from time import *
import threading
import getpass
import socket
import os
import re
import time
import argparse
import signal
import sys
from pathlib import Path #za windows compatibility

def upis_u_dat(var, ime_dat): #upis naredbi u dat
    dat = open(ime_dat, 'a')
    dat.write(var)
    dat.write('\n')
    dat.close()

def korak_nazad(put):
    nova_adresa = ""
    if len(put) == 2 and put[1] == '/':
        nova_adresa = "/"
    else:
        trenutna = ""
        trenutna = trenutna.join(put[1])
        trenutna = trenutna.split('/')
        absolutna = os.path.abspath(os.getcwd())
        absolutna = absolutna.split('/')
        iste = False
        if len(trenutna) > 1:
            if absolutna[1] == trenutna[1]:
                iste = True
        if iste == False:
            for x in absolutna:
                if x == "." or x == '':
                    continue
                nova_adresa += "/"
                nova_adresa += x
        for ele in trenutna:
            if ele == "." or ele == '':
                continue
            nova_adresa += "/"
            nova_adresa += ele
    return nova_adresa

trenutno_vrijeme = strftime("%d.%m.%Y. %H:%M:%S", localtime()) #Vrijeme

print('Pozdrav, dobro dosao...')
print('Datum i vrijeme vaseg pristupa: {}'.format(trenutno_vrijeme))

#kucni_dir = os.getenv("HOME")  #radi samo s unixom, na windowsu ne
kucni_dir = str(Path.home())    

povijest = kucni_dir + '/.povijest'
while True: #Petlja koja vrti prompt
    korisnik, host, adresa = getpass.getuser(), socket.gethostname(), os.path.abspath(os.getcwd())
    naredba = input('[{0}@{1}:{2}]$ '.format(korisnik, host, adresa)) #Prompt/odzivni znak
    if naredba == 'exit' or naredba == 'logout':
        break;
    lista_sa_naredbom = naredba.split()
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~pwd naredba~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~        
    if re.match(r"(pwd\s+.*)|(pwd$)", naredba): #pwd naredba
        if re.match(r"pwd\s*$", naredba):
            print(os.path.abspath(os.getcwd()))
            upis_u_dat(naredba, povijest)
        else:
            print('Naredba ne prima parametre ni argumente')
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~ps naredba~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~           
    elif re.match(r"(ps\s+.*)|(ps$)", naredba): #ps naredba
        if re.match(r"ps\s*$", naredba):
            print(os.getpid())
            upis_u_dat(naredba, povijest)
        else:
            print('Nepostojeci parametar ili argument')
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~echo naredba~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~            
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
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~kill naredba~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~            
    elif re.match(r"(kill\s+.*)|(kill$)", naredba): #kill naredba
        if re.match(r"kill\s*$", naredba):
            print('Naredba prima tocno jedan parametar: naziv signala ili njegov redni broj')
        elif re.match(r"(kill -2\s*$)|(kill -SIGINT\s*$)|(kill -INT\s*$)", naredba):
            def upravljac(broj_signala, stog):
                print('Pristiago je signal broj 2: Program se zavrsava.'.format(broj_signala))
                sys.exit()
                return
            signal.signal(signal.SIGINT,upravljac) 
            os.kill(os.getpid(), signal.SIGINT)
            upis_u_dat(naredba, povijest)
        elif re.match(r"(kill -3\s*$)|(kill -SIGQUIT\s*$)|(kill -QUIT\s*$)", naredba):
            signal.signal(signal.SIGQUIT,signal.SIG_IGN) 
            os.kill(os.getpid(), signal.SIGQUIT)
            print('Signal broj 3 je ignoriran')
            upis_u_dat(naredba, povijest)
        elif re.match(r"(kill -15\s*$)|(kill -SIGTERM\s*$)|(kill -TERM\s*$)", naredba):
            signal.signal(signal.SIGTERM,signal.SIG_DFL)
            os.kill(os.getpid(), signal.SIGTERM)
            upis_u_dat(naredba, povijest)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~cd naredba~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 
    

    elif re.match(r"(cd\s+.*)|(cd$)", naredba): #cd naredba    
        if re.match(r"^cd\s*$", naredba):
            os.chdir(kucni_dir)
        elif re.match(r"cd\s+(\.{0,2}(\/.*)+)|([^\/]+\/{1})+|([^\/]+)", naredba):
            try:
                os.chdir(korak_nazad(naredba.split()))
            except OSError:
                print('Upisana adresa ne postoji')
        else:
            print('Kriva naredba')
        
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~date naredba~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~       
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
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~ls naredba~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  
    elif re.match(r"(ls\s+.*)|(ls$)", naredba): #ls naredba
        if re.match(r"(ls\s+[^\-]+.*)|(ls\s*$)", naredba):
            def lsnohidden(path):
                for f in os.listdir(path):
                    if not f.startswith('.'):
                        print (f)
            if re.match(r"ls\s*$", naredba):
                lsnohidden(os.getcwd())
            elif re.match(r"ls\s+[^\-]", naredba):
                try:
                    lsnohidden(korak_nazad(naredba.split()))
                except OSError:
                    print('Upisali ste krivu adresu')
            upis_u_dat(naredba, povijest)
        elif re.match(r"ls -l\s*$", naredba):
            def ls():
                    from pwd import getpwuid
                    from grp import getgrgid
                    import pprint
                    for f in listdir():
                        filestats=os.lstat(os.path.join(os.getcwd(),f))
                        mode_chars=['r','w','x']
                        st_perms=bin(filestats.st_mode)[-9:]
                        mode=filetype_char(filestats.st_mode)
                        for i, perm in enumerate(st_perms):
                            if perm=='0':
                                mode+='-'
                            else:
                                mode+=mode_chars[i%3] 
                        entry=[mode,str(filestats.st_nlink),getpwuid(filestats.st_uid).pw_name,getgrgid(filestats.st_gid).gr_name,str(filestats.st_size),f]                          
                        pprint.pprint(entry) 
              
           def filetype_char(mode):
                import stat
                if stat.S_ISDIR(mode):
                    return 'd'
                if stat.S_ISLNK(mode):
                    return 'l'
                return '-'
            
           def listdir():
               dirs=os.listdir(os.getcwd())
               dirs=[dir for dir in dirs if dir[0]!='.']
               return dirs
                
           ls()
           upis_u_dat(naredba, povijest)
        elif re.match(r"ls\s+-l+[^\-]", naredba):
            def ls():
                    from pwd import getpwuid
                    from grp import getgrgid
                    import pprint
                    for f in listdir():
                        var=naredba.split()
                        var=var[1:]
                        filestats=os.lstat(os.path.join(korak_nazad(var,0),f))
                        mode_chars=['r','w','x']
                        st_perms=bin(filestats.st_mode)[-9:]
                        mode=filetype_char(filestats.st_mode)
                        for i, perm in enumerate(st_perms):
                            if perm=='0':
                                mode+='-'
                            else:
                                mode+=mode_chars[i%3] 
                        entry=[mode,str(filestats.st_nlink),getpwuid(filestats.st_uid).pw_name,getgrgid(filestats.st_gid).gr_name,str(filestats.st_size),f]                          
                        pprint.pprint(entry) 
              
            def filetype_char(mode):
                import stat
                if stat.S_ISDIR(mode):
                    return 'd'
                if stat.S_ISLNK(mode):
                    return 'l'
                return '-'
            
            def listdir():
               var=naredba.split()
               var=var[1:]
               dirs=os.listdir(korak_nazad(var,0))
               dirs=[dir for dir in dirs if dir[0]!='.']
               return dirs
                
            ls()
            upis_u_dat(naredba, povijest)
        elif re.match(r"ls -l.*$", naredba):
            print('Nepostojeci parametar')
        elif re.match(r"ls -[^l]*\s*$", naredba):
            print('Nepostojeci parametar')
            
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~mkdir naredba~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~            
    elif re.match(r"(mkdir\s+.*)|(mkdir$)", naredba):  
        if re.match(r"mkdir\s*$", naredba):             #regex za ako korisnik upise samo mkdir bez argumenata
            print("Naredba mora primiti argument")     
        elif (len(lista_sa_naredbom)>=3):       #ako naredba ima vise od jednog argumenta javi gresku
            print ("Naredba ne smije imati vise od jednog argumenta")       
        else:                                           #izvedi ovo ako je dobro upisana naredba
            for word in lista_sa_naredbom[1:2]:         
                argument=word                           
            try:
                os.makedirs(argument)                   #stvaranje direktorija
            except FileExistsError:                     #ako direktorij postoji, javi ovu gresku
                print("Ovaj direktorij vec postoji!")
            except OSError:                             #pri javljanju neke druge greske (npr ako nema mjesta na disku) javi ovu gresku
                print("Stvaranje direktorija nije uspjelo!")
            upis_u_dat(naredba, povijest)               #upis u povjest
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~rmdir naredba~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~        
    elif re.match(r"(rmdir\s+.*)|(rmdir$)", naredba):   
        if re.match(r"rmdir\s*$", naredba):             #regex za ako korisnik upise samo rmdir bez ikakvih argumenata
            print("Naredba mora primiti argument")      
        elif (len(lista_sa_naredbom)>=3):               #ako naredba ima vise od jednog argumenta javi gresku
            print ("Naredba ne smije imati vise od jednog argumenta")
        else:                                           #izvedi ovo kad je naredba dobro upisana
            for word in lista_sa_naredbom[1:2]:         
                argument=word
            try:
                os.rmdir(argument)                      #brisanje direktorija
            except FileNotFoundError:
                print("Direktorij nije pronadena!")       #greska koja se ispisuje ako je argument direktorij koji ne postoji
            except OSError:
                print("Brisanje direktorija nije uspjelo, direktorij nije prazan")     #greska koja se ispisuje kad direktorij koji se brise nije prazan
            upis_u_dat(naredba, povijest)               #upis u povjest
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~kub naredba~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~              
    elif naredba == "kub":
        print(naredba)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~        
    elif re.match(r"\s*$", naredba):
        continue
    else:
        print('pogresna naredba')
