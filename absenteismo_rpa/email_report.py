"""
email_report.py
----------------
Monta o relatório de absenteísmo em HTML (agrupado por gestor) e envia
por e-mail via SMTP.
"""

from __future__ import annotations

import datetime as dt
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from absenteismo import Ocorrencia, ResumoGestor, TipoOcorrencia
from config import SMTPConfig

_COR_TIPO = {
    TipoOcorrencia.FALTA: "#c0392b",
    TipoOcorrencia.ATRASO: "#e67e22",
    TipoOcorrencia.SAIDA_ANTECIPADA: "#d35400",
}


def _linha_ocorrencia(oc: Ocorrencia) -> str:
    cor = _COR_TIPO.get(oc.tipo, "#333")
    minutos = f"{oc.minutos} min" if oc.minutos else "-"
    return f"""
        <tr>
            <td style="padding:6px 10px;border-bottom:1px solid #eee;">{oc.data.strftime('%d/%m/%Y')}</td>
            <td style="padding:6px 10px;border-bottom:1px solid #eee;">{oc.nome}</td>
            <td style="padding:6px 10px;border-bottom:1px solid #eee;color:{cor};font-weight:600;">{oc.tipo.value}</td>
            <td style="padding:6px 10px;border-bottom:1px solid #eee;">{minutos}</td>
            <td style="padding:6px 10px;border-bottom:1px solid #eee;">{oc.detalhe}</td>
        </tr>
    """


def _bloco_gestor(resumo: ResumoGestor) -> str:
    linhas = "\n".join(_linha_ocorrencia(oc) for oc in sorted(
        resumo.ocorrencias, key=lambda o: (o.data, o.nome)))
    return f"""
    <h3 style="margin-top:28px;color:#2c3e50;">Gestor: {resumo.gestor}</h3>
    <p style="margin:4px 0 10px 0;color:#555;">
        Faltas: <b>{resumo.total_faltas}</b> &nbsp;|&nbsp;
        Atrasos: <b>{resumo.total_atrasos}</b> &nbsp;|&nbsp;
        Saídas antecipadas: <b>{resumo.total_saidas_antecipadas}</b>
    </p>
    <table style="border-collapse:collapse;width:100%;font-family:Arial,sans-serif;font-size:13px;">
        <thead>
            <tr style="background:#f4f6f7;text-align:left;">
                <th style="padding:6px 10px;">Data</th>
                <th style="padding:6px 10px;">Funcionário</th>
                <th style="padding:6px 10px;">Ocorrência</th>
                <th style="padding:6px 10px;">Minutos</th>
                <th style="padding:6px 10px;">Detalhe</th>
            </tr>
        </thead>
        <tbody>
            {linhas}
        </tbody>
    </table>
    """


def montar_html(
    titulo: str,
    data_inicio: dt.date,
    data_fim: dt.date,
    resumos_por_gestor: dict[str, ResumoGestor],
) -> str:
    periodo = (
        data_inicio.strftime("%d/%m/%Y")
        if data_inicio == data_fim
        else f"{data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}"
    )

    if not resumos_por_gestor:
        corpo = "<p style='color:#27ae60;font-weight:600;'>Nenhuma ocorrência de absenteísmo no período. 🎉</p>"
    else:
        corpo = "\n".join(
            _bloco_gestor(resumo)
            for resumo in sorted(resumos_por_gestor.values(), key=lambda r: r.gestor)
        )

    return f"""
    <html>
    <body style="font-family:Arial,sans-serif;color:#2c3e50;">
        <h2 style="color:#1a5276;">{titulo}</h2>
        <p>Período analisado: <b>{periodo}</b></p>
        {corpo}
        <p style="margin-top:30px;font-size:12px;color:#999;">
            Relatório gerado automaticamente pelo processo de RPA de absenteísmo.
        </p>
    </body>
    </html>
    """


def enviar_email(smtp_config: SMTPConfig, assunto: str, html: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = assunto
    msg["From"] = smtp_config.remetente
    msg["To"] = ", ".join(smtp_config.destinatarios)
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP(smtp_config.host, smtp_config.port) as server:
        if smtp_config.use_tls:
            server.starttls()
        server.login(smtp_config.username, smtp_config.password)
        server.sendmail(smtp_config.remetente, smtp_config.destinatarios, msg.as_string())
