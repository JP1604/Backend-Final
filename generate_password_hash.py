#!/usr/bin/env python3
"""
Script para generar hash de contraseña válido
"""

from passlib.context import CryptContext

# Crear contexto de encriptación
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Generar hash para la contraseña "password"
password = "password"
hashed_password = pwd_context.hash(password)

print(f"Password: {password}")
print(f"Hash: {hashed_password}")

# Verificar que funciona
is_valid = pwd_context.verify(password, hashed_password)
print(f"Verification: {is_valid}")
