from base64 import b64encode, b64decode
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

_ki = "Zk4BN2Dpt4/9WdFsSP5uFZXiBbYq+MYLwQuPFsa3M7w="
_iv = "RVlJy3sZ5II9nQTOe3Hg+Q=="

def encrypt(plain_text):
    padded_plain_text = pad(plain_text.encode(), AES.block_size)
    cipher = AES.new(b64decode(_ki), AES.MODE_CBC, b64decode(_iv))
    cipher_text = cipher.encrypt(padded_plain_text)
    return b64encode(cipher_text).decode()

def decrypt(encrypted_text):
    decoded_encrypted_text = b64decode(encrypted_text)
    cipher = AES.new(b64decode(_ki), AES.MODE_CBC, b64decode(_iv))
    padded_palin_text = cipher.decrypt(decoded_encrypted_text)
    return unpad(padded_palin_text, AES.block_size).decode()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--decrypt", action="store_true", help="decrypt text")
    parser.add_argument("text")
    args = parser.parse_args()
    print(decrypt(args.text) if args.decrypt else encrypt(args.text))

