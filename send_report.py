# Imports necesarios
from google.cloud import storage
from funciones.utils import send_grid_mail
import pathlib
import os
from fnmatch import fnmatch
from time import sleep
from google.cloud import bigquery
from funciones.utils import rename_blob
from datetime import datetime

def open_file(filepath):
    """
    Abre un archivo y devuelve su contenido como texto.
    
    :param filepath: Ruta del archivo a abrir.
    :return: Contenido del archivo.
    """
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()

def download_blob(source_blob_name, destination_file_name):
    """
    Descarga un archivo (blob) desde Google Cloud Storage.

    :param source_blob_name: Nombre del blob a descargar.
    :param destination_file_name: Ruta donde se guardará el archivo descargado.
    """
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)
    print(f"Blob {source_blob_name} descargado exitosamente a {destination_file_name}.")

def get_filename_without_extension(file_name):
    """
    Obtiene el nombre del archivo sin su extensión.
    
    :param file_name: Nombre del archivo con extensión.
    :return: Nombre del archivo sin extensión.
    """
    extension = file_name.split(".")[-1]
    return file_name[:-len(extension)-1]

# Carga la API key de SendGrid
api_sendgrid = open_file('/home/maruaran/lib-ia/apis/api_sendgrid.txt')

# Inicializa el cliente de BigQuery
bqclient = bigquery.Client()

# Consulta para obtener los registros pendientes de envío de correo
query = """
    SELECT *
    FROM `lib-ia.d_client_info.f_request_stage1_view`
    WHERE datetime_sent IS NULL
    AND uri_output IS NOT NULL
    AND email IS NOT NULL
    AND output_type = 'XLSX'
"""
query_job = bqclient.query(query).to_dataframe()

# Inicializa el cliente de Google Cloud Storage
storage_client = storage.Client()
bucket_name = "lib-ia"
bucket = storage_client.get_bucket(bucket_name)

# Itera sobre los registros obtenidos de la consulta
for index, registro in query_job.iterrows():
    print(registro.text_name)
    print(registro.uuid)

    # Extrae el nombre del archivo desde la URI
    file_name = os.path.basename(registro.uri_output)
    print(file_name)
    print(registro.uri_output)

    # Ajusta la URI para acceder correctamente al blob en Cloud Storage
    uri_path = registro.uri_output.replace('lib-ia/', '')
    print(uri_path)
    
    # Descarga el archivo desde Cloud Storage a la carpeta local 'mail_files'
    download_blob(uri_path, 'lib-ia/mail_files/' + file_name)
    sleep(0.1)

    # Prepara los datos para insertar en BigQuery
    table_id = "lib-ia.d_client_info.f_request_sent"
    rows_to_insert = [
        {"uuid": registro.uuid, 'datetime_sent': str(datetime.now()), 'mail_sent': registro.email, 'stage': registro.stage}
    ]

    print(rows_to_insert)
    
    # Inserta los datos en BigQuery
    errors = bqclient.insert_rows_json(table_id, rows_to_insert)
    if not errors:
        print("Se han agregado nuevas filas.")
        
        # Envía un correo usando SendGrid con el archivo adjunto
        send_grid_mail(api_sendgrid, registro.email, 'hola@dataimpacta.com', 'lib-ia/mail_files/' + file_name, file_name)
        
        # Renombra el archivo en el bucket, moviéndolo a la carpeta 'sent_stage1'
        rename_blob(bucket_name, file_name, 'reportes/sent_stage1/' + str(datetime.now()) + '_' + file_name)
    else:
        print(f"Errores al insertar filas: {errors}")

# Limpia la carpeta 'mail_files', eliminando archivos XLSX procesados
for dirpath, dirnames, filenames in os.walk('lib-ia/mail_files'):
    for file in filenames:
        if fnmatch(file, '*.xlsx'):
            os.remove(os.path.join(dirpath, file))
