import os
import telebot
import asyncio
import json
from dotenv import load_dotenv
from playwright.async_api import async_playwright
import random
import string
import requests
import time
from collections import deque
import base64
from io import BytesIO

# Cargar variables de entorno
load_dotenv()
API_TOKEN = "7985710824:AAGAl5rWA14OCVNSfxgfkitzUxnX-SLy3-Q"
OWNER_ID = 6225500207
GROUP_ID = 0
RENAPER_API_KEY = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6OTQyLCJyb2xlIjoyLCJpYXQiOjE3MzI4OTEyMTh9.ZJE93rqr5TzXlJ3Tz-On9Cj9AerPc9pxMNayONJ5BSo"

bot = telebot.TeleBot(API_TOKEN)
queue = deque()
cooldown = {}
TOKENS_FILE = "tokens.json"

# --- Cargar y guardar tokens ---
def cargar_tokens():
    try:
        with open(TOKENS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def guardar_tokens(data):
    with open(TOKENS_FILE, "w") as f:
        json.dump(data, f)

user_tokens = cargar_tokens()

# --- Comando para ver tokens ---
@bot.message_handler(commands=['mistokens'])
def handle_mistokens(message):
    uid = str(message.from_user.id)
    tokens = user_tokens.get(uid, 0)
    bot.reply_to(message, f"🔐 Tenés {tokens} tokens disponibles.")

# --- Comando para agregar tokens (solo OWNER) ---
@bot.message_handler(commands=['addtokens'])
def handle_addtokens(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "⛔ No tenés permiso para usar este comando.")
        return
    args = message.text.split()
    if len(args) != 3:
        bot.reply_to(message, "Uso: /addtokens <user_id> <cantidad>")
        return
    uid, cantidad = args[1], args[2]
    if not uid.isdigit() or not cantidad.isdigit():
        bot.reply_to(message, "ID y cantidad deben ser números.")
        return
    user_tokens[uid] = user_tokens.get(uid, 0) + int(cantidad)
    guardar_tokens(user_tokens)
    bot.reply_to(message, f"✅ Se agregaron {cantidad} tokens al usuario {uid}.")

RENAPER_API_URL = "https://colmen-api.rgn.io/renaper/new"

def consultar_dni(dni, gender):
    headers = {
        "Authorization": RENAPER_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {"dni": dni, "gender": gender}
    try:
        response = requests.post(RENAPER_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        return {"error": f"Error al conectar con la API del RENAPER: {e}"}

@bot.message_handler(commands=['dni'])
def handle_dni(message):
    uid = str(message.from_user.id)
    if user_tokens.get(uid, 0) < 4:
        bot.reply_to(message, "❌ No tenés tokens suficientes. Pedile al admin que te cargue.")
        return
    args = message.text.split(" ", 2)
    if len(args) != 3:
        bot.reply_to(message, "Uso: /dni 12345678 M")
        return
    dni, gender = args[1], args[2].upper()
    if not dni.isdigit() or gender not in ["M", "F"]:
        bot.reply_to(message, "Formato inválido. Ej: /dni 12345678 M")
        return
    bot.reply_to(message, "Buscando información, un momento...")
    data = consultar_dni(dni, gender)
    if "error" in data:
        bot.reply_to(message, data["error"])
        return

    respuesta = (
        f"📄 Nombre: {data.get('nombres', 'N/A')} {data.get('apellido', 'N/A')}\n"
        f"📆 Fecha de nacimiento: {data.get('fecha_nacimiento', 'N/A')}\n"
        f"🔛 CUIL: {data.get('cuil', 'N/A')}\n"
        f"🏠 Dirección: {data.get('calle', '')} {data.get('numero', '')}, {data.get('ciudad', '')}, {data.get('provincia', '')}\n"
        f"📆 Emisión: {data.get('fecha_emision', 'N/A')} - Vencimiento: {data.get('fecha_vencimiento', 'N/A')}\n"
    )
    bot.reply_to(message, respuesta)

    if data.get('foto'):
        try:
            imagen_bytes = base64.b64decode(data['foto'])
            bot.send_photo(message.chat.id, photo=BytesIO(imagen_bytes))
        except:
            bot.reply_to(message, "No se pudo cargar la foto.")

    user_tokens[uid] -= 4
    guardar_tokens(user_tokens)

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, "🤖 ¡Hola! Enviá /check o /dni para comenzar. Usá /mistokens para ver tus tokens disponibles.")

if __name__ == "__main__":
    bot.infinity_polling()
