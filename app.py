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
        df = pd.read_csv(
            CAMINHO_ARQUIVO, 
            sep=';', 
            encoding='latin1',
            low_memory=False
        )
        
        df.columns = df.columns.str.lower().str.strip()
        
        # Tratamento de Datas
        df['dt_notific'] = pd.to_datetime(df['dt_notific'], errors='coerce')
        df['mes'] = df['dt_notific'].dt.month_name()
        
        # --- MELHORIA 1: Semana Epidemiológica ---
        # Cria a coluna da semana do ano (1 a 52/53)
        df['semana_epidemiologica'] = df['dt_notific'].dt.isocalendar().week
        
        # Tratamento da Classificação Final
        df['classi_fin'] = pd.to_numeric(df['classi_fin'], errors='coerce')
        df = df[df['classi_fin'] != 5] # Remove descartados
        
        # Tratamento de Distritos
        if 'id_distrit' in df.columns:
            df['id_distrit'] = pd.to_numeric(df['id_distrit'], errors='coerce')
            df['nome_distrito'] = df['id_distrit'].map(MAPA_DISTRITOS)
            df['nome_distrito'] = df['nome_distrito'].fillna(df['id_distrit'].astype(str))
        
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
    distritos_disponiveis = sorted(df['nome_distrito'].dropna().unique().astype(str))
    distrito_selecionado = st.sidebar.multiselect(
        "Filtrar por Distrito Sanitário:",
        options=distritos_disponiveis,
        default=distritos_disponiveis
    )
    df_filtrado_geo = df[df['nome_distrito'].isin(distrito_selecionado)]
else:
    df_filtrado_geo = df

# Aplicação do Filtro de Confirmação
if tipo_visualizacao == "Apenas Casos Confirmados":
    codigos_confirmados = [10, 11, 12] 
    df_final = df_filtrado_geo[df_filtrado_geo['classi_fin'].isin(codigos_confirmados)]
    subtitulo = "Exibindo apenas casos confirmados (Dengue Clássica, Com Sinais de Alarme e Grave)."
    cor_tema = '#FF4B4B' # Vermelho para confirmados
else:
    df_final = df_filtrado_geo
    subtitulo = "Exibindo todas as notificações (Suspeitos + Confirmados)."
    cor_tema = '#1F77B4' # Azul para notificações gerais

# --- LAYOUT PRINCIPAL ---
st.title(f"🦟 Dashboard Dengue Recife - 2024")
st.markdown(f"**Modo:** {tipo_visualizacao}")
st.caption(subtitulo)

# --- MELHORIA 4: Botão de Download ---
csv = df_final.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Baixar Dados Filtrados (CSV)",
    data=csv,
    file_name='dengue_recife_filtrado.csv',
    mime='text/csv',
)

st.markdown("---")

# --- KPIs (Com Melhoria 3) ---
col1, col2, col3, col4 = st.columns(4)

total_casos = len(df_final)
casos_graves = len(df_final[df_final['classi_fin'] == 12]) 

# --- MELHORIA 3: KPI de % de Gravidade ---
percentual_graves = (casos_graves / total_casos * 100) if total_casos > 0 else 0

if not df_final.empty and 'nm_bairro' in df_final.columns:
    bairro_pior = df_final['nm_bairro'].mode()[0]
else:
    bairro_pior = "-"

col1.metric("Total de Registros", f"{total_casos:,}")
col2.metric("Casos Graves (Absoluto)", f"{casos_graves}")
col3.metric("Taxa de Gravidade", f"{percentual_graves:.2f}%")
col4.metric("Bairro Crítico", f"{bairro_pior}")

st.markdown("### 📈 Análise Temporal Avançada")

# Preparação dos dados temporais
if not df_final.empty:
    # Agrupamento Diário
    casos_diarios = df_final.groupby('dt_notific').size().reset_index(name='Casos')
    casos_diarios = casos_diarios.sort_values('dt_notific')
    
    # --- MELHORIA 2: Cálculo da Média Móvel (7 dias) ---
    casos_diarios['Media_Movel_7d'] = casos_diarios['Casos'].rolling(window=7).mean()

    # Agrupamento Semanal (Melhoria 1)
    casos_semanais = df_final.groupby('semana_epidemiologica').size().reset_index(name='Casos')

    tab1, tab2 = st.tabs(["Evolução Diária (+ Tendência)", "Por Semana Epidemiológica"])

    with tab1:
        # Gráfico Misto (Barras + Linha de Tendência) usando Graph Objects
        fig_diario = go.Figure()
        
        # Barras (Casos Reais)
        fig_diario.add_trace(go.Bar(
            x=casos_diarios['dt_notific'],
            y=casos_diarios['Casos'],
            name='Casos Diários',
            marker_color=cor_tema,
            opacity=0.4
        ))
        
        # Linha (Média Móvel)
        fig_diario.add_trace(go.Scatter(
            x=casos_diarios['dt_notific'],
            y=casos_diarios['Media_Movel_7d'],
            name='Média Móvel (7 dias)',
            line=dict(color='black', width=2),
            mode='lines'
        ))
        
        fig_diario.update_layout(
            title="Curva Epidêmica com Tendência Suavizada",
            xaxis_title="Data de Notificação",
            yaxis_title="Quantidade de Casos",
            legend=dict(x=0, y=1.0),
            template='plotly_white'
        )
        st.plotly_chart(fig_diario, use_container_width=True)
        st.info("ℹ️ A linha preta representa a **Média Móvel de 7 dias**, ideal para visualizar a tendência real sem as oscilações de fins de semana.")

    with tab2:
        # Gráfico por Semana Epidemiológica
        fig_semanal = px.bar(
            casos_semanais,
            x='semana_epidemiologica',
            y='Casos',
            title='Casos por Semana Epidemiológica (SE)',
            labels={'semana_epidemiologica': 'Semana Epidemiológica (SE)', 'Casos': 'Total de Casos'},
            color_discrete_sequence=[cor_tema]
        )
        st.plotly_chart(fig_semanal, use_container_width=True)

st.markdown("### 🗺️ Análise Espacial e Demográfica")

row2_col1, row2_col2 = st.columns([1, 1])

with row2_col1:
    st.subheader("Top 10 Bairros")
    if not df_final.empty and 'nm_bairro' in df_final.columns:
        casos_por_bairro = df_final['nm_bairro'].value_counts().head(10).reset_index()
        casos_por_bairro.columns = ['Bairro', 'Casos']
        
        fig_barras = px.bar(
            casos_por_bairro, 
            x='Casos', 
            y='Bairro', 
            orientation='h',
            text_auto=True,
            color_discrete_sequence=[cor_tema]
        )
        fig_barras.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_barras, use_container_width=True)

with row2_col2:
    st.subheader("Pirâmide Etária (Simulada)")
    if 'nu_idade_n' in df_final.columns and 'cs_sexo' in df_final.columns:
        df_idade = df_final[(df_final['nu_idade_n'] < 100) & (df_final['cs_sexo'].isin(['M', 'F']))]
        
        # Criação de faixas etárias (Bins)
        bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 100]
        labels = ['0-9', '10-19', '20-29', '30-39', '40-49', '50-59', '60-69', '70-79', '80+']
        df_idade['faixa_etaria'] = pd.cut(df_idade['nu_idade_n'], bins=bins, labels=labels, right=False)
        
        # Agrupamento
        df_pyramid = df_idade.groupby(['faixa_etaria', 'cs_sexo'], observed=False).size().reset_index(name='Casos')
        
        # Ajuste para pirâmide (Homens negativo para ficar na esquerda)
        df_pyramid['Casos_Plot'] = df_pyramid.apply(lambda x: -x['Casos'] if x['cs_sexo'] == 'M' else x['Casos'], axis=1)
        
        fig_pyramid = px.bar(
            df_pyramid,
            x='Casos_Plot',
            y='faixa_etaria',
            color='cs_sexo',
            orientation='h',
            title='Distribuição por Faixa Etária e Sexo',
            labels={'Casos_Plot': 'Quantidade de Casos', 'faixa_etaria': 'Faixa Etária'},
            color_discrete_map={'M': '#36A2EB', 'F': '#FF6384'}
        )
        # Formata o eixo X para mostrar números positivos dos dois lados
        fig_pyramid.update_layout(
            barmode='overlay', 
            xaxis=dict(tickvals=[-1000, -500, 0, 500, 1000], ticktext=['1000', '500', '0', '500', '1000'])
        )
        st.plotly_chart(fig_pyramid, use_container_width=True)
