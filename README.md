# EditorIA
 
## ¿Cómo funciona?

Nuestro sistema de análisis de texto de obras literarias que utiliza técnicas de procesamiento de lenguaje natural funciona mediante el uso de algoritmos de aprendizaje automático y procesamiento de texto para identificar patrones en la estructura y contenido de una obra literaria. El sistema puede analizar la sintaxis, la semántica y el contexto del texto, lo que le permite identificar temas, personajes y elementos literarios clave. Además, el sistema puede analizar la frecuencia de las palabras y el tono del texto para determinar la emoción y el estilo del autor. Estos análisis pueden ser útiles para la investigación literaria, la evaluación de la calidad de la escritura y la identificación de tendencias literarias.

# Proyecto de Automatización de Procesos con Google Cloud y OpenAI

Este repositorio contiene scripts y funciones para automatizar el procesamiento de archivos y la integración con diversas APIs, como **Google Cloud Storage**, **BigQuery**, y **OpenAI**. El sistema está diseñado para gestionar la descarga, procesamiento, y envío de archivos a usuarios, con un enfoque en la generación de resúmenes, categorización de textos, y análisis de personajes usando la API de **OpenAI**.

## Funcionalidades Principales

1. **Procesamiento de Archivos en Google Cloud Storage**:
   - Descarga y procesamiento de archivos de texto (.txt), PDF (.pdf), y documentos (.doc, .docx) almacenados en **Google Cloud Storage**.
   - Cálculo de métricas como la cantidad de palabras, caracteres con y sin espacios, y el número de imágenes en PDFs.

2. **Generación de Resúmenes y Análisis de Textos con OpenAI**:
   - Resumen de textos utilizando la API de **OpenAI**.
   - Categorización de textos en géneros literarios predefinidos.
   - Identificación de personajes y asignación de géneros.

3. **Automatización de Correos con SendGrid**:
   - Envío automático de correos electrónicos a los usuarios con los archivos procesados adjuntos, utilizando **SendGrid**.

4. **Almacenamiento y Registro en BigQuery**:
   - Inserción de datos procesados (resúmenes, categorías, etc.) en tablas de **Google BigQuery** para su almacenamiento y análisis.
   - Seguimiento de archivos enviados a los usuarios, incluyendo marcas de tiempo y correos electrónicos.

## Estructura del Proyecto

```bash
├── funciones/
│   ├── utils.py          # Funciones utilitarias para renombrar blobs, enviar correos, etc.
├── lib-ia/
│   ├── apis/             # Archivos de API keys y configuraciones
│   ├── mail_files/       # Archivos temporales de correo
├── logs/                 # Logs generados durante la ejecución
├── README.md             # Este archivo de documentación
├── main.py               # Script principal de procesamiento
└── requirements.txt      # Dependencias del proyecto
