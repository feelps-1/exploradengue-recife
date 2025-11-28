import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Monitoramento Dengue Recife 2024",
    page_icon="🦟",
    layout="wide"
)

st.title("🦟 Dashboard Dengue Recife - 2024")
st.markdown("""
Monitoramento dos casos de dengue notificados no ano de **2024**.
Utilize os filtros laterais para analisar regiões específicas.
""")

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
        
        df['dt_notific'] = pd.to_datetime(df['dt_notific'], errors='coerce')
        df['mes'] = df['dt_notific'].dt.month_name()
        
        df['classi_fin'] = pd.to_numeric(df['classi_fin'], errors='coerce')
        df = df[df['classi_fin'] != 5]
        
        if 'id_distrit' in df.columns:
            df['id_distrit'] = pd.to_numeric(df['id_distrit'], errors='coerce')
            df['nome_distrito'] = df['id_distrit'].map(MAPA_DISTRITOS)
            df['nome_distrito'] = df['nome_distrito'].fillna(df['id_distrit'].astype(str))
        
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

st.sidebar.header("Filtros")

if 'nome_distrito' in df.columns:
    distritos_disponiveis = sorted(df['nome_distrito'].dropna().unique().astype(str))
    distrito_selecionado = st.sidebar.multiselect(
        "Selecione o Distrito Sanitário:",
        options=distritos_disponiveis,
        default=distritos_disponiveis
    )
    
    df_filtrado = df[df['nome_distrito'].isin(distrito_selecionado)]
else:
    st.warning("Coluna de distrito não identificada corretamente.")
    df_filtrado = df

st.markdown("---")
col1, col2, col3 = st.columns(3)

total_casos = len(df_filtrado)
casos_graves = len(df_filtrado[df_filtrado['classi_fin'].isin([12, 13])])

if not df_filtrado.empty and 'nm_bairro' in df_filtrado.columns:
    bairro_pior = df_filtrado['nm_bairro'].mode()[0]
else:
    bairro_pior = "-"

col1.metric("Total Notificações (2024)", f"{total_casos:,}")
col2.metric("Casos Graves/Alarme", f"{casos_graves}")
col3.metric("Bairro Crítico", f"{bairro_pior}")

st.markdown("### Análise Temporal e Espacial")

row1_col1, row1_col2 = st.columns([2, 1])

with row1_col1:
    st.subheader("Evolução dos Casos em 2024")
    if not df_filtrado.empty:
        casos_por_data = df_filtrado.groupby('dt_notific').size().reset_index(name='Casos')
        
        fig_linha = px.line(
            casos_por_data, 
            x='dt_notific', 
            y='Casos', 
            title='Curva Epidêmica Diária',
            template='plotly_white'
        )
        st.plotly_chart(fig_linha, use_container_width=True)

with row1_col2:
    st.subheader("Top 10 Bairros")
    if not df_filtrado.empty and 'nm_bairro' in df_filtrado.columns:
        casos_por_bairro = df_filtrado['nm_bairro'].value_counts().head(10).reset_index()
        casos_por_bairro.columns = ['Bairro', 'Casos']
        
        fig_barras = px.bar(
            casos_por_bairro, 
            x='Casos', 
            y='Bairro', 
            orientation='h',
            title='Bairros com maior incidência'
        )
        fig_barras.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_barras, use_container_width=True)

with st.expander("Ver dados brutos (Amostra)"):
    col_visualizacao = ['dt_notific', 'nome_distrito', 'nm_bairro', 'classi_fin', 'mes']
    cols_existentes = [c for c in col_visualizacao if c in df_filtrado.columns]
    st.dataframe(df_filtrado[cols_existentes].head(100))

st.markdown("### Perfil dos Pacientes")

col_perfil1, col_perfil2 = st.columns(2)

with col_perfil1:
    st.subheader("Distribuição por Sexo")
    if 'cs_sexo' in df_filtrado.columns:
        df_sexo = df_filtrado['cs_sexo'].value_counts().reset_index()
        df_sexo.columns = ['Sexo', 'Quantidade']
        
        fig_sexo = px.pie(
            df_sexo, 
            values='Quantidade', 
            names='Sexo', 
            color='Sexo',
            color_discrete_map={'M': '#36A2EB', 'F': '#FF6384', 'I': '#C9CBCF'},
            hole=0.4
        )
        st.plotly_chart(fig_sexo, use_container_width=True)
    else:
        st.warning("Coluna 'cs_sexo' não encontrada.")

with col_perfil2:
    st.subheader("Distribuição por Idade")
    if 'nu_idade_n' in df_filtrado.columns:
        df_filtrado['nu_idade_n'] = pd.to_numeric(df_filtrado['nu_idade_n'], errors='coerce')
        
        df_idade = df_filtrado[df_filtrado['nu_idade_n'] < 120]
        
        if not df_idade.empty:
            fig_idade = px.box(
                df_idade, 
                y="nu_idade_n", 
                x="cs_sexo",
                color="cs_sexo",
                title="Dispersão de Idade por Sexo",
                labels={"nu_idade_n": "Idade (Anos)", "cs_sexo": "Sexo"}
            )
            st.plotly_chart(fig_idade, use_container_width=True)
            
            media_idade = df_idade['nu_idade_n'].mean()
            mediana_idade = df_idade['nu_idade_n'].median()
            st.info(f"💡 Estatística: A idade média é **{media_idade:.1f} anos** e a mediana é **{mediana_idade:.0f} anos**.")
    else:
        st.warning("Coluna 'nu_idade_n' não encontrada.")

st.markdown("### Matriz de Risco: Onde e Quando?")
st.markdown("Visualização da intensidade de casos cruzando o Local (Distrito) com o Tempo (Mês).")

if 'mes' in df_filtrado.columns and 'nome_distrito' in df_filtrado.columns:
    heatmap_data = df_filtrado.groupby(['nome_distrito', 'mes']).size().reset_index(name='Casos')
    
    ordem_meses = ['January', 'February', 'March', 'April', 'May', 'June', 
                   'July', 'August', 'September', 'October', 'November', 'December']
    
    fig_heatmap = px.density_heatmap(
        heatmap_data, 
        x="mes", 
        y="nome_distrito", 
        z="Casos", 
        color_continuous_scale="Reds",
        title="Intensidade de Casos",
        category_orders={"mes": ordem_meses}
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)