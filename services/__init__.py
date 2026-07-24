import pandas as pd

def formatar_clientes_para_select(df):
    """
    Recebe um DataFrame de clientes contendo colunas:
      - razao_social
      - cidade
      - estado
      - (opcional) codigo_erp
      - (opcional) id

    Retorna:
      - lista_formatada: list[str] com rótulos "RAZAO SOCIAL - Cidade/UF"
      - dict_formatado: dict mapeando rótulo -> id do cliente
      - dict_reverso: dict mapeando rótulo -> dict com dados do cliente

    Se o DataFrame estiver vazio (banco novo), retorna listas e dicts vazios sem erro.
    """
    # ── Tratar DataFrame vazio (banco novo sem clientes) ──
    if df is None or df.empty:
        return [], {}, {}

    df = df.copy()

    if "codigo_erp" in df.columns and df["codigo_erp"].notna().any():
        df["_codigo"] = df["codigo_erp"].fillna("").astype(str).str.strip()
        df["_tem_codigo"] = df["_codigo"] != ""
    else:
        df["_codigo"] = ""
        df["_tem_codigo"] = False

    def montar_rotulo(row):
        if pd.notna(row.get("cidade")) and pd.notna(row.get("estado")):
            cidade_estado = f"{row['cidade']}/{row['estado']}"
        elif pd.notna(row.get("cidade")):
            cidade_estado = row["cidade"]
        elif pd.notna(row.get("estado")):
            cidade_estado = row["estado"]
        else:
            cidade_estado = ""

        rotulo = f"{row['razao_social']} - {cidade_estado}" if cidade_estado else row["razao_social"]

        if row["_tem_codigo"]:
            rotulo += f" ({row['_codigo']})"

        return rotulo

    df["_rotulo"] = df.apply(montar_rotulo, axis=1)

    lista_formatada = df["_rotulo"].tolist()

    dict_formatado = {}
    dict_reverso = {}
    for _, row in df.iterrows():
        rotulo = row["_rotulo"]
        if "id" in df.columns:
            dict_formatado[rotulo] = row["id"]
        dict_reverso[rotulo] = row.to_dict()

    return lista_formatada, dict_formatado, dict_reverso
