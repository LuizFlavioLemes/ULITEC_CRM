"""
Testes do módulo IA - ULITEC CRM v1.0.0

Valida:
- criação das tabelas
- leitura dos clientes
- leitura faturamento
- leitura OS
- leitura oportunidades
- leitura Mitsubishi
- montagem do contexto
- geração do prompt
- gravação dos logs
"""

import sqlite3
import os
import sys
import unittest
from datetime import datetime, timedelta

# Adiciona diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.db_init import garantir_schema as criar_banco
from services.ia.data_collector import (
    coletar_cliente,
    coletar_faturamento,
    coletar_os,
    coletar_oportunidades,
    coletar_mitsubishi,
    coletar_interacoes,
)
from services.ia.prompt_builder import PROMPT_SISTEMA, montar_contexto_cliente, montar_prompt_completo
from services.ia.engine import _salvar_log


DB_PATH = "crm.db"


class TestTabelasIA(unittest.TestCase):
    """Testa criação das tabelas do módulo IA."""

    @classmethod
    def setUpClass(cls):
        criar_banco(DB_PATH)

    def test_tabela_config_ia_existe(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='config_ia'"
        )
        self.assertIsNotNone(cursor.fetchone())
        conn.close()

    def test_tabela_relatorios_ia_existe(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='relatorios_ia'"
        )
        self.assertIsNotNone(cursor.fetchone())
        conn.close()

    def test_colunas_config_ia(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(config_ia)")
        colunas = {row[1] for row in cursor.fetchall()}
        self.assertIn("id", colunas)
        self.assertIn("api_key", colunas)
        self.assertIn("modelo", colunas)
        self.assertIn("ativo", colunas)
        self.assertIn("criado_em", colunas)
        self.assertIn("atualizado_em", colunas)
        conn.close()

    def test_colunas_relatorios_ia(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(relatorios_ia)")
        colunas = {row[1] for row in cursor.fetchall()}
        self.assertIn("id", colunas)
        self.assertIn("cliente_id", colunas)
        self.assertIn("modelo", colunas)
        self.assertIn("prompt_tokens", colunas)
        self.assertIn("completion_tokens", colunas)
        self.assertIn("tempo_execucao", colunas)
        self.assertIn("custo_estimado", colunas)
        self.assertIn("criado_em", colunas)
        conn.close()


class TestColetaDados(unittest.TestCase):
    """Testa as funções de coleta de dados."""

    @classmethod
    def setUpClass(cls):
        criar_banco(DB_PATH)
        # Garante que existe pelo menos um cliente para testar
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "INSERT OR IGNORE INTO clientes (id, razao_social, cidade, estado, segmento, status) "
            "VALUES (99999, 'CLIENTE TESTE IA', 'CIDADE TESTE', 'SP', 'TESTE', 'ATIVO')"
        )
        conn.commit()
        conn.close()

    def test_coletar_cliente(self):
        dados = coletar_cliente(99999)
        self.assertIsInstance(dados, dict)
        if dados:
            self.assertIn("razao_social", dados)

    def test_coletar_cliente_inexistente(self):
        dados = coletar_cliente(-1)
        self.assertIsInstance(dados, dict)
        # Deve retornar dict vazio
        self.assertEqual(len(dados), 0)

    def test_coletar_faturamento(self):
        dados = coletar_faturamento(99999)
        self.assertIsInstance(dados, dict)
        self.assertIn("faturamento_12m", dados)
        self.assertIn("meses_faturados", dados)
        self.assertIn("media_mensal", dados)

    def test_coletar_os(self):
        dados = coletar_os(99999)
        self.assertIsInstance(dados, dict)
        self.assertIn("quantidade_total", dados)
        self.assertIn("por_status", dados)

    def test_coletar_oportunidades(self):
        dados = coletar_oportunidades(99999)
        self.assertIsInstance(dados, dict)
        self.assertIn("abertas", dados)
        self.assertIn("ganhas", dados)
        self.assertIn("perdidas", dados)
        self.assertIn("valor_potencial", dados)

    def test_coletar_mitsubishi(self):
        dados = coletar_mitsubishi(99999)
        self.assertIsInstance(dados, dict)
        self.assertIn("quantidade", dados)
        self.assertIn("principais_series_cnc", dados)

    def test_coletar_interacoes(self):
        dados = coletar_interacoes(99999)
        self.assertIsInstance(dados, list)


class TestPromptBuilder(unittest.TestCase):
    """Testa montagem do prompt."""

    def test_prompt_sistema_nao_vazio(self):
        self.assertTrue(len(PROMPT_SISTEMA) > 100)

    def test_prompt_sistema_tem_secoes(self):
        self.assertIn("Resumo Executivo", PROMPT_SISTEMA)
        self.assertIn("Situação Comercial", PROMPT_SISTEMA)
        self.assertIn("Riscos Identificados", PROMPT_SISTEMA)
        self.assertIn("Oportunidades Identificadas", PROMPT_SISTEMA)
        self.assertIn("Próximas Ações Recomendadas", PROMPT_SISTEMA)

    def test_montar_contexto_cliente_vazio(self):
        contexto = montar_contexto_cliente({}, {}, {}, {}, {}, [])
        self.assertIsInstance(contexto, str)
        self.assertIn("DADOS DO CLIENTE", contexto)

    def test_montar_contexto_cliente_com_dados(self):
        cliente = {
            "razao_social": "EMPRESA XYZ",
            "cidade": "Jundiaí",
            "estado": "SP",
            "segmento": "Metal Mecânico",
            "observacoes": "Cliente estratégico",
            "status": "ATIVO",
        }
        faturamento = {
            "faturamento_12m": 500000.0,
            "ultimo_faturamento": "2026-05-01",
            "meses_faturados": 10,
            "media_mensal": 50000.0,
        }
        os_data = {
            "quantidade_total": 15,
            "ultima_os": "OS-001",
            "valor_total": 200000.0,
            "por_status": {"APROVADA": 5, "FATURADA": 10},
        }
        oportunidades = {
            "abertas": 3,
            "ganhas": 5,
            "perdidas": 2,
            "valor_potencial": 150000.0,
        }
        mitsubishi = {
            "quantidade": 8,
            "principais_series_cnc": ["M700 (5)", "M80 (3)"],
        }
        interacoes = [
            {
                "data_interacao": "2026-06-01",
                "tipo_interacao": "Visita Técnica",
                "responsavel": "João",
                "resumo": "Cliente solicitou orçamento",
                "proxima_acao": "Enviar proposta",
            }
        ]

        contexto = montar_contexto_cliente(
            cliente, faturamento, os_data, oportunidades, mitsubishi, interacoes
        )
        self.assertIn("EMPRESA XYZ", contexto)
        self.assertIn("R$ 500,000.00", contexto)
        self.assertIn("M700 (5)", contexto)
        self.assertIn("Visita Técnica", contexto)


class TestLogs(unittest.TestCase):
    """Testa gravação de logs na tabela relatorios_ia."""

    @classmethod
    def setUpClass(cls):
        criar_banco(DB_PATH)

    def test_salvar_log(self):
        _salvar_log(
            cliente_id=99999,
            modelo="gpt-4o-mini",
            prompt_tokens=100,
            completion_tokens=200,
            tempo_execucao=5.5,
            custo=0.00015,
        )

        conn = sqlite3.connect(DB_PATH)
        row = conn.execute(
            "SELECT * FROM relatorios_ia WHERE cliente_id = 99999 ORDER BY id DESC LIMIT 1"
        ).fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row[1], 99999)  # cliente_id
        self.assertEqual(row[2], "gpt-4o-mini")  # modelo
        self.assertEqual(row[3], 100)  # prompt_tokens
        self.assertEqual(row[4], 200)  # completion_tokens
        self.assertEqual(row[5], 5.5)  # tempo_execucao


class TestPromptCompleto(unittest.TestCase):
    """Testa a função montar_prompt_completo do prompt_builder."""

    def test_montar_prompt_completo_todas_secoes(self):
        """Verifica se o prompt completo contém todas as seções obrigatórias."""
        prompt = montar_prompt_completo({}, {}, {}, {}, {}, [])
        self.assertIn("# CONTEXTO", prompt)
        self.assertIn("## DADOS DO CLIENTE", prompt)
        self.assertIn("## FATURAMENTO 12M", prompt)
        self.assertIn("## ORDENS DE SERVIÇO", prompt)
        self.assertIn("## OPORTUNIDADES", prompt)
        self.assertIn("## PARQUE MITSUBISHI", prompt)
        self.assertIn("## INTERAÇÕES", prompt)
        self.assertIn("IMPORTANTE:", prompt)
        self.assertIn("Utilize apenas os dados fornecidos", prompt)

    def test_montar_prompt_completo_sem_dados(self):
        """Verifica se cliente sem dados não quebra."""
        prompt = montar_prompt_completo({}, {}, {}, {}, {}, [])
        self.assertIsInstance(prompt, str)
        self.assertIn("Sem dados cadastrais disponíveis", prompt)
        self.assertIn("Sem faturamento", prompt)
        self.assertIn("Nenhuma ordem de serviço", prompt)
        self.assertIn("Nenhuma oportunidade", prompt)
        self.assertIn("Nenhuma máquina", prompt)
        self.assertIn("Nenhuma interação", prompt)

    def test_montar_prompt_completo_com_dados(self):
        """Verifica se o prompt completo é montado corretamente com dados."""
        cliente = {
            "razao_social": "EMPRESA TESTE",
            "cidade": "Jundiaí",
            "estado": "SP",
            "segmento": "Metal Mecânico",
            "observacoes": "Cliente estratégico",
            "status": "ATIVO",
        }
        faturamento = {
            "faturamento_12m": 500000.0,
            "ultimo_faturamento": "2026-05-01",
            "meses_faturados": 10,
            "media_mensal": 50000.0,
        }
        os_data = {
            "quantidade_total": 15,
            "ultima_os": "OS-001",
            "valor_total": 200000.0,
            "por_status": {"APROVADA": 5, "FATURADA": 10},
        }
        oportunidades = {
            "abertas": 3,
            "ganhas": 5,
            "perdidas": 2,
            "valor_potencial": 150000.0,
        }
        mitsubishi = {
            "quantidade": 8,
            "principais_series_cnc": ["M700 (5)", "M80 (3)"],
        }
        interacoes = [
            {
                "data_interacao": "2026-06-01",
                "tipo_interacao": "Visita Técnica",
                "responsavel": "João",
                "resumo": "Cliente solicitou orçamento",
                "proxima_acao": "Enviar proposta",
            }
        ]

        prompt = montar_prompt_completo(
            cliente, faturamento, os_data, oportunidades, mitsubishi, interacoes
        )
        self.assertIn("EMPRESA TESTE", prompt)
        self.assertIn("R$ 500,000.00", prompt)
        self.assertIn("M700 (5)", prompt)
        self.assertIn("Visita Técnica", prompt)
        self.assertIn("Resumo executivo", prompt)
        self.assertIn("Serviços preventivos sugeridos", prompt)
        self.assertIn("Potencial de venda de peças", prompt)

    def test_montar_prompt_completo_faturamento_vazio(self):
        """Verifica se cliente sem faturamento não quebra."""
        prompt = montar_prompt_completo(
            {"razao_social": "TESTE", "cidade": "SP", "estado": "SP",
             "segmento": "TESTE", "status": "ATIVO"},
            {"faturamento_12m": 0, "ultimo_faturamento": None,
             "meses_faturados": 0, "media_mensal": 0},
            {}, {}, {}, []
        )
        self.assertIn("Sem faturamento", prompt)

    def test_montar_prompt_completo_os_vazia(self):
        """Verifica se cliente sem OS não quebra."""
        prompt = montar_prompt_completo(
            {"razao_social": "TESTE", "cidade": "SP", "estado": "SP",
             "segmento": "TESTE", "status": "ATIVO"},
            {}, {"quantidade_total": 0, "ultima_os": None,
                 "valor_total": 0, "por_status": {}},
            {}, {}, []
        )
        self.assertIn("Nenhuma ordem de serviço", prompt)

    def test_montar_prompt_completo_oportunidades_vazias(self):
        """Verifica se cliente sem oportunidades não quebra."""
        prompt = montar_prompt_completo(
            {"razao_social": "TESTE", "cidade": "SP", "estado": "SP",
             "segmento": "TESTE", "status": "ATIVO"},
            {}, {}, {"abertas": 0, "ganhas": 0, "perdidas": 0, "valor_potencial": 0},
            {}, []
        )
        self.assertIn("Nenhuma oportunidade", prompt)

    def test_montar_prompt_completo_interacoes_vazias(self):
        """Verifica se cliente sem interações não quebra."""
        prompt = montar_prompt_completo(
            {"razao_social": "TESTE", "cidade": "SP", "estado": "SP",
             "segmento": "TESTE", "status": "ATIVO"},
            {}, {}, {}, {}, []
        )
        self.assertIn("Nenhuma interação", prompt)


class TestOpenAIClient(unittest.TestCase):
    """Testa o cliente OpenAI (sem chamada real)."""

    def test_precos_definidos(self):
        from services.ia.openai_client import PRECOS

        self.assertIn("gpt-4o", PRECOS)
        self.assertIn("gpt-4o-mini", PRECOS)
        self.assertIn("input", PRECOS["gpt-4o"])
        self.assertIn("output", PRECOS["gpt-4o"])
        self.assertGreater(PRECOS["gpt-4o"]["input"], 0)
        self.assertGreater(PRECOS["gpt-4o-mini"]["input"], 0)

    def test_gerar_relatorio_modelo_invalido(self):
        from services.ia.openai_client import gerar_relatorio

        resultado = gerar_relatorio(
            api_key="fake", modelo="modelo-invalido", prompt_sistema="", prompt_usuario=""
        )
        self.assertFalse(resultado["sucesso"])
        self.assertIn("não suportado", resultado["erro"])


if __name__ == "__main__":
    unittest.main()