"""
db.py
-----
Camada de acesso a dados. Responsável por abrir a conexão com o SQL Server
e executar as consultas necessárias para o cálculo de absenteísmo.

Pressupõe duas tabelas (nomes configuráveis via .env):

- funcionarios (tabela_funcionarios)
    id                  INT / PK
    nome                VARCHAR
    gestor              VARCHAR
    hora_inicio_jornada TIME   -- ex: 08:00:00
    hora_fim_jornada    TIME   -- ex: 17:00:00

- marcacao_ponto (tabela_ponto)
    id              INT / PK
    funcionario_id  INT / FK -> funcionarios.id
    data            DATE
    hora_entrada    TIME (nullable)
    hora_saida      TIME (nullable)

Se os nomes de colunas do seu banco forem diferentes, ajuste apenas
as queries abaixo (SELECT ... AS alias) para manter o restante do
projeto (absenteismo.py) funcionando sem alterações.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import pyodbc

from config import DBConfig


@dataclass
class RegistroFuncionario:
    IdFuncionario: int
    Nome: str
    Cargo: str
    Setor: str
    Data: dt.date
    Hora: dt.time



class SQLServerRepository:
    def __init__(self, db_config: DBConfig):
        self._config = db_config

    def _conectar(self) -> pyodbc.Connection:
        return pyodbc.connect(self._config.connection_string)

    def buscar_registros_periodo(
        self, data_inicio: dt.date, data_fim: dt.date
    ) -> list[RegistroFuncionario]:
        """
        Retorna, para cada funcionário e cada dia do período, o registro de
        ponto correspondente (podendo vir com hora_entrada/hora_saida nulas
        caso o funcionário não tenha batido o ponto naquele dia).

        Usamos LEFT JOIN de funcionarios -> marcacao_ponto para não perder
        dias em que não houve NENHUMA marcação (o que também é absenteísmo:
        falta).
        """
        query = f"""
            SELECT
                f.[IdFuncionario]    AS IdFuncionario,
                f.[Nome]    AS Nome,
                f.[Cargo]   AS Cargo,
                f.[Setor]   AS Setor,
                p.[Data]    AS Data,
                p.[Hora]    AS Hora
            FROM {self._config.tabela_funcionarios} f
            LEFT JOIN {self._config.tabela_ponto} p
                ON f.[IdFuncionario] = p.[WorkDay]
            AND p.[Data] BETWEEN ? AND ?
        """

        registros: list[RegistroFuncionario] = []
        with self._conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(query, data_inicio, data_fim)
            for row in cursor.fetchall():
                registros.append(
                    RegistroFuncionario(
                        IdFuncionario=row.IdFuncionario,
                        Nome=row.Nome,
                        Cargo=row.Cargo,
                        Setor=row.Setor,
                        Data=row.Data,
                        Hora=row.Hora
                    )
                )
        return registros
