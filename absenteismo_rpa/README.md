# RPA de Monitoramento de Absenteísmo

Automação em Python que:

1. Lê os dados de **marcação de ponto** e **cadastro de funcionários** em um
   banco **SQL Server**;
2. Calcula ocorrências de **falta**, **atraso** e **saída antecipada**,
   comparando os horários batidos com a jornada de trabalho de cada
   funcionário;
3. Envia um **relatório em HTML por e-mail**, agrupado por gestor.

## Estrutura do projeto

```
absenteismo_rpa/
├── config.py        # Configurações (lidas do .env)
├── db.py             # Conexão e queries no SQL Server
├── absenteismo.py     # Regras de negócio (falta/atraso/saída antecipada)
├── email_report.py    # Montagem do HTML e envio do e-mail
├── main.py            # Orquestração (ponto de entrada)
├── requirements.txt
├── .env.example        # Modelo de variáveis de ambiente
└── README.md
```

## Pré-requisitos

- Python 3.10+
- Driver ODBC do SQL Server instalado na máquina que vai rodar o script
  (ex.: "ODBC Driver 17 for SQL Server" ou 18). No Windows normalmente já
  vem com o SQL Server Management Studio; no Linux, siga o guia da
  Microsoft para instalar o `msodbcsql`.
- Uma conta de e-mail/SMTP para envio (Office 365, Gmail com senha de app,
  servidor SMTP interno da empresa, etc.).

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Configuração

1. Copie `.env.example` para `.env`:
   ```bash
   cp .env.example .env
   ```
2. Preencha os dados de conexão do SQL Server e do SMTP.
3. Ajuste `DB_TABELA_PONTO` e `DB_TABELA_FUNCIONARIOS` se os nomes das
   tabelas no seu banco forem diferentes.

### Estrutura de tabelas esperada

O projeto assume (mas você pode adaptar as queries em `db.py` se os nomes
de colunas forem diferentes):

**funcionarios**

| coluna              | tipo    | descrição                          |
|---------------------|---------|-------------------------------------|
| id                  | INT     | chave primária                      |
| nome                | VARCHAR | nome do funcionário                 |
| gestor              | VARCHAR | nome do gestor responsável          |
| hora_inicio_jornada | TIME    | horário de início da jornada        |
| hora_fim_jornada    | TIME    | horário de fim da jornada           |

**marcacao_ponto**

| coluna         | tipo    | descrição                                   |
|----------------|---------|-----------------------------------------------|
| id             | INT     | chave primária                                |
| funcionario_id | INT     | FK para funcionarios.id                       |
| data           | DATE    | data da marcação                              |
| hora_entrada   | TIME    | horário de entrada (pode ser nulo se faltou)  |
| hora_saida     | TIME    | horário de saída (pode ser nulo)              |

> Se seu sistema de ponto registra múltiplas batidas por dia (ex.: entrada,
> saída para almoço, retorno, saída final), será necessário um passo
> intermediário para consolidar essas batidas em "primeira entrada do dia"
> e "última saída do dia" antes de usar `db.py` — posso ajudar a adaptar
> a query se você me passar a estrutura real dessa tabela.

## Executando manualmente

```bash
python main.py
```

O script:
- calcula o período (por padrão, **o dia anterior** — configurável via
  `PERIODO_DIAS`);
- busca os registros no banco;
- calcula as ocorrências;
- envia o e-mail;
- grava logs em `absenteismo_rpa.log` (e também exibe no console).

## Agendamento (execução diária automática)

### Windows — Agendador de Tarefas
1. Abra o "Agendador de Tarefas" → "Criar Tarefa Básica".
2. Gatilho: diariamente, no horário desejado (ex.: 07:00, após o
   fechamento do dia anterior).
3. Ação: "Iniciar um programa"
   - Programa/script: caminho do `python.exe` do seu ambiente virtual
     (ex.: `C:\caminho\absenteismo_rpa\.venv\Scripts\python.exe`)
   - Argumentos: `main.py`
   - Iniciar em: `C:\caminho\absenteismo_rpa`

### Linux/Mac — cron
```bash
crontab -e
```
Adicione (exemplo: todo dia às 07:00):
```
0 7 * * * cd /caminho/absenteismo_rpa && /caminho/absenteismo_rpa/.venv/bin/python main.py >> cron.log 2>&1
```

## Personalizações comuns

- **Tolerância de atraso/saída**: ajuste `TOLERANCIA_ATRASO_MIN` e
  `TOLERANCIA_SAIDA_MIN` no `.env`.
- **Período do relatório**: `PERIODO_DIAS` (ex.: `7` para um relatório
  semanal, rodando às segundas-feiras).
- **E-mail por gestor** (em vez de um único e-mail consolidado): dá para
  adaptar `main.py` para enviar um e-mail por gestor, usando
  `agrupar_por_gestor` e chamando `enviar_email` dentro de um loop — posso
  implementar essa variação se preferir.
- **Anexar Excel**: se quiser o relatório também em `.xlsx` anexado ao
  e-mail (além do corpo HTML), posso adicionar isso usando `openpyxl`.

## Segurança

- Nunca versione o arquivo `.env` (adicione-o ao `.gitignore`).
- Use uma conta de banco **somente leitura** para esse processo, se
  possível.
- Para Gmail/Office 365, use senha de aplicativo em vez da senha normal
  da conta.
