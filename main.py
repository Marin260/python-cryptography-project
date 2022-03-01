import threading as th
from time import *
import getpass
import socket
import signal
import sys
import os
import re

import crypt
import socket
import configparser
from cryptography.fernet import Fernet
from hmac import compare_digest as compare_hash
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key

from pomocneFje import *
from klijent import remotesh
from napadi import attack

login = False

trenutno_vrijeme = strftime("%d.%m.%Y. %H:%M:%S", localtime()) #Vrijeme

print('Pozdrav, dobro dosao... ({})'.format(trenutno_vrijeme))

kucni_dir = os.getenv("HOME")  #radi samo s unixom, na windowsu ne
  

povijest = kucni_dir + '/.povijest'
lista_za_ispis = []
while True: #Petlja koja vrti prompt
    port = 8000 # default
    korisnik, host, adresa = getpass.getuser(), socket.gethostname(), os.path.abspath(os.getcwd()) #varijable koje cine prompt
    naredba = input('[{0}@{1}:{2}]$ '.format(korisnik, host, adresa)) #Prompt/odzivni znak
    if re.match(r"exit\s*$", naredba) or re.match(r'logout\s*$', naredba): #ako je unos exit ili logout onda se prekida program
        dat(lista_za_ispis, povijest) #upis naredbi iz trenutna sesije u datoteku 
        sendComand(naredba, sym_key, port)
        break
    lista_sa_naredbom = naredba.split()

    if re.match(r"remoteshd\s*", naredba):
        config = configparser.ConfigParser()
        config.read('remoteshd.ini')
        port = int(config['DEFAULT']['port'])
        status_code = 200

        if config.has_option('keys', 'private_key') == False:
            # gen private/public key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=4096,
            )
            public_key = private_key.public_key()
            
            # serialize private/public key
            private_key = private_key.private_bytes(
                encoding = serialization.Encoding.PEM,
                format = serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.BestAvailableEncryption(b'1234')
            )
            public_key = public_key.public_bytes(
                encoding = serialization.Encoding.PEM,
                format = serialization.PublicFormat.PKCS1
            )
            
            private_key = private_key.decode("utf-8")
            public_key = public_key.decode("utf-8")
            config['keys']['private_key'] = private_key
            config['keys']['public_key'] = public_key
            with open('remoteshd.ini', 'w') as configfile:
                config.write(configfile)

        #--------------------------------
        #citanje iz konfiga
        pasConf = configparser.ConfigParser() # config parser za zaporke
        pasConf.read('users-passwords.ini')

        public_key = config['keys']['public_key'].encode()
        privateKey = config['keys']['private_key'].encode()

        session = "False"

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('localhost', port))
        sock.listen(1)
        clisock, addr = sock.accept()
        clisock.send(public_key)

        key = load_pem_private_key(privateKey, password=b'1234')

        lista_sa_podacima=[] #lista sa primljenim podacima
        step = 0
        while step < 2:
            podaci = clisock.recv(1024)
            if not podaci:
                break
            
            plaintext = key.decrypt(
                podaci,
                padding.OAEP(
                    mgf = padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            print(plaintext)
            lista_sa_podacima.append(plaintext.decode()) #dodavanje podataka u listu
            if step == 1:
                if pasConf.has_section(lista_sa_podacima[0]) == False: #ako user ne postoji
                    pasConf[lista_sa_podacima[0]] = {}

                    # Ako user ne postoji generiraj sol
                    salt = crypt.mksalt(crypt.METHOD_SHA512)
                    pasConf[lista_sa_podacima[0]]['salt'] = salt
                    # hash lozinke
                    hashed = crypt.crypt(lista_sa_podacima[1], salt)
                    
                    pasConf[lista_sa_podacima[0]]['password'] = hashed
                    with open('users-passwords.ini', 'w') as configfile:
                        pasConf.write(configfile)
                    step+=1
                    login = True
                    session = "True"
                    podaci_za_slanje = session.encode()
                    clisock.send(podaci_za_slanje)
                    print('Uspjesna registracija')
                    
                else:
                    toCheck = crypt.crypt(lista_sa_podacima[1], pasConf[lista_sa_podacima[0]]['salt'])
                    if not compare_hash(pasConf[lista_sa_podacima[0]]['password'], crypt.crypt(lista_sa_podacima[1], pasConf[lista_sa_podacima[0]]['salt'])):
                        print("hashed version doesn't validate against original")
                        lista_sa_podacima.pop()
                        podaci_za_slanje = session.encode()
                        clisock.send(podaci_za_slanje)
                        continue
                    else:
                        login = True
                        session = "True"
                        print('Uspjesna prijava')
                    podaci_za_slanje = session.encode()
                    clisock.send(podaci_za_slanje)
            step+=1

        # sim kluc primanje
        podaci = clisock.recv(1024)
        client_key = key.decrypt(
            podaci,
            padding.OAEP(
                mgf = padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        while login:
            sock.listen(1)
            clisock, addr = sock.accept()
            while True:
                token = clisock.recv(1024)
                if not token:
                    break
                f = Fernet(client_key)
                podaci = f.decrypt(token)
                if podaci.decode() == "exit":
                    login = False
                    break

                elif re.match(r"(pwd\s+.*)|(pwd$)", podaci.decode()):
                    if re.match(r"pwd\s*$", podaci.decode()):
                        to_send = str(os.path.abspath(os.getcwd())).encode() #Ispis adrese u kojoj se korisnik nalazi
                        upis_u_dat(podaci.decode(), lista_za_ispis)
                    else:
                        to_send = b'Naredba ne prima parametre ni argumente'

                    token = f.encrypt(to_send)
                    clisock.send(token)

                elif re.match(r"(ps\s+.*)|(ps$)", podaci.decode()): #ps naredba
                    if re.match(r"ps\s*$", podaci.decode()):
                        to_send = str(os.getpid()).encode() #Ispis PID-a procesa
                        upis_u_dat(podaci.decode(), lista_za_ispis)
                        status_code = 200
                    else:
                        to_send = b'Nepostojeci parametar ili argument'
                        status_code = 400
                    token = f.encrypt(to_send)
                    clisock.send(token)

                elif re.match(r"(date\s.*)|(date\s*$)", podaci.decode()): #date naredba
                    if re.match(r"date\s*$", podaci.decode()):
                        to_send = strftime("%H::%M::%S  %A  %d/%m/%Y").encode()       #printa sati::minute::sekunde dan u tjednu dan/mjesec/godina
                        upis_u_dat(podaci.decode(), lista_za_ispis)
                        status_code = 200                
                    elif re.match(r"date\s+-r\s*$", podaci.decode()):
                        to_send = strftime("%d/%m/%Y  %A  %H::%M::%S").encode()       #printa dan/mjesec/godina dan u tjednu sati::minute::sekunde
                        upis_u_dat(podaci.decode(), lista_za_ispis)
                        status_code = 200
                    elif re.match(r"date\s+-[^r].*\s*$", podaci.decode()):
                        to_send = b'Nepostojeci parametar'
                        status_code = 400
                    else:
                        to_send = b'Nepostojeci argument'
                        status_code = 400
                    token = f.encrypt(to_send)
                    clisock.send(token)

                elif re.match(r"(ls\s+.*)|(ls$)", podaci.decode()): #ls naredba
                    if re.match(r"(ls\s+[^\-]+.*)|(ls\s*$)", podaci.decode()):
                        def lsnohidden(path):                    #fja za izlistavanje direktorija i datoteka (bez skrivenih)
                            list_to_send = []
                            for f in os.listdir(path):           #petlja koja izbacuje sve sto pocinje sa .(skrivene datoteke/direktoriji)
                                if not f.startswith('.'):
                                    list_to_send.append(f)
                            return list_to_send
                        if re.match(r"ls\s*$", podaci.decode()):
                            to_send = str(lsnohidden(os.getcwd())).encode()      #uzima adresu gdje se trenutno nalazimo
                            status_code = 400
                        elif re.match(r"ls\s+[^\-]", podaci.decode()):
                            try:
                                to_send = str(lsnohidden(korak_nazad(podaci.decode().split()))).encode()       #implementirana funkcija za apsolutnu adresu iz naredbe cd
                                status_code = 200
                            except OSError:                                    #ako je upisana nepostojeca adresa (oserror) program nam to javlja porukom
                                to_send = b'Upisali ste krivu adresu'
                                status_code = 400
                        upis_u_dat(podaci.decode(), lista_za_ispis)
                    elif re.match(r"ls -l\s*$", podaci.decode()):
                        x=1
                        def ls():  
                            from pwd import getpwuid   #trebaju nam kako bi mogli dobiti uid i gid
                            from grp import getgrgid
                            for f in listdir():
                                if x==0:
                                    var=podaci.decode().split()      #razdvaja naredbu u 3 djela
                                    var=var[1:]              #te ju cita tek od -l(zanemaruje ls)
                                    filestats=os.lstat(os.path.join(korak_nazad(var),f))   #ako je x=0 znaci da je ls -l aps_adresa, a ako je x=1 onda je samo ls-l
                                else:
                                    filestats=os.lstat(os.path.join(os.getcwd(),f))
                                mode_chars=['r','w','x']              #svi moguci znakovi permissionsa
                                st_perms=bin(filestats.st_mode)[-9:]    #zadnih 9 bitova u binarnom obliku su permissionsi ako je 1 je slovo ako je 0 je -
                                mode=filetype_char(filestats.st_mode)    #mode je varijabla u koju spremamo permissionse 
                                for i, perm in enumerate(st_perms):      #petlja koja ide kroz zadnjih 9 binarnih brojeva(permissionse)
                                    if perm=='0':                        #ako je broj 0 vraca -
                                        mode+='-'
                                    else:
                                        mode+=mode_chars[i%3]            #inace ako je 1 vraca koje god slovo bi trebalo bit na tom mjestu(r,w ili x) 
                                entry=[mode,str(filestats.st_nlink),getpwuid(filestats.st_uid).pw_name,getgrgid(filestats.st_gid).gr_name,str(filestats.st_size),f]                          
                                to_send = str(entry).encode()
                                return to_send

                        def filetype_char(mode):      #fja za prvo slovo permissionsa
                            import stat
                            if stat.S_ISDIR(mode):    #ako je direktorij vrati d
                                return 'd'
                            if stat.S_ISLNK(mode):     #ako je symbolic link vrati l
                                return 'l'
                            return '-'                 #ako je datoteka bilo kojeg tipa vrati -
                        
                        def listdir():
                            if x==0:
                                var=podaci.decode().split()
                                var=var[1:]
                                dirs=os.listdir(korak_nazad(var))
                            else:
                                dirs=os.listdir(os.getcwd())
                            dirs=[dir for dir in dirs if dir[0]!='.']
                            return dirs                         #fja koja vraca sve datoteke i direktorije koji nisu skriveni u obliku liste
                            
                        to_send = ls()                                    #poziv fje koja ispisuje ls -l
                        upis_u_dat(podaci.decode(), lista_za_ispis)
                        status_code = 200
                    elif re.match(r"ls\s+-l+\s+[^\-]", podaci.decode()):
                        x=0
                        try:   
                            to_send = ls()          #fja za ls -l sa argumentom apsolutne adrese 
                            status_code = 200
                        except FileNotFoundError:                  #ako apsolutna adresa ne postoji javlja nam gresku
                            to_send = b'Upisali ste krivu adresu'
                            status_code = 400
                        upis_u_dat(podaci.decode(), lista_za_ispis)
                    elif re.match(r"ls -l.*$", podaci.decode()):          #petlje za pogresne parametre
                        to_send = b'Nepostojeci parametar'
                        status_code = 400
                    elif re.match(r"ls -[^l]*\s*$", podaci.decode()):
                        to_send = b'Nepostojeci parametar'
                        status_code = 400  
                    
                    token = f.encrypt(to_send)
                    clisock.send(token)

                elif re.match(r"(mkdir\s+.*)|(mkdir$)", podaci.decode()):  
                    if re.match(r"mkdir\s*$", podaci.decode()):
                        to_send = b"Naredba mora primiti argument"
                        status_code = 400
                    elif (len(lista_sa_naredbom)>=3):       #ako naredba ima vise od jednog argumenta javi gresku
                        to_send = b'Naredba ne smije imati vise od jednog argumenta' 
                        status_code = 400      
                    else:
                        for word in lista_sa_naredbom[1:2]:         
                            argument=word                           
                        try:
                            os.makedirs(argument)                   #stvaranje direktorija
                            status_code = 200
                        except FileExistsError:                     #ako direktorij postoji, javi ovu gresku
                            to_send = b'Ovaj direktorij vec postoji!'
                            status_code = 400
                        except OSError:                             #pri javljanju neke druge greske (npr ako nema mjesta na disku) javi ovu gresku
                            to_send = b'Stvaranje direktorija nije uspjelo!'
                            status_code = 400
                        upis_u_dat(podaci.decode(), lista_za_ispis)
                    token = f.encrypt(to_send)
                    clisock.send(token)

                elif re.match(r"(rmdir\s+.*)|(rmdir$)", podaci.decode()):   
                    if re.match(r"rmdir\s*$", podaci.decode()):
                        to_send = b'Naredba mora primiti argument'
                        status_code = 400      
                    elif (len(lista_sa_naredbom)>=3):               #ako naredba ima vise od jednog argumenta javi gresku
                        to_send = b'Naredba ne smije imati vise od jednog argumenta'
                        status_code = 400
                    else:
                        for word in lista_sa_naredbom[1:2]:         
                            argument=word
                        try:
                            os.rmdir(argument)                      #brisanje direktorija
                            status_code = 200
                        except FileNotFoundError:
                            to_send = b'Direktorij nije pronadena!'       #greska koja se ispisuje ako je argument direktorij koji ne postoji
                            status_code = 400
                        except OSError:
                            to_send = b'Brisanje direktorija nije uspjelo, direktorij nije prazan'     #greska koja se ispisuje kad direktorij koji se brise nije prazan
                            status_code = 400
                        upis_u_dat(podaci.decode(), lista_za_ispis)              #upis u povjest
                    token = f.encrypt(to_send)
                    clisock.send(token)
                
                elif re.match(r"kub\s*$", podaci.decode()):
                    broj_za_oduzimanje = 29290290290290290290
                    adresa_rez = kucni_dir + '/rezultat.txt' #datoteka za meduvrijednosti

                    barijera = th.Barrier(3) #barijera
                    lock = th.Lock()         #lokot za threadove

                    try:                             #brise sve iz datoteke ako vec postoji
                        rez = open(adresa_rez, 'r+') 
                        rez.truncate(0)
                        rez.close
                    except FileNotFoundError:
                        pass
                    
                    def thread_kub(n): #oduzimanje
                        #argument je broj do kojeg ce for petlja vrtiti
                        lock.acquire()           #ulazi u kriticnu sekciju i zatvara ulaz drugima
                        rez = open(adresa_rez, 'a')
                        global broj_za_oduzimanje #djeljiva varijabla
                        for i in range(n):
                            broj_za_oduzimanje -= i**3 #oduzima kubove brojeva
                            rez.write('N = {}'.format(broj_za_oduzimanje)) #zapis meduvrijednosti u datoteku
                            rez.write('\n')
                            
                        rez.write('Kraj threada')
                        rez.write('\n')
                        rez.close()
                        lock.release()
                        id_threada = barijera.wait()
                        if id_threada == 1:
                            to_send = b'Dretve se prosle barijeru i izvrsile su program'
                        
                    nit1 = th.Thread(target = thread_kub, args=(100000,))    #novi thread
                    nit2 = th.Timer(2, thread_kub, args=(100000, ))          #thread pocinje dvije sekunde kasnije
                    nit3 = th.Thread(target = thread_kub, args=(100000,))    #novi thread
                    
                    nit1.start() #
                    nit2.start() #pokretanje threadova
                    nit3.start() #

                    nit1.join() #
                    nit3.join() #program ceka da se threadovi izvrse
                    nit2.join() #

                    upis_u_dat(podaci.decode(), lista_za_ispis)      # upis naredbe u listu
                    status_code = 400
                    token = f.encrypt(to_send)
                    clisock.send(token)
                elif re.match(r"kub\s+\-+.*\s*", podaci.decode()):   # ako korisnik upise
                    to_send = b'Naredba ne prima parametre'      # parametre ili
                    token = f.encrypt(to_send)
                    clisock.send(token)
                    status_code = 400
                elif re.match(r"kub\s+[^\-]+\s*", podaci.decode()):  # argumente
                    to_send = b'Naredba ne prima argumente'      # ispisuje gresku
                    token = f.encrypt(to_send)
                    clisock.send(token)
                    status_code = 400
                else:
                    to_send = b'pogresna naredba'      # ispisuje gresku
                    token = f.encrypt(to_send)
                    clisock.send(token)
                    status_code = 404

                if login:
                    print(u"\u001b[32mDatum i vrijeme:\u001b[37m {}".format(strftime("%d-%m-%Y %H:%M:%S", localtime())))
                    print(u"\u001b[32mPrimljena naredba:\u001b[37m {}".format(podaci.decode()))
                    print(u"\u001b[32mStatusni kod:\u001b[37m {}".format(status_code))
                    print(u"\u001b[32mIzlaz naredbe:\u001b[37m {}".format(to_send.decode()))
                    print()
        
        clisock.close()
        sock.close()

#------------------------------------------------------------------------------
    elif re.match(r"remotesh\s*", naredba):
        status_code = 200
        sym_key, login = remotesh(login)

        print(login)
        print(sym_key)
        continue
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~pwd naredba~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~        
    if re.match(r"(pwd\s+.*)|(pwd$)", naredba):
        if login:
            sendComand(naredba, sym_key, port)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~ps naredba~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~           
    elif re.match(r"(ps\s+.*)|(ps$)", naredba): #ps naredba
        if login:
            sendComand(naredba, sym_key, port)    
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~echo naredba~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~            
    elif re.match(r"(echo\s+.*)|(echo$)", naredba): #echo naredba
        if re.match(r"echo\s*$", naredba):
            print('Naredba prima barem jedan argument')
        else:
            upis_u_dat(naredba, lista_za_ispis) # upis naredbe u listu
            for word in lista_sa_naredbom[1:]:
                if re.match(r'^\"(.*\".*)*\"$', word):
                    word = word[1:-1]
                    print(word, end=" ")
                elif re.match(r'(^\"[^"]+)|([^"]+\"$)|(^\"[^"]+\"$)|(^\"$)', word):
                    izmjena = word.replace('"', '') #brise "
                    print(izmjena, end=" ")
                else:
                    print(word, end=" ")
            print()
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~kill naredba~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~            
    elif re.match(r"(kill\s+.*)|(kill$)", naredba): #kill naredba
        if re.match(r"kill\s*$", naredba):
            print('Naredba prima tocno jedan parametar: naziv signala ili njegov redni broj')
        elif re.match(r"(kill\s+\-2\s*$)|(kill\s+\-SIGINT\s*$)|(kill\s+\-INT\s*$)", naredba):
            def upravljac(broj_signala, stog):
                print('Pristiago je signal broj 2: Program se zavrsava.'.format(broj_signala))
                sys.exit()
                return
            upis_u_dat(naredba, lista_za_ispis)      # upis naredbe u listu
            signal.signal(signal.SIGINT,upravljac)   #ceka sigint salje ga upravljacu
            os.kill(os.getpid(), signal.SIGINT)      #interrupta i zavrsava program
        elif re.match(r"(kill\s+\-3\s*$)|(kill\s+\-SIGQUIT\s*$)|(kill\s+\-QUIT\s*$)", naredba):
            upis_u_dat(naredba, lista_za_ispis)                 # upis naredbe u listu
            signal.signal(signal.SIGQUIT,signal.SIG_IGN)        #ceka da se desi signal broj 3 te ga ignorira
            os.kill(os.getpid(), signal.SIGQUIT)                #salje signal 3
            print('Signal broj 3 je ignoriran')
        elif re.match(r"(kill\s+\-15\s*$)|(kill\s+\-SIGTERM\s*$)|(kill\s+\-TERM\s*$)", naredba):
            upis_u_dat(naredba, lista_za_ispis)                 # upis naredbe u listu
            signal.signal(signal.SIGTERM,signal.SIG_DFL)        #ceka da se desi signal i izvrsava default
            os.kill(os.getpid(), signal.SIGTERM)                #saljemo signal broj 15
        elif re.match(r"kill\s+\-.*", naredba):
            print('Krivi parametar')
        elif re.match(r"kill\s+[^\-].*", naredba):
            print('Naredba ne prima argumente')
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~cd naredba~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 
    elif re.match(r"(cd\s+.*)|(cd$)", naredba): #cd naredba    
        if re.match(r"^cd\s*$", naredba):
            os.chdir(kucni_dir) #ako je samo cd onda nas vraca u kucni dir
            upis_u_dat(naredba, lista_za_ispis)
        elif re.match(r"cd\s+(\.{0,2}(\/.*)+)|([^\/]+\/{1})+|([^\/]+)", naredba):
            try:        #mjenjamo direktoriji, u slucaju OS greske znamo da direktoriji ne postoji
                os.chdir(korak_nazad(naredba.split())) #mjenja dir uz pomoc definirane fje
            except OSError: #ako se desi OSError onda je unesena kriva adresa
                print('Upisana adresa ne postoji') #promjena dir se nece izvest
            upis_u_dat(naredba, lista_za_ispis) # upis naredbe u listu
        else:
            print('Kriva naredba')
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~date naredba~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~       
    elif re.match(r"(date\s.*)|(date\s*$)", naredba): #date naredba
        if login:
            sendComand(naredba, sym_key, port)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~ls naredba~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  
    elif re.match(r"(ls\s+.*)|(ls$)", naredba): #ls naredba
        if login:
            sendComand(naredba, sym_key, port)   
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~mkdir naredba~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~            
    elif re.match(r"(mkdir\s+.*)|(mkdir$)", naredba):  
        if login:
            sendComand(naredba, sym_key, port)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~rmdir naredba~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~        
    elif re.match(r"(rmdir\s+.*)|(rmdir$)", naredba):   
        if login:
            sendComand(naredba, sym_key, port)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~kub naredba~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    elif re.match(r"kub\s*$", naredba):
        if login:
            sendComand(naredba, sym_key, port)
    elif re.match(r"kub\s+\-+.*\s*", naredba):   # ako korisnik upise
        if login:
            sendComand(naredba, sym_key, port)
    elif re.match(r"kub\s+[^\-]+\s*", naredba):  # argumente
        if login:
            sendComand(naredba, sym_key, port)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~      
    elif re.match(r"attack\s*", naredba):
        import time
        start = time.time()
        # type of attack su tocke u zadatku, promjenom tog broja mjenja se i ono sta napadac "zna"
        type_of_attack = 2
        print('napadi')

        foundPass = attack(type_of_attack)
        print("pronadena lozinka je {}".format(foundPass))
        end = time.time()
        print(end - start)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~     
    elif re.match(r"\s*$", naredba):
        continue #prazna naredba samo pokrece prompt
    else:
        if login:
            sendComand(naredba, sym_key, port)
        