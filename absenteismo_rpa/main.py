"""
main.py
-------
Ponto de entrada do RPA. Fluxo:

1. Carrega configuração (.env)
2. Conecta no SQL Server e busca marcações de ponto + dados de funcionários
   no período configurado
3. Calcula ocorrências de absenteísmo (falta, atraso, saída antecipada)
4. Monta o relatório em HTML, agrupado por gestor
5. Envia o relatório por e-mail

Para rodar diariamente, agende este script (ver README.md — seção
"Agendamento").
"""

from __future__ import annotations

import datetime as dt
import logging
import sys

from absenteismo import agrupar_por_gestor, calcular_ocorrencias
from config import load_config
from db import SQLServerRepository
from email_report import enviar_email, montar_html

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("absenteismo_rpa.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("absenteismo_rpa")


def executar() -> None:
    logger.info("Iniciando processo de monitoramento de absenteísmo.")

    config = load_config()

    hoje = dt.date.today()
    data_fim = hoje - dt.timedelta(days=1)  # por padrão, analisa até "ontem"
    data_inicio = data_fim - dt.timedelta(days=config.regras.periodo_dias - 1)

    logger.info("Período de análise: %s a %s", data_inicio, data_fim)

    repositorio = SQLServerRepository(config.db)
    try:
        registros = repositorio.buscar_registros_periodo(data_inicio, data_fim)
    except Exception:
        logger.exception("Falha ao consultar o SQL Server.")
        raise

    logger.info("Registros retornados do banco: %d", len(registros))

    ocorrencias = calcular_ocorrencias(registros, config.regras)
    logger.info("Ocorrências de absenteísmo encontradas: %d", len(ocorrencias))

    resumos_por_gestor = agrupar_por_gestor(ocorrencias)

    html = montar_html(
        titulo=config.titulo_relatorio,
        data_inicio=data_inicio,
        data_fim=data_fim,
        resumos_por_gestor=resumos_por_gestor,
    )

    assunto = f"{config.titulo_relatorio} - {data_fim.strftime('%d/%m/%Y')}"

    try:
        enviar_email(config.smtp, assunto, html)
    except Exception:
        logger.exception("Falha ao enviar o e-mail do relatório.")
        raise

    logger.info("E-mail enviado com sucesso para: %s", ", ".join(config.smtp.destinatarios))
    logger.info("Processo finalizado com sucesso.")


if __name__ == "__main__":
    executar()
