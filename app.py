import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Monitoramento Dengue Recife 2024",
    page_icon="🦟",
    layout="wide"
)

# --- CONFIGURAÇÃO E DADOS ---
CAMINHO_ARQUIVO = "./dados-historicos/dengue-recife-2024.csv"

# Mapa oficial de distritos sanitários do Recife
MAPA_DISTRITOS = {
    117: "DS I - Centro Expandido",
    118: "DS II - Encruzilhada-Beberibe",
    119: "DS III - Casa Amarela-Dois Irmãos",
    120: "DS IV - Caxangá-Várzea",
    121: "DS V - Afogados-Tejipió",
    122: "DS VI - Ibura-Boa Viagem",
    123: "DS VII - Noroeste", 
    124: "DS VIII - Jordão"
}

@st.cache_data
def carregar_dados_2024():
    try:
        df = pd.read_csv(
            CAMINHO_ARQUIVO, 
            sep=';', 
            encoding='latin1',
            low_memory=False
        )
        
        df.columns = df.columns.str.lower().str.strip()
        
        # 1. Tratamento de Datas
        df['dt_notific'] = pd.to_datetime(df['dt_notific'], errors='coerce')
        df['mes'] = df['dt_notific'].dt.month_name()
        df['semana_epidemiologica'] = df['dt_notific'].dt.isocalendar().week
        
        # 2. Tratamento da Classificação Final (Filtra descartados)
        df['classi_fin'] = pd.to_numeric(df['classi_fin'], errors='coerce')
        df = df[df['classi_fin'] != 5] 
        
        # 3. CORREÇÃO CRÍTICA DE BAIRROS (Resolve o problema Ibura vs Várzea)
        if 'nm_bairro' in df.columns:
            # Converte para string, remove espaços no início/fim e coloca em maiúsculo
            df['nm_bairro'] = df['nm_bairro'].astype(str).str.strip().str.upper()
            # Remove valores nulos convertidos para string "NAN"
            df.loc[df['nm_bairro'] == 'NAN', 'nm_bairro'] = "NÃO INFORMADO"

        # 4. CORREÇÃO CRÍTICA DE DISTRITOS
        if 'id_distrit' in df.columns:
            # Converte para numérico, erros viram NaN, depois preenche NaN com 0
            df['id_distrit'] = pd.to_numeric(df['id_distrit'], errors='coerce').fillna(0).astype(int)
            
            # Mapeia usando o dicionário
            df['nome_distrito'] = df['id_distrit'].map(MAPA_DISTRITOS)
            
            # Se não achou no mapa (ex: código 0 ou código errado), define como Indefinido
            df['nome_distrito'] = df['nome_distrito'].fillna("Distrito Indefinido/Outro")
        else:
            df['nome_distrito'] = "Não Identificado"
        
        if 'nu_idade_n' in df.columns:
             df['nu_idade_n'] = pd.to_numeric(df['nu_idade_n'], errors='coerce')

        return df

    except FileNotFoundError:
        st.error(f"Arquivo não encontrado: {CAMINHO_ARQUIVO}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}")
        return pd.DataFrame()

df = carregar_dados_2024()

if df.empty:
    st.stop()

# --- BARRA LATERAL (FILTROS) ---
st.sidebar.header("Configurações")

# Filtro de Visualização
tipo_visualizacao = st.sidebar.radio(
    "Tipo de Análise:",
    ("Todas Notificações", "Apenas Casos Confirmados")
)

# Filtro de Distrito
if 'nome_distrito' in df.columns:
    # Obtém lista única e ordenada de distritos
    distritos_disponiveis = sorted(df['nome_distrito'].unique().astype(str))
    
    distrito_selecionado = st.sidebar.multiselect(
        "Filtrar por Distrito Sanitário:",
        options=distritos_disponiveis,
        default=distritos_disponiveis
    )
    
    # Aplica o filtro
    if not distrito_selecionado:
        st.warning("Selecione pelo menos um distrito.")
        st.stop()
        
    df_filtrado_geo = df[df['nome_distrito'].isin(distrito_selecionado)]
else:
    df_filtrado_geo = df

# Aplicação do Filtro de Confirmação (Classificação SINAN)
if tipo_visualizacao == "Apenas Casos Confirmados":
    codigos_confirmados = [10, 11, 12] 
    df_final = df_filtrado_geo[df_filtrado_geo['classi_fin'].isin(codigos_confirmados)]
    subtitulo = "Exibindo apenas casos confirmados."
    cor_tema = '#FF4B4B' 
else:
    df_final = df_filtrado_geo
    subtitulo = "Exibindo todas as notificações (Suspeitos + Confirmados)."
    cor_tema = '#1F77B4' 

# --- LAYOUT PRINCIPAL ---
st.title(f"🦟 Dashboard Dengue Recife - 2024")
st.markdown(f"**Modo:** {tipo_visualizacao}")
st.caption(subtitulo)

# Botão de Download
csv = df_final.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Baixar Dados Filtrados (CSV)",
    data=csv,
    file_name='dengue_recife_filtrado.csv',
    mime='text/csv',
)

st.markdown("---")

# --- KPIs ---
col1, col2, col3, col4 = st.columns(4)

total_casos = len(df_final)
casos_graves = len(df_final[df_final['classi_fin'] == 12]) 
percentual_graves = (casos_graves / total_casos * 100) if total_casos > 0 else 0

# Lógica para pegar o Bairro Crítico ignorando "Não Informado" se possível
if not df_final.empty and 'nm_bairro' in df_final.columns:
    bairros_validos = df_final[df_final['nm_bairro'] != "NÃO INFORMADO"]
    if not bairros_validos.empty:
        bairro_pior = bairros_validos['nm_bairro'].mode()[0]
    else:
        bairro_pior = "-"
else:
    bairro_pior = "-"

col1.metric("Total de Registros", f"{total_casos:,}")
col2.metric("Casos Graves (Absoluto)", f"{casos_graves}")
col3.metric("Taxa de Gravidade", f"{percentual_graves:.2f}%")
col4.metric("Bairro Crítico", f"{bairro_pior}")

st.markdown("### 📈 Análise Temporal Avançada")

if not df_final.empty:
    casos_diarios = df_final.groupby('dt_notific').size().reset_index(name='Casos')
    casos_diarios = casos_diarios.sort_values('dt_notific')
    casos_diarios['Media_Movel_7d'] = casos_diarios['Casos'].rolling(window=7).mean()

    casos_semanais = df_final.groupby('semana_epidemiologica').size().reset_index(name='Casos')

    tab1, tab2 = st.tabs(["Evolução Diária", "Semana Epidemiológica"])

    with tab1:
        fig_diario = go.Figure()
        fig_diario.add_trace(go.Bar(
            x=casos_diarios['dt_notific'], y=casos_diarios['Casos'],
            name='Casos Diários', marker_color=cor_tema, opacity=0.4
        ))
        fig_diario.add_trace(go.Scatter(
            x=casos_diarios['dt_notific'], y=casos_diarios['Media_Movel_7d'],
            name='Média Móvel (7 dias)', line=dict(color='black', width=2)
        ))
        fig_diario.update_layout(
            title="Curva Epidêmica", xaxis_title="Data", yaxis_title="Casos",
            template='plotly_white', legend=dict(x=0, y=1.0)
        )
        st.plotly_chart(fig_diario, use_container_width=True)

    with tab2:
        fig_semanal = px.bar(
            casos_semanais, x='semana_epidemiologica', y='Casos',
            title='Casos por Semana Epidemiológica',
            color_discrete_sequence=[cor_tema]
        )
        st.plotly_chart(fig_semanal, use_container_width=True)

st.markdown("### 🗺️ Análise de Localidade")

if not df_final.empty and 'nm_bairro' in df_final.columns:
    # Filtra bairros nulos ou vazios para não poluir o gráfico
    dados_bairros = df_final[~df_final['nm_bairro'].isin(['NÃO INFORMADO', 'nan', 'NAN'])]
    
    casos_por_bairro = dados_bairros['nm_bairro'].value_counts().head(15).reset_index()
    casos_por_bairro.columns = ['Bairro', 'Casos']
    
    fig_barras = px.bar(
        casos_por_bairro, 
        x='Casos', 
        y='Bairro', 
        orientation='h',
        text_auto=True,
        title='Top 15 Bairros com maior incidência',
        color_discrete_sequence=[cor_tema],
        height=500
    )
    fig_barras.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_barras, use_container_width=True)
else:
    st.warning("Dados de bairro não disponíveis para visualização.")
