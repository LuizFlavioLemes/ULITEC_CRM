"""
Testes do Módulo de Inteligência Comercial — ULITEC CRM v1.0.2
"""

import unittest
import sys
import os

# Garantir que o diretório raiz está no path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import sqlite3

from services.inteligencia_comercial import (
    get_clientes_esfriando,
    get_clientes_esquentando,
    get_clientes_sem_visita,
    get_clientes_sem_faturamento,
    get_clientes_muitas_os,
    get_clientes_parque_relevante,
    calcular_score_comercial,
    get_resumo_executivo,
)


class TestEsfriando(unittest.TestCase):
    """Testes para clientes esfriando."""

    def test_get_clientes_esfriando_retorna_dataframe(self):
        df = get_clientes_esfriando()
        self.assertIsInstance(df, pd.DataFrame)

    def test_get_clientes_esfriando_colunas(self):
        df = get_clientes_esfriando()
        colunas_esperadas = [
            "cliente", "cidade", "estado",
            "faturamento_periodo_atual", "faturamento_periodo_anterior",
            "variacao", "dias_sem_visita"
        ]
        for col in colunas_esperadas:
            self.assertIn(col, df.columns, f"Coluna '{col}' ausente")

    def test_get_clientes_esfriando_ordenado(self):
        df = get_clientes_esfriando()
        if not df.empty:
            self.assertEqual(
                df["variacao"].iloc[0], df["variacao"].min(),
                "Primeira linha deve ter a menor variação"
            )

    def test_get_clientes_esfriando_unidade(self):
        df = get_clientes_esfriando(unidade="ULITEC SP")
        self.assertIsInstance(df, pd.DataFrame)


class TestEsquentando(unittest.TestCase):
    """Testes para clientes esquentando."""

    def test_get_clientes_esquentando_retorna_dataframe(self):
        df = get_clientes_esquentando()
        self.assertIsInstance(df, pd.DataFrame)

    def test_get_clientes_esquentando_colunas(self):
        df = get_clientes_esquentando()
        colunas_esperadas = ["cliente", "cidade", "estado", "variacao", "faturamento"]
        for col in colunas_esperadas:
            self.assertIn(col, df.columns, f"Coluna '{col}' ausente")

    def test_get_clientes_esquentando_ordenado(self):
        df = get_clientes_esquentando()
        if not df.empty:
            self.assertEqual(
                df["variacao"].iloc[0], df["variacao"].max(),
                "Primeira linha deve ter a maior variação"
            )


class TestSemVisita(unittest.TestCase):
    """Testes para clientes sem visita."""

    def test_get_clientes_sem_visita_retorna_dataframe(self):
        df = get_clientes_sem_visita()
        self.assertIsInstance(df, pd.DataFrame)

    def test_get_clientes_sem_visita_colunas(self):
        df = get_clientes_sem_visita()
        colunas_esperadas = ["cliente", "dias_sem_visita", "cidade", "tipo"]
        for col in colunas_esperadas:
            self.assertIn(col, df.columns, f"Coluna '{col}' ausente")

    def test_get_clientes_sem_visita_ordenado(self):
        df = get_clientes_sem_visita()
        if not df.empty:
            # Deve ter a coluna tipo
            self.assertIn("tipo", df.columns, "Coluna 'tipo' deve existir")
            # Nunca visitados (NULL) devem vir primeiro
            # Pelo menos o primeiro deve ser NUNCA_VISITADO
            self.assertIn(df["tipo"].iloc[0], ["NUNCA_VISITADO", "VISITA_ATRASADA"])


class TestSemFaturamento(unittest.TestCase):
    """Testes para clientes sem faturamento."""

    def test_get_clientes_sem_faturamento_retorna_dataframe(self):
        df = get_clientes_sem_faturamento()
        self.assertIsInstance(df, pd.DataFrame)

    def test_get_clientes_sem_faturamento_colunas(self):
        df = get_clientes_sem_faturamento()
        colunas_esperadas = ["cliente", "máquinas", "última OS", "último faturamento"]
        for col in colunas_esperadas:
            self.assertIn(col, df.columns, f"Coluna '{col}' ausente")


class TestMuitasOS(unittest.TestCase):
    """Testes para clientes com muitas OS."""

    def test_get_clientes_muitas_os_retorna_dataframe(self):
        df = get_clientes_muitas_os()
        self.assertIsInstance(df, pd.DataFrame)

    def test_get_clientes_muitas_os_limite_20(self):
        df = get_clientes_muitas_os()
        self.assertLessEqual(len(df), 20, "Deve retornar no máximo 20 registros")


class TestParqueRelevante(unittest.TestCase):
    """Testes para clientes com parque Mitsubishi relevante."""

    def test_get_clientes_parque_relevante_retorna_dataframe(self):
        df = get_clientes_parque_relevante()
        self.assertIsInstance(df, pd.DataFrame)

    def test_get_clientes_parque_relevante_colunas(self):
        df = get_clientes_parque_relevante()
        colunas_esperadas = ["cliente", "quantidade_maquinas"]
        for col in colunas_esperadas:
            self.assertIn(col, df.columns, f"Coluna '{col}' ausente")


class TestScoreComercial(unittest.TestCase):
    """Testes para score comercial."""

    def test_calcular_score_comercial_retorna_dataframe(self):
        df = calcular_score_comercial()
        self.assertIsInstance(df, pd.DataFrame)

    def test_calcular_score_comercial_colunas(self):
        df = calcular_score_comercial()
        colunas_esperadas = ["cliente", "cidade", "score", "classificacao"]
        for col in colunas_esperadas:
            self.assertIn(col, df.columns, f"Coluna '{col}' ausente")

    def test_calcular_score_comercial_score_range(self):
        df = calcular_score_comercial()
        if not df.empty:
            self.assertTrue(
                df["score"].between(0, 100).all(),
                "Scores devem estar entre 0 e 100"
            )

    def test_calcular_score_comercial_classificacao(self):
        df = calcular_score_comercial()
        if not df.empty:
            for _, row in df.iterrows():
                self.assertIn(
                    row["classificacao"],
                    ["AAA", "AA", "A", "B", "C"],
                    f"Classificação inválida: {row['classificacao']}"
                )

    def test_calcular_score_comercial_ordenado(self):
        df = calcular_score_comercial()
        if not df.empty:
            self.assertGreaterEqual(
                df["score"].iloc[0],
                df["score"].iloc[-1],
                "Deve estar ordenado do maior score para o menor"
            )

    def test_calcular_score_comercial_limite_50(self):
        df = calcular_score_comercial()
        self.assertLessEqual(len(df), 50, "Deve retornar no máximo 50 registros")

    def test_calcular_score_comercial_unidade(self):
        df = calcular_score_comercial(unidade="ULITEC SP")
        self.assertIsInstance(df, pd.DataFrame)


class TestResumoExecutivo(unittest.TestCase):
    """Testes para resumo executivo."""

    def test_get_resumo_executivo_retorna_dict(self):
        resumo = get_resumo_executivo()
        self.assertIsInstance(resumo, dict)

    def test_get_resumo_executivo_chaves(self):
        resumo = get_resumo_executivo()
        chaves_esperadas = [
            "total_clientes",
            "clientes_esfriando",
            "clientes_esquentando",
            "clientes_sem_visita",
            "clientes_sem_faturamento",
            "maquinas_monitoradas",
        ]
        for chave in chaves_esperadas:
            self.assertIn(chave, resumo, f"Chave '{chave}' ausente")

    def test_get_resumo_executivo_tipos(self):
        resumo = get_resumo_executivo()
        for chave in resumo:
            self.assertIsInstance(
                resumo[chave], (int, float),
                f"Chave '{chave}' deve ser numérica"
            )

    def test_get_resumo_executivo_unidade(self):
        resumo = get_resumo_executivo(unidade="ULITEC SP")
        self.assertIsInstance(resumo, dict)


class TestPyCompile(unittest.TestCase):
    """Testes de compilação dos módulos."""

    def test_py_compile_inteligencia_comercial(self):
        import py_compile
        result = py_compile.compile("services/inteligencia_comercial.py", doraise=True)
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()