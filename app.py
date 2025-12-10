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
        # Lê o arquivo
        df = pd.read_csv(
            CAMINHO_ARQUIVO, 
            sep=';', 
            encoding='latin1',
            low_memory=False,
            dayfirst=True,
            dtype={'sem_not': str} # Força ler como texto para não perder formato
        )
        
        # Padroniza colunas
        df.columns = df.columns.str.lower().str.strip()
        
        # 1. Tratamento de Datas
        df['dt_notific'] = pd.to_datetime(df['dt_notific'], errors='coerce', dayfirst=True)
        
        # --- MUDANÇA: SEMANA EPIDEMIOLÓGICA VIA CAMPO 'sem_not' ---
        # Formato esperado: '202411' (Ano + Semana)
        if 'sem_not' in df.columns:
            # Remove '.0' se tiver vindo como float convertido para string
            df['sem_not'] = df['sem_not'].astype(str).str.replace(r'\.0$', '', regex=True)
            
            # Pega os últimos 2 caracteres para saber a semana (Ex: '202411' -> '11')
            df['semana_epidemiologica'] = pd.to_numeric(df['sem_not'].str[-2:], errors='coerce')
        else:
            # Fallback se não existir a coluna (calcula pela data)
            df['semana_epidemiologica'] = df['dt_notific'].dt.isocalendar().week

        # 2. Tratamento da Classificação
        df['classi_fin'] = pd.to_numeric(df['classi_fin'], errors='coerce')
        
        def definir_status(codigo):
            if codigo in [10, 11, 12]: return "Confirmado"
            elif codigo == 5: return "Descartado"
            elif pd.isna(codigo) or codigo == '': return "Em Investigação/Branco"
            else: return "Inconclusivo/Outro"
            
        df['status_caso'] = df['classi_fin'].apply(definir_status)

        # 3. Limpeza de Bairros
        if 'nm_bairro' in df.columns:
            df['nm_bairro'] = df['nm_bairro'].astype(str).str.strip().str.upper()
            df.loc[df['nm_bairro'].isin(['NAN', 'nan', '']), 'nm_bairro'] = "NÃO INFORMADO"
            
        # 4. Limpeza de Distritos
        if 'id_distrit' in df.columns:
            df['id_distrit'] = pd.to_numeric(df['id_distrit'], errors='coerce').fillna(0).astype(int)
            df['nome_distrito'] = df['id_distrit'].map(MAPA_DISTRITOS)
            df['nome_distrito'] = df['nome_distrito'].fillna("Distrito Não Identificado")
        else:
            df['nome_distrito'] = "Não Identificado"
            
        # Tratamento de idade
        if 'nu_idade_n' in df.columns:
             df['nu_idade_n'] = pd.to_numeric(df['nu_idade_n'], errors='coerce')

        return df

    except FileNotFoundError:
        st.error(f"Arquivo não encontrado: {CAMINHO_ARQUIVO}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro crítico ao ler o arquivo: {e}")
        return pd.DataFrame()

df = carregar_dados_2024()

if df.empty:
    st.stop()

# --- BARRA LATERAL (FILTROS) ---
st.sidebar.title("Filtros")

st.sidebar.markdown(f"**Total bruto:** `{len(df)}` linhas")

# 1. Filtro de Status
opcoes_status = sorted(df['status_caso'].unique())
status_selecionado = st.sidebar.multiselect(
    "Status da Notificação:",
    options=opcoes_status,
    default=opcoes_status 
)

# 2. Filtro de Distrito
if 'nome_distrito' in df.columns:
    distritos_disponiveis = sorted(df['nome_distrito'].unique().astype(str))
    distrito_selecionado = st.sidebar.multiselect(
        "Distrito Sanitário:",
        options=distritos_disponiveis,
        default=distritos_disponiveis
    )
else:
    distrito_selecionado = []

# --- APLICAÇÃO DOS FILTROS ---
df_filtrado = df[df['nome_distrito'].isin(distrito_selecionado)]
df_final = df_filtrado[df_filtrado['status_caso'].isin(status_selecionado)]

st.sidebar.markdown(f"**Total exibido:** `{len(df_final)}` linhas")
st.sidebar.markdown("---")

# Definição de cor dinâmica
if "Confirmado" in status_selecionado and len(status_selecionado) == 1:
    cor_tema = '#FF4B4B' 
    subtitulo = "Exibindo apenas Casos Confirmados"
elif "Descartado" in status_selecionado and len(status_selecionado) == 1:
    cor_tema = '#808080' 
    subtitulo = "Exibindo apenas Casos Descartados"
else:
    cor_tema = '#1F77B4' 
    subtitulo = "Exibindo Total de Notificações"

# --- LAYOUT DO DASHBOARD ---
st.title(f"🦟 Dashboard Dengue Recife - 2024")
st.caption(subtitulo)

# Botão Download
csv = df_final.to_csv(index=False).encode('utf-8')
st.download_button("📥 Baixar CSV Filtrado", data=csv, file_name='dengue_filtrado.csv', mime='text/csv')

st.markdown("---")

# KPIs
col1, col2, col3, col4 = st.columns(4)

total_exibido = len(df_final)
confirmados_reais = len(df_final[df_final['classi_fin'].isin([10, 11, 12])])
em_investigacao = len(df_final[pd.isna(df_final['classi_fin'])])

bairros_validos = df_final[~df_final['nm_bairro'].isin(["NÃO INFORMADO", "NAN"])]
if not bairros_validos.empty:
    bairro_pior = bairros_validos['nm_bairro'].mode()[0]
else:
    bairro_pior = "-"

col1.metric("Total (Filtro)", f"{total_exibido:,}")
col2.metric("Confirmados", f"{confirmados_reais:,}")
col3.metric("Em Investigação", f"{em_investigacao:,}")
col4.metric("Bairro Crítico", f"{bairro_pior}")

st.markdown("### 📈 Curva Epidêmica")

if not df_final.empty:
    tab1, tab2 = st.tabs(["Por Semana Epidemiológica (SEM_NOT)", "Evolução Diária (DT_NOTIFIC)"])
    
    with tab1:
        # Agrupa pela nova lógica SEM_NOT
        casos_semanais = df_final.groupby('semana_epidemiologica').size().reset_index(name='Casos')
        # Garante ordenação
        casos_semanais = casos_semanais.sort_values('semana_epidemiologica')
        
        fig_semana = px.bar(
            casos_semanais, 
            x='semana_epidemiologica', 
            y='Casos',
            title="Casos por Semana Epidemiológica (Extraído de SEM_NOT)",
            labels={'semana_epidemiologica': 'Semana (1-53)', 'Casos': 'Quantidade'},
            color_discrete_sequence=[cor_tema]
        )
        # Ajusta eixo X para mostrar todas as semanas se couber
        fig_semana.update_xaxes(type='category')
        st.plotly_chart(fig_semana, use_container_width=True)

    with tab2:
        # Agrupa por dia (dt_notific)
        casos_diarios = df_final.groupby('dt_notific').size().reset_index(name='Casos')
        casos_diarios = casos_diarios.sort_values('dt_notific')
        
        casos_diarios['Media_Movel'] = casos_diarios['Casos'].rolling(window=7).mean()

        fig_diario = go.Figure()
        fig_diario.add_trace(go.Bar(
            x=casos_diarios['dt_notific'], y=casos_diarios['Casos'],
            name='Notificações', marker_color=cor_tema, opacity=0.5
        ))
        fig_diario.add_trace(go.Scatter(
            x=casos_diarios['dt_notific'], y=casos_diarios['Media_Movel'],
            name='Média Móvel (7d)', line=dict(color='black', width=2)
        ))
        fig_diario.update_layout(title="Evolução Diária das Notificações", template='plotly_white')
        st.plotly_chart(fig_diario, use_container_width=True)
else:
    st.warning("Nenhum dado disponível para o filtro selecionado.")

st.markdown("### 🗺️ Localidade")

col_map1, col_map2 = st.columns(2)

with col_map1:
    st.subheader("Por Distrito Sanitário")
    if not df_final.empty:
        por_distrito = df_final['nome_distrito'].value_counts().reset_index()
        por_distrito.columns = ['Distrito', 'Total']
        fig_dist = px.bar(por_distrito, x='Total', y='Distrito', orientation='h', text_auto=True)
        st.plotly_chart(fig_dist, use_container_width=True)

with col_map2:
    st.subheader("Top 10 Bairros")
    if not bairros_validos.empty:
        por_bairro = bairros_validos['nm_bairro'].value_counts().head(10).reset_index()
        por_bairro.columns = ['Bairro', 'Total']
        fig_bairro = px.bar(por_bairro, x='Total', y='Bairro', orientation='h', text_auto=True, color_discrete_sequence=[cor_tema])
        fig_bairro.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bairro, use_container_width=True)
