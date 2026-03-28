# Recrutamento Inteligente com Agentes

Este repositório implementa um assistente de recrutamento que combina modelos de linguagem locais (LLMs) com uma interface web simples para gerar descrições de vaga e avaliar candidatos automaticamente.

**Objetivo**
- Automatizar a geração de descrições de vaga (role summary, responsabilidades, skills) a partir de poucos parâmetros.
- Avaliar e ranquear candidatos tecnicamente com base na aderência à vaga (skills, anos de experiência, título/área).
- Fornecer uma interface prática para recrutadores via Streamlit.

**Demosntração do MVP**

Em poucos segundos e algumas palavras gerar uma descrição completa de vaga automatizando atividade manual e operacional e promovendo agilidade no dia a dia.

1. Tela Inicial
<img width="1394" height="371" alt="image" src="https://github.com/user-attachments/assets/a5c480e1-a84e-4a29-9dd0-47d0c3144a54" />

2. Geração de Vaga
<img width="1414" height="598" alt="image" src="https://github.com/user-attachments/assets/c5fceae6-25e1-4db2-9ce2-9c029718ac2c" />

Vale destacar que o projeto teve o intuito de ser um produto para uma empresa focada em recrutamento de talentos para outras empresas, portanto, cada tempo reduzido na operação garante consequentemente um melhor resultado para a empresa, além de padronização, eficiência e performance nas seleções dos talentos.

4. Busca Automática de Talentos
<img width="1811" height="532" alt="444" src="https://github.com/user-attachments/assets/38051d57-811e-4532-b077-20c68c037039" />

Promovendo uma seleção adequada utilizando o banco de talentos da empresa para geração de score do match entre vaga gerada e candidatos cadastrados, dessa forma, é possível entender qual será o esforço para fechar a posição, se já existe candidatos aderentes ou se será preciso a realização de hunting. 

**Principais componentes (arquitetura)**
- `app.py` — Interface Streamlit: formulário para criar vaga, mostrar descrição e botão para avaliar candidatos.
- `agents/agentjobbuilder.py` — Agente gerador de descrição de vaga (usa Ollama se disponível, fallback local quando não).
- `agents/agentqualifier.py` — Agente avaliador de candidatos (usa Ollama se disponível, fallback local com heurística de matching).
- `data/bronze/` — Dados de candidatos (JSON/NDJSON). Pode haver também um Excel `applicants_best_fields.xlsx` como fonte.
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

<img width="1112" height="638" alt="image" src="https://github.com/user-attachments/assets/4f832c73-33f0-4449-8980-398caa93f4cf" />

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
├─ data/
│  ├─ bronze/
│  │  ├─ applicants.json
│  │  └─ applicants.ndjson

```

Recomendações finais na utilização
- Se pretende operar com modelos locais, mantenha o Ollama atualizado e baixe o(s) modelos necessários com `ollama pull`.
- Se quiser rodar em produção, considere separar a UI (Streamlit) do processamento de agentes (API/worker), adicionar filas (Redis/RQ) e autenticação.

---
**Evoluções**

<img width="1168" height="649" alt="image" src="https://github.com/user-attachments/assets/9efb59f9-f9c1-4498-912e-6ad632e4e39b" />

Extensibilidade — adicionando novos agentes para garantir uma esteira completa em atração e seleção.

- A arquitetura é modular: cada agente é um módulo em `agents/` com funções claras.
- Exemplos de novos agentes:
  - Entrevistador simulado (gera perguntas e avalia respostas)
  - Gerador de feedback automático (para candidatos não selecionados)
  - Agente de triagem inicial (filtra currículos por critérios rígidos)

 ---
