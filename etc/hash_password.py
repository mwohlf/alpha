"""
Usage: python etc/hash_password.py <password>
Prints the bcrypt hash to paste into .env.dev as LOGIN_PASSWORD.
"""
import sys
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
print(pwd_context.hash(sys.argv[1]))
