import asyncio
import requests
from telethon import TelegramClient, events
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import os
from telethon.errors import PeerIdInvalidError

# Configuración del cliente de Telegram para la primera cuenta
API_ID_1 = '9161657'
API_HASH_1 = '400dafb52292ea01a8cf1e5c1756a96a'
PHONE_NUMBER_1 = '+51981119038'

# Configuración del cliente de Telegram para la segunda cuenta
API_ID_2 = '24994755'
API_HASH_2 = '83c4d6c5ab28171766cb4b67f900d185'
PHONE_NUMBER_2 = '+51944865840'

# Inicializar clientes de Telegram para las dos cuentas
client_1 = TelegramClient('mi_sesion_token_1', API_ID_1, API_HASH_1)
client_2 = TelegramClient('mi_sesion_token_2', API_ID_2, API_HASH_2)

# Usuario administrador
ADMIN_USER = 'Asteriscom'

# Archivo JSON para almacenar permisos y URLs
ARCHIVO_PERMISOS = 'memoria_permisos.json'
ARCHIVO_URLS = 'memoria_urls.json'

# Diccionario para almacenar permisos con fecha de expiración
permisos = {}

# Máximo de intentos antes de bloquear temporalmente
MAX_INTENTOS = 5
BLOQUEO_TIEMPO = timedelta(hours=2)

# Lista de URLs asociadas a cada comando
URLS = {
    'vip': {},
    'gold': {}
}

# Cargar permisos y URLs desde los archivos JSON
def cargar_permisos():
    if os.path.exists(ARCHIVO_PERMISOS):
        with open(ARCHIVO_PERMISOS, 'r') as archivo:
            datos = json.load(archivo)
            for usuario, tiempo in datos.items():
                permisos[usuario] = {
                    'nivel': tiempo['nivel'],
                    'expiracion': datetime.fromisoformat(tiempo['expiracion'])
                }

def cargar_urls():
    if os.path.exists(ARCHIVO_URLS):
        with open(ARCHIVO_URLS, 'r') as archivo:
            datos = json.load(archivo)
            URLS.update(datos)

# Guardar permisos y URLs en los archivos JSON
def guardar_permisos():
    datos = {usuario: {'nivel': permiso['nivel'], 'expiracion': permiso['expiracion'].isoformat()} for usuario, permiso in permisos.items()}
    with open(ARCHIVO_PERMISOS, 'w') as archivo:
        json.dump(datos, archivo)

def guardar_urls():
    with open(ARCHIVO_URLS, 'w') as archivo:
        json.dump(URLS, archivo)

# Función para obtener datos de las URLs
async def obtener_datos(url):
    """Extrae el usuario, contraseña y token del HTML de la URL proporcionada."""
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            usuario = soup.find(string="Usuario:").find_next('input')['value']
            password = soup.find(string="Contraseña:").find_next('input')['value']
            token = soup.find(string="Token:").find_next('input')['value']

            return usuario, password, token
        else:
            return None, None, None
    except Exception as e:
        print(f"Error al obtener los datos de la URL {url}: {str(e)}")
        return None, None, None

async def manejar_comando(event, url, client):
    """Maneja la respuesta para cualquier comando registrado en la lista URLS."""
    sender = await event.get_sender()
    username = sender.username

    # Verificar si el usuario tiene permisos y si no ha expirado
    if username in permisos:
        if permisos[username]['expiracion'] > datetime.now():
            usuario, password, token = await obtener_datos(url)

            if usuario and password and token:
                chat_id = event.chat_id
                
                try:
                    # Enviar cada dato individualmente
                    await client.send_message(chat_id, f" {usuario}")
                    await client.send_message(chat_id, f" {password}")
                    await client.send_message(chat_id, f" {token}")
                except PeerIdInvalidError:
                    await client.send_message(event.chat_id, f"❌ No se pudo enviar el mensaje a @{username}. Asegúrate de que el usuario haya iniciado una conversación con el bot.")
            else:
                await client.send_message(event.chat_id, "❌ Error al obtener los datos del token.")
        else:
            await client.send_message(event.chat_id, "❌ Tu membresía ha caducado contactate con @Asteriscom.")
    else:
        await client.send_message(event.chat_id, "❌ No estás autorizado para usar este comando.")

# Comandos para otorgar permisos temporales
@client_1.on(events.NewMessage(pattern=r'/vip(\d) (.+)'))
@client_2.on(events.NewMessage(pattern=r'/vip(\d) (.+)'))
async def otorgar_vip(event):
    # Verificar si el mensaje es privado
    if not event.is_private:
        return
    
    sender = await event.get_sender()
    username = sender.username
    client = event.client
    
    if username == ADMIN_USER:
        dias = int(event.pattern_match.group(1))
        nuevo_usuario = event.pattern_match.group(2).lstrip('@')  # Eliminar '@' del nombre de usuario si está presente
        permisos[nuevo_usuario] = {'nivel': 'vip', 'expiracion': datetime.now() + timedelta(days=dias)}
        
        # Guardar los permisos actualizados en JSON
        guardar_permisos()
        
        try:
            # Enviar confirmación al administrador y al usuario específico
            await client.send_message(event.chat_id, f"🎉 ¡Felicidades @{nuevo_usuario}, ahora cuentas con privilegios VIP para poder consultar por {dias} días!")
            await client.send_message(nuevo_usuario, f"🎉 ¡Hola @{nuevo_usuario}, has recibido membresía VIP para consultar durante {dias} días!")
        except PeerIdInvalidError:
            await client.send_message(event.chat_id, f"❌ No se pudo enviar el mensaje a @{nuevo_usuario}. Asegúrate de que el usuario haya iniciado una conversación con el bot.")
    else:
        await client.send_message(event.chat_id, "❌ No tienes permiso para otorgar privilegios.")

@client_1.on(events.NewMessage(pattern=r'/gold(\d) (.+)'))
@client_2.on(events.NewMessage(pattern=r'/gold(\d) (.+)'))
async def otorgar_gold(event):
    # Verificar si el mensaje es privado
    if not event.is_private:
        return
    
    sender = await event.get_sender()
    username = sender.username
    client = event.client
    
    if username == ADMIN_USER:
        dias = int(event.pattern_match.group(1))
        nuevo_usuario = event.pattern_match.group(2).lstrip('@')  # Eliminar '@' del nombre de usuario si está presente
        permisos[nuevo_usuario] = {'nivel': 'gold', 'expiracion': datetime.now() + timedelta(days=dias)}
        
        # Guardar los permisos actualizados en JSON
        guardar_permisos()
        
        try:
            # Enviar confirmación al administrador y al usuario específico
            await client.send_message(event.chat_id, f"🎖 ¡Felicidades @{nuevo_usuario}, ahora cuentas con privilegios GOLD para poder consultar por {dias} días!")
            await client.send_message(nuevo_usuario, f"🎖 ¡Hola @{nuevo_usuario}, has recibido membresía GOLD para consultar durante {dias} días!")
        except PeerIdInvalidError:
            await client.send_message(event.chat_id, f"❌ No se pudo enviar el mensaje a @{nuevo_usuario}. Asegúrate de que el usuario haya iniciado una conversación con el bot.")
    else:
        await client.send_message(event.chat_id, "❌ No tienes permiso para otorgar privilegios.")

# Comandos para actualizar URLs
@client_1.on(events.NewMessage(pattern=r'/actualizar (\w+) (.+)'))
@client_2.on(events.NewMessage(pattern=r'/actualizar (\w+) (.+)'))
async def actualizar_url(event):
    # Verificar si el mensaje es privado
    if not event.is_private:
        return
    
    sender = await event.get_sender()
    username = sender.username
    client = event.client
    
    if username == ADMIN_USER:
        comando = event.pattern_match.group(1)
        nueva_url = event.pattern_match.group(2)
        
        for categoria in URLS.values():
            if comando in categoria:
                categoria[comando] = nueva_url
                # Guardar las URLs actualizadas en JSON
                guardar_urls()
                await client.send_message(event.chat_id, f"🔄 La URL para el comando /{comando} ha sido actualizada correctamente.")
                return
        
        await client.send_message(event.chat_id, f"❌ El comando /{comando} no existe.")
    else:
        await client.send_message(event.chat_id, "❌ No tienes permiso para actualizar URLs.")

# Cargar permisos y URLs al iniciar el bot
cargar_permisos()
cargar_urls()

# Registrar los comandos dinámicamente solo para usuarios con permisos
def registrar_comandos(client):
    for comando, url in URLS['vip'].items():
        @client.on(events.NewMessage(pattern=fr'/{comando}'))
        async def evento_handler(event, url=url):
            if event.is_private:
                await manejar_comando(event, url, client)
    for comando, url in URLS['gold'].items():
        @client.on(events.NewMessage(pattern=fr'/{comando}'))
        async def evento_handler(event, url=url):
            if event.is_private:
                await manejar_comando(event, url, client)

registrar_comandos(client_1)
registrar_comandos(client_2)

# Conexión persistente con reconexión automática en caso de error o caída de Internet
async def main():
    while True:
        try:
            await client_1.start(PHONE_NUMBER_1)
            await client_2.start(PHONE_NUMBER_2)
            print("Bots de token conectados y funcionando.")
            await asyncio.gather(
                client_1.run_until_disconnected(),
                client_2.run_until_disconnected()
            )
        except Exception as e:
            print(f"Error detectado: {e}. Reintentando en 5 segundos...")
            await asyncio.sleep(5)  # Esperar unos segundos antes de intentar reconectar

# Iniciar los clientes de Telegram
with client_1, client_2:
    client_1.loop.run_until_complete(main())

