# Mapa de Dependências

## _check_db.py

Depende de:
- `sqlite3`

## _create_evolucao.py

Depende de:
- `sqlite3`

## _inspect_db.py

Depende de:
- `sqlite3`

## _inspect_schema.py

Depende de:
- `sqlite3`

## _temp_deps.py

Depende de:
- `os,`

## _temp_estrutura.py

Depende de:
- `os`

## _temp_schema_export.py

Depende de:
- `sqlite3`

## app.py

Depende de:
- `auth`
- `streamlit`

## auth.py

Depende de:
- `bcrypt`
- `datetime`
- `functools`
- `sqlite3`
- `streamlit`

## database.py

Depende de:
- `sqlite3`

## debug\99_Debug_OS.py

Depende de:
- `auth`
- `pandas`
- `sqlite3`
- `streamlit`

## debug\diagnostico_classificacao.py

Depende de:
- `os`
- `pandas`
- `services.inteligencia_comercial`
- `sqlite3`
- `sys`

## debug\valida_v151.py

Depende de:
- `ast`
- `sys`

## legacy\12_Acoes_Massa.py

Depende de:
- `auth`
- `pandas`
- `sqlite3`
- `streamlit`

## legacy\30_Importar_Clientes.py

Depende de:
- `auth`
- `pandas`
- `sqlite3`
- `streamlit`

## legacy\31_Importar_Faturamento.py

Depende de:
- `auth`
- `datetime`
- `pandas`
- `re`
- `sqlite3`
- `streamlit`

## legacy\32_Importar_OS.py

Depende de:
- `auth`
- `datetime`
- `pandas`
- `sqlite3`
- `streamlit`

## legacy\36_Pendencias_Cadastro.py

Depende de:
- `auth`
- `datetime`
- `pandas`
- `services`
- `sqlite3`
- `streamlit`

## pages\00_Dashboard.py

Depende de:
- `auth`
- `numpy`
- `numpy.polynomial`
- `pandas`
- `plotly.express`
- `sqlite3`
- `streamlit`

## pages\01_Base_Clientes.py

Depende de:
- `auth`
- `pandas`
- `sqlite3`
- `streamlit`

## pages\02_Cliente_360.py

Depende de:
- `auth`
- `datetime`
- `pandas`
- `services`
- `services.ia.data_collector`
- `services.ia.engine`
- `services.ia.openai_client`
- `services.ia.prompt_builder`
- `services.relacionamento`
- `sqlite3`
- `streamlit`

## pages\06_Relacionamento_Comercial.py

Depende de:
- `auth`
- `datetime`
- `pandas`
- `services`
- `services.relacionamento`
- `sqlite3`
- `streamlit`

## pages\10_Central_Oportunidades.py

Depende de:
- `auth`
- `datetime`
- `pandas`
- `services`
- `services.inteligencia_comercial`
- `services.relacionamento`
- `sqlite3`
- `streamlit`

## pages\11_Pipeline_OS.py

Depende de:
- `auth`
- `datetime`
- `pandas`
- `sqlite3`
- `streamlit`

## pages\15_Parque_Mitsubishi.py

Depende de:
- `auth`
- `pandas`
- `services.mitsubishi`
- `streamlit`

## pages\16_Base_Produtos_Importados.py

Depende de:
- `auth`
- `datetime`
- `openpyxl`
- `pandas`
- `sqlite3`
- `streamlit`

## pages\30_Centro_Importacoes.py

Depende de:
- `auth`
- `datetime`
- `pandas`
- `re`
- `services`
- `sqlite3`
- `streamlit`

## pages\90_Administracao.py

Depende de:
- `auth`
- `datetime`
- `pathlib`
- `services.relacionamento`
- `shutil`
- `sqlite3`
- `streamlit`

## services\__init__.py

Depende de:
- `pandas`

## services\ia\__init__.py

*(sem imports próprios)*

## services\ia\data_collector.py

Depende de:
- `datetime`
- `pandas`
- `sqlite3`

## services\ia\engine.py

Depende de:
- `datetime`
- `services.ia.data_collector`
- `services.ia.openai_client`
- `services.ia.prompt_builder`
- `sqlite3`

## services\ia\openai_client.py

Depende de:
- `openai`
- `time`

## services\ia\prompt_builder.py

*(sem imports próprios)*

## services\inteligencia_comercial.py

Depende de:
- `datetime`
- `pandas`
- `sqlite3`
- `typing`

## services\mitsubishi.py

Depende de:
- `pandas`
- `rapidfuzz`
- `re`
- `sqlite3`

## services\relacionamento.py

Depende de:
- `datetime`
- `pandas`
- `sqlite3`
- `typing`

## tests\test_cliente360_ia.py

Depende de:
- `database`
- `datetime`
- `os`
- `services.ia.data_collector`
- `services.ia.engine`
- `services.ia.prompt_builder`
- `sqlite3`
- `sys`
- `unittest`

## tests\test_inteligencia_comercial.py

Depende de:
- `os`
- `pandas`
- `services.inteligencia_comercial`
- `sqlite3`
- `sys`
- `unittest`

## tests\test_produtos_importados.py

Depende de:
- `datetime`
- `sqlite3`

