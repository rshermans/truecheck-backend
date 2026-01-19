import jwt
try:
    print(f"jwt.JWTError exists: {jwt.JWTError}")
except AttributeError:
    print("jwt.JWTError does NOT exist")

try:
    print(f"jwt.PyJWTError exists: {jwt.PyJWTError}")
except AttributeError:
    print("jwt.PyJWTError does NOT exist")
