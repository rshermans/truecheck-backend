import jwt
try:
    print(f"jwt.ExpiredSignatureError exists: {jwt.ExpiredSignatureError}")
except AttributeError:
    print("jwt.ExpiredSignatureError does NOT exist")
