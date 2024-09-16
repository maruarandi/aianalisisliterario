# Librerías necesarias
import pandas as pd
import textwrap
import re
import openai
from time import time, sleep
from datetime import datetime
from google.cloud import bigquery
from funciones.utils import replace_similar_strings, rename_blob
import os
import pathlib
import PyPDF2
import subprocess
import logging
import fcntl
import sys

# Google Cloud Storage client
from google.cloud import storage

# Archivo de bloqueo para evitar múltiples ejecuciones simultáneas
LOCK_FILE = '/tmp/my_script.lock'

def acquire_lock():
    """
    Adquiere un bloqueo de archivo para evitar que múltiples instancias del script se ejecuten simultáneamente.
    """
    try:
        lockfile = open(LOCK_FILE, 'w')
        fcntl.lockf(lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        print("El script ya está en ejecución. Saliendo.")
        sys.exit(1)

def release_lock():
    """
    Libera el bloqueo del archivo y cierra el archivo de bloqueo.
    """
    lockfile = open(LOCK_FILE, 'w')
    fcntl.lockf(lockfile, fcntl.LOCK_UN)
    lockfile.close()

def open_file(filepath):
    """
    Abre un archivo en modo de lectura y devuelve su contenido.
    
    :param filepath: Ruta del archivo a leer.
    :return: Contenido del archivo.
    """
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()

def save_file(content, filepath):
    """
    Guarda el contenido en un archivo de texto.

    :param content: Contenido a guardar.
    :param filepath: Ruta del archivo donde se guardará.
    """
    with open(filepath, 'w', encoding='utf-8') as outfile:
        outfile.write(content)

def summarizador(text):
    """
    Utiliza la API de OpenAI para resumir un texto y extraer los personajes y géneros.

    :param text: Texto a resumir.
    :return: Respuesta de la API de OpenAI con el resumen y personajes.
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "assistant", "content": "Soy un experto en resumir textos y analizar su contenido."},
            {"role": "user", "content": "Necesito que resumas este texto en 15 palabras máximo... Este es el texto para resumir: " + str(text)}
        ]
    )
    return response

def categoria(text):
    """
    Utiliza la API de OpenAI para categorizar un texto según un listado de categorías predefinidas.

    :param text: Texto a categorizar.
    :return: Respuesta de la API de OpenAI con la categoría asignada.
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "assistant", "content": "Soy un experto en categorizar libros en las siguientes categorías..."},
            {"role": "user", "content": "¿En qué categoría entra este texto? " + str(text)}
        ],
        temperature=0
    )
    return response

def summarizador_resumen(previous_text, text):
    """
    Utiliza la API de OpenAI para generar un resumen que combine un texto previo y el texto actual.

    :param previous_text: Texto previo utilizado como contexto.
    :param text: Texto actual a resumir.
    :return: Resumen generado por OpenAI.
    """
    system_message = {"role": "system", "content": "Este es el resumen previo: " + previous_text}
    user_message = {"role": "user", "content": "Contame de qué se trata el texto en 300 palabras máximo... Este es el texto: " + text}

    messages = [system_message, user_message]

    retries = 0
    max_retries = 5
    retry_delay = 5

    while retries < max_retries:
        try:
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=" ".join([m["content"] for m in messages]),
                temperature=0.4,
                max_tokens=1048,
                n=1,
                stop=None,
                timeout=15,
            )
            return response.choices[0].text.strip()
        except openai.error.ServiceUnavailableError as e:
            print(f"Error: {e}. Reintentando en {retry_delay} segundos...")
            sleep(retry_delay)
            retries += 1

    raise Exception("No se pudo obtener una respuesta válida.")

def sinopsis(text):
    """
    Genera una sinopsis del texto usando la API de OpenAI.

    :param text: Texto a analizar para crear una sinopsis.
    :return: Sinopsis generada.
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": 'Sos una IA que redacta mejores sinopsis de libros.'},
            {"role": "user", "content": "Este es el texto: " + str(text)}
        ]
    )
    return response

def similar_books(text):
    """
    Recomienda libros similares basados en el texto proporcionado.

    :param text: Texto de un libro para analizar.
    :return: Lista de libros similares generada por OpenAI.
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "assistant", "content": "Sos una IA bibliotecaria que recomienda libros similares..."},
            {"role": "user", "content": "Qué libros similares a este podés recomendar, respondé en formato lista: " + str(text)}
        ]
    )
    return response

def potential_clientes(text):
    """
    Identifica el público potencial de un libro usando la API de OpenAI.

    :param text: Resumen del libro para identificar el público.
    :return: Descripción del público potencial.
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "assistant", "content": "Sos una IA experta en marketing..."},
            {"role": "user", "content": "¿Qué público potencial tiene este libro? Responder en 50 palabras."}
        ]
    )
    return response

def len_chars(alltext):
    """
    Calcula la longitud de un texto con y sin espacios.

    :param alltext: Texto para analizar.
    :return: Cantidad de caracteres con y sin espacios.
    """
    chars_without_spaces = re.findall(r'[^\s]', alltext)
    chars_with_spaces = re.findall(r'.', alltext)
    return len(chars_without_spaces), len(chars_with_spaces)

def len_images(read_pdf):
    """
    Cuenta el número de imágenes en un archivo PDF.

    :param read_pdf: Objeto PDF para analizar.
    :return: Número total de imágenes en el PDF.
    """
    num_images = 0
    for page in range(len(read_pdf.pages)):
        page_obj = read_pdf.pages[page]
        if '/XObject' in page_obj['/Resources']:
            xObject = page_obj['/Resources']['/XObject'].get_object()
            for obj in xObject:
                if xObject[obj]['/Subtype'] == '/Image':
                    num_images += 1
    return num_images

def main():
    """
    Función principal que coordina el procesamiento de archivos, resumen, categorización y carga en BigQuery.
    """
    acquire_lock()
    try:
        # Inicializa el cliente de Google Cloud Storage y BigQuery
        storage_client = storage.Client()
        bqclient = bigquery.Client()
        bucket_name = "lib-ia"
        bucket = storage_client.get_bucket(bucket_name)

        # Lista de archivos en el bucket que requieren procesamiento
        blobs = storage_client.list_blobs(bucket_name)
        requests = [blob.name for blob in blobs if not blob.name.endswith('/') and pathlib.PurePath(blob.name).parent.name == 'request_stage1']

        if requests:
            logging.basicConfig(filename=f'lib-ia/logs/log_{str(datetime.now())}.log', level=logging.DEBUG)
            for libro in requests:
                logging.info(f'{datetime.now()} Libro {libro}')
                # Procesar libros de diferentes formatos (.txt, .pdf, .doc, .docx)
                # ...

                # Resumir, analizar personajes, categorizar y guardar en BigQuery
                # ...
        else:
            print('No hay libros nuevos')

    finally:
        release_lock()

if __name__ == '__main__':
    main()
