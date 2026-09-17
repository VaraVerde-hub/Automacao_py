"""
config.py
---------
Centraliza todas as configurações do projeto, lidas a partir de variáveis
de ambiente (arquivo .env). Isso evita hardcode de credenciais no código
e facilita o deploy em diferentes ambientes (dev/homologação/produção).
"""

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env (se existir) para o ambiente do processo
load_dotenv()


def _get_env(name: str, default: str | None = None, required: bool = False) -> str:
    value = os.getenv(name, default)
    if required and not value:
        raise RuntimeError(
            f"Variável de ambiente obrigatória não definida: {name}. "
            f"Verifique seu arquivo .env (veja .env.example)."
        )
    return value


@dataclass
class DBConfig:
    driver: str = field(default_factory=lambda: _get_env(
        "DB_DRIVER", "{ODBC Driver 17 for SQL Server}"))
    server: str = field(default_factory=lambda: _get_env("DB_SERVER", required=True))
    database: str = field(default_factory=lambda: _get_env("DB_DATABASE", required=True))
    username: str = field(default_factory=lambda: _get_env("DB_USERNAME", required=True))
    password: str = field(default_factory=lambda: _get_env("DB_PASSWORD", required=True))
    # Nomes de tabela configuráveis, caso o schema real use nomes diferentes
    tabela_ponto: str = field(default_factory=lambda: _get_env("DB_TABELA_PONTO", "marcacao_ponto"))
    tabela_funcionarios: str = field(default_factory=lambda: _get_env("DB_TABELA_FUNCIONARIOS", "funcionarios"))

    @property
    def connection_string(self) -> str:
        return (
            f"DRIVER={self.driver};"
            f"SERVER={self.server};"
            f"DATABASE={self.database};"
            f"UID={self.username};"
            f"PWD={self.password};"
            f"TrustServerCertificate=yes;"
        )


@dataclass
class SMTPConfig:
    host: str = field(default_factory=lambda: _get_env("SMTP_HOST", required=True))
    port: int = field(default_factory=lambda: int(_get_env("SMTP_PORT", "587")))
    username: str = field(default_factory=lambda: _get_env("SMTP_USERNAME", required=True))
    password: str = field(default_factory=lambda: _get_env("SMTP_PASSWORD", required=True))
    use_tls: bool = field(default_factory=lambda: _get_env("SMTP_USE_TLS", "true").lower() == "true")
    remetente: str = field(default_factory=lambda: _get_env("SMTP_REMETENTE", required=True))
    # Lista de destinatários separada por vírgula no .env
    destinatarios: list[str] = field(default_factory=lambda: [
        e.strip() for e in _get_env("SMTP_DESTINATARIOS", required=True).split(",") if e.strip()
    ])


@dataclass
class RegrasAbsenteismo:
    # Tolerância em minutos antes de considerar atraso / saída antecipada
    tolerancia_atraso_minutos: int = field(default_factory=lambda: int(_get_env("TOLERANCIA_ATRASO_MIN", "10")))
    tolerancia_saida_minutos: int = field(default_factory=lambda: int(_get_env("TOLERANCIA_SAIDA_MIN", "10")))
    # Quantos dias corridos para trás o relatório deve cobrir (1 = ontem)
    periodo_dias: int = field(default_factory=lambda: int(_get_env("PERIODO_DIAS", "1")))


@dataclass
class AppConfig:
    db: DBConfig = field(default_factory=DBConfig)
    smtp: SMTPConfig = field(default_factory=SMTPConfig)
    regras: RegrasAbsenteismo = field(default_factory=RegrasAbsenteismo)
    titulo_relatorio: str = field(default_factory=lambda: _get_env(
        "TITULO_RELATORIO", "Relatório Diário de Absenteísmo"))


def load_config() -> AppConfig:
    """Ponto único de entrada para carregar a configuração da aplicação."""
    return AppConfig()
