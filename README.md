# Recrutamento Inteligente com Agentes

Este repositório implementa um assistente de recrutamento que combina modelos de linguagem locais (LLMs) com uma interface web simples para gerar descrições de vaga e avaliar candidatos automaticamente.

**Objetivo**
- Automatizar a geração de descrições de vaga (role summary, responsabilidades, skills) a partir de poucos parâmetros.
- Avaliar e ranquear candidatos tecnicamente com base na aderência à vaga (skills, anos de experiência, título/área).
- Fornecer uma interface prática para recrutadores via Streamlit.

**Principais componentes (arquitetura)**
- `app.py` — Interface Streamlit: formulário para criar vaga, mostrar descrição e botão para avaliar candidatos.
- `agents/agentjobbuilder.py` — Agente gerador de descrição de vaga (usa Ollama se disponível, fallback local quando não).
- `agents/agentqualifier.py` — Agente avaliador de candidatos (usa Ollama se disponível, fallback local com heurística de matching).
- `data/bronze/` — Dados de candidatos (JSON/NDJSON). Pode haver também um Excel `applicants_melhores_campos.xlsx` como fonte.
- `requirements.txt` — Dependências do projeto.

Fluxo de execução
1. O usuário preenche `Company`, `Role Title`, `Seniority`, `Area` e `Team` no `app.py`.
2. Ao clicar em "Generate Job Description", o `agentjobbuilder` gera a descrição (por Ollama ou fallback local).
3. Ao clicar em "Find Best Candidates", o `agentqualifier` lê a base de candidatos (Excel/JSON/NDJSON) e retorna os melhores com `fit_score`, strengths e gaps.

Tecnologias e ferramentas
- Ollama (opcional): servidor local de LLMs (https://ollama.com). O projeto usa um modelo LLaMA local quando disponível.
- LLaMA 3 (1B): modelo usado via Ollama (se configurado).
- Streamlit: interface web.
- Pandas / openpyxl: leitura e manipulação de dados (Excel/JSON).

Como executar (Windows / PowerShell)
1. Criar e ativar virtualenv (recomendado):

```powershell
python -m venv .venv
. .venv\Scripts\Activate.ps1
```

2. Instalar dependências:

```powershell
pip install -r requirements.txt
# ou, se preferir instalar manualmente:
# pip install streamlit pandas openpyxl ollama
```

3. Rodar o app:

```powershell
.venv\Scripts\python -m streamlit run app.py
```

Uso com/sem Ollama
- Por padrão o projeto foi configurado para rodar com fallbacks locais quando Ollama não está disponível (variável `USE_OLLAMA=0`).
- Para usar Ollama (se você instalou e inicializou o servidor Ollama localmente):

```powershell
$env:USE_OLLAMA=1
.venv\Scripts\python -m streamlit run app.py
```

Boas práticas e recomendações
- Privacidade: os dados dos candidatos permanecem no ambiente local. Evite enviar CSVs/JSONs com dados sensíveis para serviços externos sem consentimento.
- Versionamento: use um `requirements.txt` travado para evitar incompatibilidades entre versões de bibliotecas (p.ex. `pip freeze > requirements.txt`).
- Testes: crie scripts unitários para validar a extração de skills e cálculo de `fit_score` (p.ex. `tests/test_qualifier.py`).
- Logging: durante desenvolvimento ative logs para capturar mensagens de erro dos agentes e do Ollama.
- Dados: normalize as colunas dos candidatos (nome, título, skills, anos de experiência, área) para melhores resultados.

Detalhes sobre os agentes

1) `agentjobbuilder` (gerador de vaga)
- Entrada: `company`, `title`, `seniority`, `area`, `team`.
- Saída: JSON estruturado com `role_summary`, `responsibilities`, `required_skills`, `nice_to_have`, `soft_skills`.
- Comportamento: se `USE_OLLAMA=1` e o servidor estiver disponível, chama o LLM via Ollama; caso contrário, gera um template local mais detalhado.
- Pontos de melhoria: personalizar prompts por cultura da empresa; permitir templates por área (Data, Backend, Frontend).

2) `agentqualifier` (avaliador de candidatos)
- Entrada: descrição da vaga (JSON) e base de candidatos (Excel/JSON/NDJSON).
- Saída: JSON com `selected_candidates` (cada candidato contém `name`, `title`, `technical_skills`, `strengths`, `gaps`, `years_experience`, `fit_score`).
- Heurística local atual (fallback):
  - Normaliza skills dos candidatos e da vaga.
  - Calcula `req_ratio` (percentual de required skills atendidas).
  - Calcula `nice_ratio` (percentual de nice-to-have).
  - Infere `desired_years` a partir da descrição (senioridade) e combina com anos reportados do candidato para gerar `exp_score`.
  - Combina sinais (skills, experiência, match de título/área) em uma pontuação ponderada `fit_score` (0-100).
- Pontos de melhoria: extrair skills via NLP, normalizar sinônimos (p.ex. "machine learning" vs "ML"), usar embeddings para matching semântico.

Extensibilidade — adicionando novos agentes
- A arquitetura é modular: cada agente é um módulo em `agents/` com funções claras.
- Exemplos de novos agentes:
  - Entrevistador simulado (gera perguntas e avalia respostas)
  - Gerador de feedback automático (para candidatos não selecionados)
  - Agente de triagem inicial (filtra currículos por critérios rígidos)

Estrutura do projeto (exemplo)
```
App/
├─ app.py
├─ requirements.txt
├─ README.md
├─ agents/
│  ├─ __init__.py
│  ├─ agentjobbuilder.py
│  ├─ agentqualifier.py
│  └─ agent_job_builder.py  # shim para compatibilidade
├─ data/
│  ├─ bronze/
│  │  ├─ applicants.json
│  │  └─ applicants.ndjson
├─ scripts/
│  └─ test_eval.py
```

Recomendações finais
- Se pretende operar com modelos locais, mantenha o Ollama atualizado e baixe o(s) modelos necessários com `ollama pull`.
- Se quiser rodar em produção, considere separar a UI (Streamlit) do processamento de agentes (API/worker), adicionar filas (Redis/RQ) e autenticação.

---

Se quiser, eu:
- incluo uma figura/diagrama de arquitetura (você disse que adicionará a imagem depois);
- gero exemplos de unit tests para `agentqualifier`;
- converto `data/bronze/applicants.json` em Excel (`.xlsx`) se preferir.

---

