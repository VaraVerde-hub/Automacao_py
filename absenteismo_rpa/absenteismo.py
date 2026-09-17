"""
absenteismo.py
--------------
Regras de negócio para classificar cada registro como:
- Falta (nenhuma marcação de ponto no dia)
- Atraso (entrada após o início da jornada + tolerância)
- Saída antecipada (saída antes do fim da jornada - tolerância)
- OK (dentro do esperado)

Um mesmo dia pode gerar mais de uma ocorrência (ex: atraso E saída
antecipada no mesmo dia).
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from enum import Enum

from config import RegrasAbsenteismo
from db import RegistroFuncionario


class TipoOcorrencia(str, Enum):
    FALTA = "Falta"
    ATRASO = "Atraso"
    SAIDA_ANTECIPADA = "Saída antecipada"


@dataclass
class Ocorrencia:
    funcionario_id: int
    nome: str
    gestor: str
    data: dt.date
    tipo: TipoOcorrencia
    minutos: int  # minutos de atraso/saída antecipada (0 para falta)
    detalhe: str


def _minutos_entre(hora_referencia: dt.time, hora_real: dt.time) -> int:
    """Diferença em minutos entre dois horários (hora_real - hora_referencia)."""
    ref = dt.datetime.combine(dt.date.min, hora_referencia)
    real = dt.datetime.combine(dt.date.min, hora_real)
    return int((real - ref).total_seconds() / 60)


def avaliar_registro(
    registro: RegistroFuncionario, regras: RegrasAbsenteismo
) -> list[Ocorrencia]:
    """Aplica as regras de absenteísmo a um único registro (funcionário + dia)."""
    ocorrencias: list[Ocorrencia] = []

    # Caso não haja NENHUMA marcação no dia -> Falta
    if registro.hora_entrada is None and registro.hora_saida is None:
        ocorrencias.append(
            Ocorrencia(
                funcionario_id=registro.funcionario_id,
                nome=registro.nome,
                gestor=registro.gestor,
                data=registro.data,
                tipo=TipoOcorrencia.FALTA,
                minutos=0,
                detalhe="Nenhuma marcação de ponto encontrada no dia.",
            )
        )
        return ocorrencias  # se faltou, não faz sentido checar atraso/saída

    # Atraso na entrada
    if registro.hora_entrada is not None:
        atraso_min = _minutos_entre(registro.hora_inicio_jornada, registro.hora_entrada)
        if atraso_min > regras.tolerancia_atraso_minutos:
            ocorrencias.append(
                Ocorrencia(
                    funcionario_id=registro.funcionario_id,
                    nome=registro.nome,
                    gestor=registro.gestor,
                    data=registro.data,
                    tipo=TipoOcorrencia.ATRASO,
                    minutos=atraso_min,
                    detalhe=(
                        f"Entrada às {registro.hora_entrada.strftime('%H:%M')} "
                        f"(jornada inicia às {registro.hora_inicio_jornada.strftime('%H:%M')})."
                    ),
                )
            )

    # Saída antecipada
    if registro.hora_saida is not None:
        adiantamento_min = _minutos_entre(registro.hora_saida, registro.hora_fim_jornada)
        if adiantamento_min > regras.tolerancia_saida_minutos:
            ocorrencias.append(
                Ocorrencia(
                    funcionario_id=registro.funcionario_id,
                    nome=registro.nome,
                    gestor=registro.gestor,
                    data=registro.data,
                    tipo=TipoOcorrencia.SAIDA_ANTECIPADA,
                    minutos=adiantamento_min,
                    detalhe=(
                        f"Saída às {registro.hora_saida.strftime('%H:%M')} "
                        f"(jornada termina às {registro.hora_fim_jornada.strftime('%H:%M')})."
                    ),
                )
            )

    return ocorrencias


def calcular_ocorrencias(
    registros: list[RegistroFuncionario], regras: RegrasAbsenteismo
) -> list[Ocorrencia]:
    """Aplica avaliar_registro a toda a lista de registros do período."""
    todas: list[Ocorrencia] = []
    for registro in registros:
        todas.extend(avaliar_registro(registro, regras))
    return todas


@dataclass
class ResumoGestor:
    gestor: str
    total_faltas: int = 0
    total_atrasos: int = 0
    total_saidas_antecipadas: int = 0
    ocorrencias: list[Ocorrencia] = field(default_factory=list)


def agrupar_por_gestor(ocorrencias: list[Ocorrencia]) -> dict[str, ResumoGestor]:
    """Agrupa ocorrências por gestor, útil para montar o e-mail por equipe."""
    resumos: dict[str, ResumoGestor] = {}
    for oc in ocorrencias:
        resumo = resumos.setdefault(oc.gestor, ResumoGestor(gestor=oc.gestor))
        resumo.ocorrencias.append(oc)
        if oc.tipo == TipoOcorrencia.FALTA:
            resumo.total_faltas += 1
        elif oc.tipo == TipoOcorrencia.ATRASO:
            resumo.total_atrasos += 1
        elif oc.tipo == TipoOcorrencia.SAIDA_ANTECIPADA:
            resumo.total_saidas_antecipadas += 1
    return resumos
