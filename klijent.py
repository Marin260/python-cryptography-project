import socket
import getpass

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key

def remotesh(login):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', 8000))
    pub_key = sock.recv(4096)

    key = load_pem_public_key(pub_key)
    #print(isinstance(key, rsa.RSAPublicKey))

    for x in range(2):
        if x == 0:
            data = input('unesite username: ')
        elif x == 1:
            data = getpass.getpass()
        chiphertext = key.encrypt(
            data.encode(),
            padding.OAEP(
                mgf = padding.MGF1(algorithm=hashes.SHA256()),
                algorithm= hashes.SHA256(),
                label = None
            )
        )

        sock.send(chiphertext)
        
    primljeni_podaci = sock.recv(4096)
    primljeni_pozdrav = primljeni_podaci.decode()

    while primljeni_pozdrav == "False":
        print('kriva lozinka')
        data = getpass.getpass()
        chiphertext = key.encrypt(
            data.encode(),
            padding.OAEP(
                mgf = padding.MGF1(algorithm=hashes.SHA256()),
                algorithm= hashes.SHA256(),
                label = None
            )
        )

        sock.send(chiphertext)
        primljeni_podaci = sock.recv(4096)
        primljeni_pozdrav = primljeni_podaci.decode()


    if primljeni_pozdrav == "True":
        print('Uspjesna prijava')
        sym_key = Fernet.generate_key()
        login = True

        chiphertext = key.encrypt(
            sym_key,
            padding.OAEP(
                mgf = padding.MGF1(algorithm=hashes.SHA256()),
                algorithm= hashes.SHA256(),
                label = None
            )
        )
        sock.send(chiphertext)

        
    sock.close()
    return sym_key, login