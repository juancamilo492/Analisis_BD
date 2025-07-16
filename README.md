Sistema de Identificación de Clientes Potenciales 🎯
Descripción
Aplicación web desarrollada en Streamlit para identificar clientes potenciales en la industria de empaques, termoformados, fundas y bolsas para alimentos. El sistema analiza la base de datos de las 1000 empresas más grandes de Colombia y utiliza inteligencia artificial para generar informes detallados.
Características principales
🔍 Identificación Automática

Análisis de códigos CIIU para identificar empresas del sector alimenticio
Filtrado por macrosector, departamento y rango de ingresos
Cálculo automático de métricas financieras clave

📊 Análisis Financiero

Crecimiento de ingresos año a año
Margen de ganancia
Ratio de endeudamiento
Comparativas 2023 vs 2024

🤖 Análisis con IA

Integración con OpenAI GPT para análisis detallado
Evaluación del potencial como cliente
Identificación de necesidades específicas de empaque

📄 Generación de Informes

Informes PDF profesionales
Información financiera detallada por empresa
Análisis de potencial comercial

Requisitos
Software

Python 3.8 o superior
Streamlit
OpenAI API Key

Archivos necesarios

Base 1000_empresas_2025.xlsx: Base de datos de empresas
.streamlit/secrets.toml: Archivo con la API Key de OpenAI

Despliegue en Streamlit Cloud
Opción 1: Repositorio Privado (Recomendado para datos sensibles)

Crear repositorio privado en GitHub
Subir todos los archivos incluyendo el .xlsx
En Streamlit Cloud:

Conectar tu cuenta de GitHub
Seleccionar el repositorio privado
En Settings > Secrets, agregar:
OPENAI_API_KEY = "tu-api-key-aqui"




Opción 2: Repositorio Público (Sin datos sensibles)

Crear repositorio público en GitHub
NO incluir el archivo .xlsx ni secrets.toml
La aplicación permitirá cargar el archivo manualmente
En Streamlit Cloud Settings > Secrets, agregar el OPENAI_API_KEY

Configuración de Secrets en Streamlit Cloud

Ir a share.streamlit.io
Seleccionar tu app
Ir a Settings → Secrets
Agregar:
tomlOPENAI_API_KEY = "sk-..."


Instalación Local

Clonar el repositorio:

bashgit clone [url-del-repositorio]
cd Analisis_BD

Instalar dependencias:

bashpip install -r requirements.txt

Configurar API Key de OpenAI:
Crear archivo .streamlit/secrets.toml:

tomlOPENAI_API_KEY = "tu-api-key-aqui"
Uso

Ejecutar la aplicación:

bashstreamlit run app.py

La aplicación se abrirá en el navegador en http://localhost:8501
Utilizar los filtros en la barra lateral para refinar la búsqueda
Seleccionar empresas y generar informe PDF

Códigos CIIU Objetivo
La aplicación busca empresas con los siguientes códigos CIIU:

C101: Procesamiento y conservación de carne
C102: Procesamiento y conservación de pescados
C103: Procesamiento y conservación de frutas, legumbres y hortalizas
C104: Elaboración de aceites y grasas
C105: Elaboración de productos lácteos
C106: Elaboración de productos de molinería
C107: Elaboración de productos de café
C108: Elaboración de otros productos alimenticios
C109: Elaboración de alimentos para animales
C110: Elaboración de bebidas
G463: Comercio al por mayor de productos alimenticios
G472: Comercio al por menor de productos alimenticios

Estructura del Proyecto
Analisis_BD/
│
├── app.py                  # Aplicación principal de Streamlit
├── requirements.txt        # Dependencias del proyecto
├── README.md              # Este archivo
├── Base 1000_empresas_2025.xlsx  # Base de datos (no incluida)
└── .streamlit/
    └── secrets.toml       # API Keys (no incluida)
Funcionalidades Detalladas
Filtros Disponibles

Macrosector: Manufactura, Comercio, Servicios, etc.
Departamento: Filtro geográfico
Rango de Ingresos: Mínimo y máximo en millones de pesos

Métricas Calculadas

Crecimiento de Ingresos: Variación porcentual 2023-2024
Margen de Ganancia: Ganancia/Ingresos * 100
Ratio de Endeudamiento: Pasivos/Activos * 100

Informe PDF Incluye

Resumen ejecutivo
Información básica de cada empresa
Tabla de información financiera
Indicadores clave
Análisis de potencial (opcional con GPT)

Notas Importantes

Privacidad: Los datos de las empresas son confidenciales y deben manejarse según las políticas de la empresa.
Costos API: El análisis con GPT consume tokens de OpenAI. Usar con moderación.
Rendimiento: Para grandes volúmenes de empresas, el análisis GPT puede tomar varios minutos.

Soporte
Para soporte o preguntas sobre la aplicación, contactar al equipo de desarrollo.
Actualizaciones Futuras

 Exportación a Excel además de PDF
 Dashboard interactivo con gráficos
 Scoring automático de clientes
 Integración con CRM
 Histórico de análisis realizados
