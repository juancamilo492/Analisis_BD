import streamlit as st
import pandas as pd
import numpy as np
import openai
from datetime import datetime
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
import io
import json

# Configuración de la página
st.set_page_config(
    page_title="Identificador de Clientes Potenciales",
    page_icon="📦",
    layout="wide"
)

# Obtener API key de OpenAI
openai_key = st.secrets["OPENAI_API_KEY"]
openai.api_key = openai_key

# Título principal
st.title("🎯 Identificador de Clientes Potenciales")
st.markdown("### Sistema de análisis para empresas de empaques y termoformados")

# Códigos CIIU de interés para la industria de empaques
CIIU_OBJETIVO = {
    'C101': 'Procesamiento y conservación de carne',
    'C102': 'Procesamiento y conservación de pescados',
    'C103': 'Procesamiento y conservación de frutas, legumbres y hortalizas',
    'C104': 'Elaboración de aceites y grasas',
    'C105': 'Elaboración de productos lácteos',
    'C106': 'Elaboración de productos de molinería',
    'C107': 'Elaboración de productos de café',
    'C108': 'Elaboración de otros productos alimenticios',
    'C109': 'Elaboración de alimentos para animales',
    'G463': 'Comercio al por mayor de productos alimenticios',
    'G472': 'Comercio al por menor de productos alimenticios',
    'C110': 'Elaboración de bebidas',
    'C120': 'Elaboración de productos de tabaco',
    'A011': 'Cultivos agrícolas',
    'A012': 'Cultivos permanentes',
    'C201': 'Fabricación de sustancias químicas básicas',
    'C202': 'Fabricación de otros productos químicos',
    'C210': 'Fabricación de productos farmacéuticos'
}

def cargar_datos():
    """Carga y procesa el archivo Excel"""
    try:
        # Intentar cargar desde diferentes fuentes
        archivo_excel = None
        
        # Opción 1: Archivo cargado por el usuario
        uploaded_file = st.file_uploader(
            "Cargar archivo de base de datos (Excel)", 
            type=['xlsx', 'xls'],
            help="Sube el archivo 'Base 1000_empresas_2025.xlsx'"
        )
        
        if uploaded_file is not None:
            archivo_excel = uploaded_file
        # Opción 2: Archivo en el repositorio (para desarrollo local)
        elif os.path.exists('Base 1000_empresas_2025.xlsx'):
            archivo_excel = 'Base 1000_empresas_2025.xlsx'
        else:
            st.warning("Por favor, carga el archivo de base de datos Excel.")
            return None
        
        # Cargar el archivo Excel
        df = pd.read_excel(archivo_excel, 
                          skiprows=4,
                          names=['No', 'NIT', 'RAZON_SOCIAL', 'SUPERVISOR', 'REGION', 
                                'DEPARTAMENTO', 'CIUDAD', 'CIIU', 'MACROSECTOR', 
                                'INGRESOS_2024', 'GANANCIA_2024', 'ACTIVOS_2024', 
                                'PASIVOS_2024', 'PATRIMONIO_2024', 'INGRESOS_2023', 
                                'GANANCIA_2023', 'ACTIVOS_2023', 'PASIVOS_2023', 
                                'PATRIMONIO_2023', 'GRUPO_NIIF'])
        
        # Limpiar datos
        df = df[df['RAZON_SOCIAL'].notna()]
        df = df[df['RAZON_SOCIAL'] != 'RAZON SOCIAL']
        
        # Convertir columnas numéricas
        numeric_columns = ['INGRESOS_2024', 'GANANCIA_2024', 'ACTIVOS_2024', 
                          'PASIVOS_2024', 'PATRIMONIO_2024', 'INGRESOS_2023', 
                          'GANANCIA_2023', 'ACTIVOS_2023', 'PASIVOS_2023', 
                          'PATRIMONIO_2023']
        
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        st.success("✅ Base de datos cargada correctamente")
        return df
    except Exception as e:
        st.error(f"Error al cargar el archivo: {str(e)}")
        return None

def identificar_clientes_potenciales(df):
    """Identifica empresas objetivo basadas en código CIIU"""
    # Crear una copia para trabajar
    df_trabajo = df.copy()
    
    # Asegurar que CIIU sea string
    df_trabajo['CIIU'] = df_trabajo['CIIU'].astype(str)
    
    # Identificar empresas con CIIU objetivo
    df_trabajo['ES_CLIENTE_POTENCIAL'] = df_trabajo['CIIU'].apply(
        lambda x: any(str(x).startswith(codigo) for codigo in CIIU_OBJETIVO.keys()) if pd.notna(x) and x != 'nan' else False
    )
    
    # Extraer código CIIU base
    df_trabajo['CIIU_BASE'] = df_trabajo['CIIU'].apply(
        lambda x: str(x)[:4] if pd.notna(x) and x != 'nan' else ''
    )
    
    # Calcular métricas financieras
    df_trabajo['CRECIMIENTO_INGRESOS'] = (
        (df_trabajo['INGRESOS_2024'] - df_trabajo['INGRESOS_2023']) / 
        df_trabajo['INGRESOS_2023'] * 100
    ).round(2)
    
    df_trabajo['MARGEN_GANANCIA_2024'] = (
        df_trabajo['GANANCIA_2024'] / df_trabajo['INGRESOS_2024'] * 100
    ).round(2)
    
    df_trabajo['RATIO_ENDEUDAMIENTO'] = (
        df_trabajo['PASIVOS_2024'] / df_trabajo['ACTIVOS_2024'] * 100
    ).round(2)
    
    # Reemplazar infinitos y NaN con 0
    df_trabajo['CRECIMIENTO_INGRESOS'] = df_trabajo['CRECIMIENTO_INGRESOS'].replace([np.inf, -np.inf], 0).fillna(0)
    df_trabajo['MARGEN_GANANCIA_2024'] = df_trabajo['MARGEN_GANANCIA_2024'].replace([np.inf, -np.inf], 0).fillna(0)
    df_trabajo['RATIO_ENDEUDAMIENTO'] = df_trabajo['RATIO_ENDEUDAMIENTO'].replace([np.inf, -np.inf], 0).fillna(0)
    
    return df_trabajo

def analizar_empresa_con_gpt(empresa_data):
    """Usa GPT para analizar por qué una empresa sería un buen cliente"""
    prompt = f"""
    Analiza la siguiente empresa como cliente potencial para una compañía que vende 
    fundas, termoformados, empaques y bolsas para alimentos:
    
    Empresa: {empresa_data['RAZON_SOCIAL']}
    Actividad (CIIU): {empresa_data['CIIU']}
    Macrosector: {empresa_data['MACROSECTOR']}
    Ubicación: {empresa_data['CIUDAD']}, {empresa_data['DEPARTAMENTO']}
    Ingresos 2024: ${empresa_data['INGRESOS_2024']:,.0f} (miles de pesos)
    Crecimiento de ingresos: {empresa_data['CRECIMIENTO_INGRESOS']:.1f}%
    Margen de ganancia: {empresa_data['MARGEN_GANANCIA_2024']:.1f}%
    Activos totales: ${empresa_data['ACTIVOS_2024']:,.0f} (miles de pesos)
    
    Proporciona un análisis conciso (máximo 150 palabras) explicando:
    1. Por qué sería un buen cliente para empaques
    2. Qué tipo de empaques probablemente necesitaría
    3. Su solidez financiera para ser un cliente confiable
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un analista de negocios experto en la industria de empaques."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Análisis no disponible: {str(e)}"

def generar_pdf(empresas_seleccionadas):
    """Genera un informe PDF con las empresas seleccionadas"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=24,
        textColor=colors.HexColor('#1f4e79'),
        alignment=TA_CENTER
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2e75b6'),
        spaceAfter=20
    )
    
    # Título del documento
    story.append(Paragraph("INFORME DE CLIENTES POTENCIALES", title_style))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(f"Generado el {datetime.now().strftime('%d/%m/%Y')}", styles['Normal']))
    story.append(Spacer(1, 0.5*inch))
    
    # Resumen ejecutivo
    story.append(Paragraph("RESUMEN EJECUTIVO", subtitle_style))
    resumen = f"""
    Se han identificado {len(empresas_seleccionadas)} empresas como clientes potenciales 
    para productos de empaque y termoformado. Estas empresas operan en sectores relacionados 
    con alimentos, bebidas y productos que requieren soluciones de empaque especializadas.
    """
    story.append(Paragraph(resumen, styles['BodyText']))
    story.append(Spacer(1, 0.3*inch))
    
    # Análisis por empresa
    for idx, empresa in empresas_seleccionadas.iterrows():
        # Nueva página para cada empresa
        if idx > 0:
            story.append(PageBreak())
        
        # Información de la empresa
        story.append(Paragraph(f"{idx + 1}. {empresa['RAZON_SOCIAL']}", subtitle_style))
        
        # Tabla de información básica
        data = [
            ['NIT:', empresa['NIT']],
            ['Actividad (CIIU):', empresa['CIIU']],
            ['Macrosector:', empresa['MACROSECTOR']],
            ['Ubicación:', f"{empresa['CIUDAD']}, {empresa['DEPARTAMENTO']}"],
            ['Región:', empresa['REGION']]
        ]
        
        t = Table(data, colWidths=[2*inch, 4*inch])
        t.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2e75b6')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.2*inch))
        
        # Información financiera
        story.append(Paragraph("Información Financiera (miles de pesos)", styles['Heading3']))
        
        financial_data = [
            ['Concepto', '2024', '2023', 'Variación'],
            ['Ingresos Operacionales', 
             f"${empresa['INGRESOS_2024']:,.0f}" if pd.notna(empresa['INGRESOS_2024']) else 'N/D',
             f"${empresa['INGRESOS_2023']:,.0f}" if pd.notna(empresa['INGRESOS_2023']) else 'N/D',
             f"{empresa['CRECIMIENTO_INGRESOS']:.1f}%" if pd.notna(empresa['CRECIMIENTO_INGRESOS']) else 'N/D'],
            ['Ganancia/Pérdida', 
             f"${empresa['GANANCIA_2024']:,.0f}" if pd.notna(empresa['GANANCIA_2024']) else 'N/D',
             f"${empresa['GANANCIA_2023']:,.0f}" if pd.notna(empresa['GANANCIA_2023']) else 'N/D',
             '-'],
            ['Total Activos', 
             f"${empresa['ACTIVOS_2024']:,.0f}" if pd.notna(empresa['ACTIVOS_2024']) else 'N/D',
             f"${empresa['ACTIVOS_2023']:,.0f}" if pd.notna(empresa['ACTIVOS_2023']) else 'N/D',
             '-'],
            ['Total Pasivos', 
             f"${empresa['PASIVOS_2024']:,.0f}" if pd.notna(empresa['PASIVOS_2024']) else 'N/D',
             f"${empresa['PASIVOS_2023']:,.0f}" if pd.notna(empresa['PASIVOS_2023']) else 'N/D',
             '-'],
            ['Total Patrimonio', 
             f"${empresa['PATRIMONIO_2024']:,.0f}" if pd.notna(empresa['PATRIMONIO_2024']) else 'N/D',
             f"${empresa['PATRIMONIO_2023']:,.0f}" if pd.notna(empresa['PATRIMONIO_2023']) else 'N/D',
             '-']
        ]
        
        ft = Table(financial_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1*inch])
        ft.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e75b6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        story.append(ft)
        story.append(Spacer(1, 0.2*inch))
        
        # Indicadores clave
        story.append(Paragraph("Indicadores Clave", styles['Heading3']))
        indicators = f"""
        • Margen de Ganancia 2024: {empresa['MARGEN_GANANCIA_2024']:.1f}%
        • Ratio de Endeudamiento: {empresa['RATIO_ENDEUDAMIENTO']:.1f}%
        • Grupo NIIF: {empresa['GRUPO_NIIF']}
        """
        story.append(Paragraph(indicators, styles['BodyText']))
        story.append(Spacer(1, 0.2*inch))
        
        # Análisis GPT
        if 'ANALISIS_GPT' in empresa and pd.notna(empresa['ANALISIS_GPT']):
            story.append(Paragraph("Análisis de Potencial como Cliente", styles['Heading3']))
            story.append(Paragraph(empresa['ANALISIS_GPT'], styles['BodyText']))
    
    # Generar PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

# Interfaz principal de Streamlit
def main():
    # Sidebar con filtros
    st.sidebar.header("⚙️ Configuración y Filtros")
    
    # Cargar datos
    if 'df' not in st.session_state:
        df = cargar_datos()
        if df is not None:
            st.session_state.df = identificar_clientes_potenciales(df)
            st.session_state.archivo_cargado = True
    
    if 'df' in st.session_state and st.session_state.get('archivo_cargado', False):
        df = st.session_state.df
        
        # Estadísticas generales
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Empresas", len(df))
        with col2:
            clientes_potenciales = df[df['ES_CLIENTE_POTENCIAL']].shape[0]
            st.metric("Clientes Potenciales", clientes_potenciales)
        with col3:
            st.metric("Sectores Objetivo", len(CIIU_OBJETIVO))
        with col4:
            st.metric("Departamentos", df['DEPARTAMENTO'].nunique())
        
        st.markdown("---")
        
        # Filtros en sidebar
        st.sidebar.subheader("Filtros de Búsqueda")
        
        # Filtro por CIIU
        st.sidebar.subheader("🔍 Filtro por Código CIIU")
        
        # Opción de búsqueda o selección
        filtro_ciiu_modo = st.sidebar.radio(
            "Modo de selección CIIU:",
            ["Clientes Potenciales Predefinidos", "Búsqueda Personalizada", "Selección Manual"]
        )
        
        ciiu_seleccionados = []
        
        if filtro_ciiu_modo == "Clientes Potenciales Predefinidos":
            # Mostrar solo los CIIU objetivo predefinidos
            st.sidebar.info("Códigos CIIU de industrias objetivo para empaques")
            usar_predefinidos = st.sidebar.checkbox("Usar todos los códigos predefinidos", value=True)
            
            if usar_predefinidos:
                ciiu_seleccionados = list(CIIU_OBJETIVO.keys())
            else:
                for codigo, descripcion in CIIU_OBJETIVO.items():
                    if st.sidebar.checkbox(f"{codigo}: {descripcion}", value=True, key=f"ciiu_{codigo}"):
                        ciiu_seleccionados.append(codigo)
        
        elif filtro_ciiu_modo == "Búsqueda Personalizada":
            # Búsqueda por texto en CIIU
            busqueda_ciiu = st.sidebar.text_input(
                "Buscar código CIIU (ej: C101, G463)",
                placeholder="Ingrese código CIIU..."
            )
            
            if busqueda_ciiu:
                # Buscar coincidencias
                df_ciiu_match = df[df['CIIU'].astype(str).str.contains(busqueda_ciiu.upper(), na=False)]
                ciiu_encontrados = df_ciiu_match['CIIU'].unique()
                
                if len(ciiu_encontrados) > 0:
                    st.sidebar.success(f"Se encontraron {len(ciiu_encontrados)} códigos CIIU")
                    ciiu_seleccionados = [str(ciiu) for ciiu in ciiu_encontrados]
                    
                    # Mostrar los CIIU encontrados
                    with st.sidebar.expander("Ver códigos encontrados"):
                        for ciiu in ciiu_encontrados[:10]:  # Mostrar máximo 10
                            st.write(f"• {ciiu}")
                        if len(ciiu_encontrados) > 10:
                            st.write(f"... y {len(ciiu_encontrados) - 10} más")
                else:
                    st.sidebar.warning("No se encontraron códigos CIIU con ese criterio")
        
        else:  # Selección Manual
            # Obtener todos los CIIU únicos
            todos_ciiu = sorted(df['CIIU'].dropna().unique())
            
            # Agrupar por los primeros 4 caracteres
            ciiu_grupos = {}
            for ciiu in todos_ciiu:
                grupo = str(ciiu)[:4]
                if grupo not in ciiu_grupos:
                    ciiu_grupos[grupo] = []
                ciiu_grupos[grupo].append(str(ciiu))
            
            # Mostrar por grupos para mejor organización
            st.sidebar.info(f"Total de códigos CIIU únicos: {len(todos_ciiu)}")
            
            # Selector de grupos
            grupos_seleccionados = st.sidebar.multiselect(
                "Seleccionar grupos CIIU:",
                options=sorted(ciiu_grupos.keys()),
                default=list(CIIU_OBJETIVO.keys())
            )
            
            # Mostrar checkboxes para los CIIU de los grupos seleccionados
            if grupos_seleccionados:
                with st.sidebar.expander("Seleccionar códigos específicos"):
                    for grupo in grupos_seleccionados:
                        st.write(f"**Grupo {grupo}:**")
                        for ciiu in ciiu_grupos[grupo]:
                            if st.checkbox(ciiu, value=True, key=f"manual_{ciiu}"):
                                ciiu_seleccionados.append(ciiu)
        
        # Filtro por macrosector
        st.sidebar.subheader("📊 Otros Filtros")
        macrosectores = ['Todos'] + sorted(df['MACROSECTOR'].unique().tolist())
        macrosector_sel = st.sidebar.selectbox("Macrosector", macrosectores)
        
        # Filtro por departamento
        departamentos = ['Todos'] + sorted(df['DEPARTAMENTO'].unique().tolist())
        depto_sel = st.sidebar.selectbox("Departamento", departamentos)
        
        # Filtro por rango de ingresos
        st.sidebar.subheader("💰 Rango de Ingresos 2024 (millones)")
        ingresos_min = st.sidebar.number_input("Mínimo", value=0, step=1000)
        ingresos_max = st.sidebar.number_input("Máximo", value=int(df['INGRESOS_2024'].max()/1000), step=1000)
        
        # Aplicar filtros
        if filtro_ciiu_modo == "Clientes Potenciales Predefinidos" and usar_predefinidos:
            # Usar el filtro original de ES_CLIENTE_POTENCIAL
            df_filtrado = df[df['ES_CLIENTE_POTENCIAL']].copy()
        else:
            # Aplicar filtro por CIIU seleccionados
            if ciiu_seleccionados:
                df_filtrado = df[df['CIIU'].astype(str).isin(ciiu_seleccionados)].copy()
            else:
                df_filtrado = df.copy()
        
        if macrosector_sel != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['MACROSECTOR'] == macrosector_sel]
        
        if depto_sel != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['DEPARTAMENTO'] == depto_sel]
        
        df_filtrado = df_filtrado[
            (df_filtrado['INGRESOS_2024'] >= ingresos_min * 1000) & 
            (df_filtrado['INGRESOS_2024'] <= ingresos_max * 1000)
        ]
        
        # Mostrar estadísticas de filtros aplicados
        st.sidebar.markdown("---")
        st.sidebar.subheader("📊 Resumen de Filtros")
        st.sidebar.info(f"""
        **CIIU seleccionados:** {len(ciiu_seleccionados)}  
        **Empresas encontradas:** {len(df_filtrado)}  
        **% del total:** {len(df_filtrado)/len(df)*100:.1f}%
        """)
        
        # Mostrar resultados
        st.header("🎯 Clientes Potenciales Identificados")
        st.write(f"Se encontraron **{len(df_filtrado)}** empresas que cumplen con los criterios")
        
        if len(df_filtrado) > 0:
            # Tabs para diferentes vistas
            tab1, tab2, tab3 = st.tabs(["📊 Tabla de Empresas", "📈 Análisis", "📄 Generar Informe"])
            
            with tab1:
                # Mostrar tabla de empresas
                columnas_mostrar = ['RAZON_SOCIAL', 'CIIU', 'CIUDAD', 'DEPARTAMENTO', 
                                   'INGRESOS_2024', 'CRECIMIENTO_INGRESOS', 'MARGEN_GANANCIA_2024']
                
                df_mostrar = df_filtrado[columnas_mostrar].copy()
                df_mostrar['INGRESOS_2024'] = df_mostrar['INGRESOS_2024'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "N/D")
                df_mostrar['CRECIMIENTO_INGRESOS'] = df_mostrar['CRECIMIENTO_INGRESOS'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "N/D")
                df_mostrar['MARGEN_GANANCIA_2024'] = df_mostrar['MARGEN_GANANCIA_2024'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "N/D")
                
                st.dataframe(df_mostrar, height=400, use_container_width=True)
            
            with tab2:
                # Análisis por sector
                st.subheader("Distribución por Tipo de Industria")
                sector_counts = df_filtrado['CIIU_BASE'].value_counts()
                
                col1, col2 = st.columns(2)
                with col1:
                    st.bar_chart(sector_counts.head(10))
                
                with col2:
                    # Top 10 empresas por ingresos
                    st.subheader("Top 10 Empresas por Ingresos")
                    top_empresas = df_filtrado.nlargest(10, 'INGRESOS_2024')[['RAZON_SOCIAL', 'INGRESOS_2024']]
                    top_empresas['INGRESOS_2024'] = top_empresas['INGRESOS_2024'].apply(lambda x: f"${x/1000000:,.1f}M")
                    st.dataframe(top_empresas, hide_index=True)
                
                # Métricas promedio
                st.subheader("Métricas Promedio del Grupo")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    avg_ingresos = df_filtrado['INGRESOS_2024'].mean()
                    st.metric("Ingresos Promedio", f"${avg_ingresos/1000000:,.1f}M")
                with col2:
                    avg_crecimiento = df_filtrado['CRECIMIENTO_INGRESOS'].mean()
                    st.metric("Crecimiento Promedio", f"{avg_crecimiento:.1f}%")
                with col3:
                    avg_margen = df_filtrado['MARGEN_GANANCIA_2024'].mean()
                    st.metric("Margen Promedio", f"{avg_margen:.1f}%")
                with col4:
                    avg_endeudamiento = df_filtrado['RATIO_ENDEUDAMIENTO'].mean()
                    st.metric("Endeudamiento Promedio", f"{avg_endeudamiento:.1f}%")
            
            with tab3:
                st.subheader("📄 Generación de Informe PDF")
                st.write("Seleccione las empresas que desea incluir en el informe detallado:")
                
                # Permitir selección de empresas
                empresas_para_informe = st.multiselect(
                    "Empresas a incluir:",
                    options=df_filtrado['RAZON_SOCIAL'].tolist(),
                    default=df_filtrado.nlargest(5, 'INGRESOS_2024')['RAZON_SOCIAL'].tolist()
                )
                
                if empresas_para_informe:
                    # Checkbox para incluir análisis GPT
                    incluir_analisis = st.checkbox("Incluir análisis detallado con GPT (puede tomar varios minutos)", value=False)
                    
                    if st.button("🚀 Generar Informe PDF", type="primary"):
                        with st.spinner("Generando informe..."):
                            # Filtrar empresas seleccionadas
                            df_informe = df_filtrado[df_filtrado['RAZON_SOCIAL'].isin(empresas_para_informe)].copy()
                            
                            # Agregar análisis GPT si se solicita
                            if incluir_analisis:
                                progress_bar = st.progress(0)
                                for idx, (index, empresa) in enumerate(df_informe.iterrows()):
                                    progress_bar.progress((idx + 1) / len(df_informe))
                                    st.write(f"Analizando: {empresa['RAZON_SOCIAL']}...")
                                    analisis = analizar_empresa_con_gpt(empresa)
                                    df_informe.at[index, 'ANALISIS_GPT'] = analisis
                            
                            # Generar PDF
                            pdf_buffer = generar_pdf(df_informe)
                            
                            # Botón de descarga
                            st.download_button(
                                label="📥 Descargar Informe PDF",
                                data=pdf_buffer,
                                file_name=f"informe_clientes_potenciales_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                mime="application/pdf"
                            )
                            st.success("¡Informe generado exitosamente!")
                else:
                    st.warning("Por favor seleccione al menos una empresa para el informe.")
        else:
            st.warning("No se encontraron empresas que cumplan con los criterios de búsqueda.")
        
        # Sección de información adicional
        with st.expander("ℹ️ Información sobre Códigos CIIU"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Códigos CIIU objetivo para la industria de empaques:**")
                for codigo, descripcion in list(CIIU_OBJETIVO.items())[:len(CIIU_OBJETIVO)//2]:
                    st.write(f"• **{codigo}**: {descripcion}")
            
            with col2:
                st.write("** **")  # Espacio para alinear
                for codigo, descripcion in list(CIIU_OBJETIVO.items())[len(CIIU_OBJETIVO)//2:]:
                    st.write(f"• **{codigo}**: {descripcion}")
            
            st.markdown("---")
            st.write("**Cómo usar los filtros CIIU:**")
            st.write("""
            1. **Clientes Potenciales Predefinidos**: Usa los códigos CIIU ya identificados como relevantes para empaques
            2. **Búsqueda Personalizada**: Busca códigos CIIU específicos por texto (ej: 'C101' o 'G46')
            3. **Selección Manual**: Explora y selecciona de todos los códigos CIIU disponibles en la base de datos
            """)
        
        # Análisis adicional de CIIU
        with st.expander("📊 Análisis de Códigos CIIU en la Base de Datos"):
            # Estadísticas de CIIU
            ciiu_stats = df['CIIU'].value_counts().head(20)
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Top 20 Códigos CIIU más frecuentes")
                st.dataframe(
                    ciiu_stats.to_frame().reset_index().rename(
                        columns={'index': 'Código CIIU', 'CIIU': 'Cantidad de Empresas'}
                    ),
                    hide_index=True
                )
            
            with col2:
                st.subheader("Distribución por Grupo CIIU")
                df['CIIU_GRUPO'] = df['CIIU'].astype(str).str[:1]
                grupo_stats = df['CIIU_GRUPO'].value_counts()
                st.bar_chart(grupo_stats)
        
        # Footer
        st.markdown("---")
        st.markdown("*Sistema desarrollado para identificación de clientes potenciales en la industria de empaques*")

if __name__ == "__main__":
    main()
