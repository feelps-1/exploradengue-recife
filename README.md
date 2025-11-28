# 🦟 Monitoramento Dengue Recife - 2024

> Sistema de Suporte à Decisão para alocação de agentes de endemias baseado em dados históricos do SINAN.

## Sobre o Projeto

Este projeto foi desenvolvido como parte da disciplina de **[Nome da Matéria]** no curso de **[Seu Curso]**. 

O objetivo é propor uma solução computacional que utilize estatística descritiva e visualização de dados para auxiliar agentes de saúde no combate à Dengue na cidade do Recife. A ferramenta analisa as notificações de 2024, identificando focos ativos, perfil dos pacientes e sazonalidade da doença.

## Funcionalidades

* **Painel de KPIs:** Visualização rápida do total de casos confirmados, casos graves e bairros críticos.
* **Análise Temporal:** Curva epidêmica diária para identificar surtos e tendências.
* **Análise Espacial:** Filtros por Distrito Sanitário e ranking dos bairros com maior incidência.
* **Perfil Epidemiológico:** Distribuição de casos por sexo e análise de dispersão de idade (Boxplot).
* **Matriz de Risco:** Heatmap cruzando Localização x Mês do ano.
* **Sanity Check:** Limpeza automática de dados (remoção de casos descartados e tratamento de nomes de bairros).

## Tecnologias Utilizadas

* **Linguagem:** Python 3.x
* **Interface:** [Streamlit](https://streamlit.io/)
* **Manipulação de Dados:** Pandas
* **Visualização:** Plotly Express

## Estrutura do Projeto

```text
├── dados-historicos/      # Pasta contendo os CSVs (ex: dengue-recife-2024.csv)
├── app.py                 # Código principal do Dashboard
├── requirements.txt       # Lista de dependências do projeto
└── README.md              # Documentação
```

## Como Rodar o Projeto
Clone o repositório:

```Bash
git clone [https://github.com/seu-usuario/seu-repo.git](https://github.com/seu-usuario/seu-repo.git)
cd seu-repo
```
Crie um ambiente virtual (Opcional, mas recomendado):

```Bash
python -m venv venv
# No Windows:
venv\Scripts\activate
# No Linux/Mac:
source venv/bin/activate
```

Instale as dependências:
```Bash
pip install -r requirements.txt
```
Execute o Dashboard:

```Bash
streamlit run app.py
```

## Fonte de Dados

Os dados foram obtidos através do Portal de Dados Abertos da Prefeitura do Recife, referentes às notificações de Arboviroses (SINAN).
Dataset: Notificações de Dengue 2024.