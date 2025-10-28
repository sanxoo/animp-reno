from base64 import b64encode, b64decode
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

_ki = "Zk4BN2Dpt4/9WdFsSP5uFZXiBbYq+MYLwQuPFsa3M7w="
_iv = "RVlJy3sZ5II9nQTOe3Hg+Q=="
_sv = "0FEMLDPZtdoH/w/m5HcBZA=="

def get_cipher():
    secret = PBKDF2(_ki, b64decode(_sv), 32, count=10000, hmac_hash_module=SHA256)
    return AES.new(secret, AES.MODE_CBC, b64decode(_iv))

def encrypt(plain_text):
    padded_plain_text = pad(plain_text.encode(), AES.block_size)
    cipher_text = get_cipher().encrypt(padded_plain_text)
    return b64encode(cipher_text).decode()

def decrypt(encrypted_text):
    decoded_encrypted_text = b64decode(encrypted_text)
    padded_palin_text = get_cipher().decrypt(decoded_encrypted_text)
    return unpad(padded_palin_text, AES.block_size).decode()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--decrypt", action="store_true", help="decrypt text")
    parser.add_argument("text")
    args = parser.parse_args()
    print(decrypt(args.text) if args.decrypt else encrypt(args.text))

