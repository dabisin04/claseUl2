import os
import hashlib
import secrets

def generate_salt(length: int = 16) -> str:
    """Genera un salt aleatorio de la longitud especificada."""
    return secrets.token_hex(length)

def hash_password(password: str, salt: str) -> str:
    """Hashea una contraseña usando el salt proporcionado."""
    salted = password + salt
    return hashlib.sha256(salted.encode()).hexdigest()

def verify_password(password: str, hashed_password: str, salt: str) -> bool:
    """Verifica si una contraseña coincide con su hash."""
    return hash_password(password, salt) == hashed_password