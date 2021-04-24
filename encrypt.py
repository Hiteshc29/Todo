import hashlib

def encryption(x):
    salt = ['hiw', 'fgb', '012', 'abz', '9fe', 'yx3', 'v57', 'jkl']
    no_of_char = int(len(x) / 8)
    x = ' '.join(x[i:i + no_of_char] for i in range(0, len(x), no_of_char)).split()
    salted = []
    i = 0
    while i < 8:
        salted.append(salt[i])
        salted.append(x[0])
        x.remove(x[0])
        i = i + 1
    if x != []:
        x[:] = [''.join(x[:])]
        salted.insert(0, x[0])
    salted[:] = [''.join(salted[:])]
    hashed = hashlib.sha256(salted[0].encode('ascii')).hexdigest()
    return hashed