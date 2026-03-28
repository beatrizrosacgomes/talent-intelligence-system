import os
import pandas as pd
from ollama import Client
import json

USE_OLLAMA = os.environ.get('USE_OLLAMA', '0') == '1'
client = None
if USE_OLLAMA:
    try:
        client = Client(host='http://localhost:11434')
    except Exception:
        client = None


SYSTEM_PROMPT = """
You are a senior People Analytics specialist focused on recruitment and talent evaluation.

Your objective is to analyze candidates based strictly on the job description and provide objective, data-driven hiring recommendations.

Guidelines:
- Prioritize technical skills and role requirements.
- Avoid bias and unsupported assumptions.
- Be concise, clear, and structured.
- Focus only on the provided data.
- If a candidate lacks critical technical requirements, deprioritize them.

Output must be valid JSON.
"""


def build_candidate_context(candidatos):
    context = "Candidates:\n"

    campos_relevantes = [
        'infos_basicas_nome',
        'informacoes_profissionais_titulo_profissional',
        'informacoes_profissionais_conhecimentos_tecnicos',
        'informacoes_profissionais_area_atuacao',
    ]

    for i, c in enumerate(candidatos, 1):
        context += f"\nCandidate {i}:\n"
        for campo in campos_relevantes:
            valor = c.get(campo, 'Not informed')
            context += f"{campo}: {valor}\n"

    return context


def build_user_prompt(job_description, candidatos):
    candidate_context = build_candidate_context(candidatos)

    return f"""
Job Description:
{job_description}

{candidate_context}

Task:
Select the TOP 3 candidates based on technical fit.

Instructions:
- Strongly prioritize required technical skills (tools, languages, certifications).
- Ignore candidates without essential requirements.
- Be objective and evidence-based.

Output format (JSON):
{{
  "selected_candidates": [
    {{
      "name": "",
      "title": "",
      "technical_skills": [],
      "strengths": [],
      "gaps": [],
      "fit_score": 0-100
    }}
  ]
}}
"""


def avaliar_candidatos(descricao_vaga, caminho_excel='applicants_melhores_campos.xlsx'):
    # If Ollama disabled or client unavailable, perform local evaluation
    candidatos = None

    # 1) Try Excel path if provided
    if os.path.exists(caminho_excel):
        try:
            df = pd.read_excel(caminho_excel)
            candidatos = df.to_dict(orient='records')
        except Exception:
            candidatos = None

    # 2) Try common JSON fallback locations
    if not candidatos:
        base_dir = os.path.dirname(os.path.dirname(__file__))
        possible = [
            os.path.normpath(os.path.join(base_dir, 'data', 'bronze', 'applicants.json')),
            os.path.normpath(os.path.join(base_dir, 'data', 'bronze')),
            os.path.normpath(os.path.join(base_dir, '..', 'data', 'bronze'))
        ]

        for path in possible:
            if os.path.isdir(path):
                # look for any json file inside
                for fname in os.listdir(path):
                    if fname.lower().endswith('.json'):
                        json_path = os.path.join(path, fname)
                        break
                else:
                    json_path = None
            else:
                json_path = path

            if json_path and os.path.exists(json_path):
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        loaded = json.load(f)
                        if isinstance(loaded, list):
                            candidatos = loaded
                        elif isinstance(loaded, dict):
                            # try common keys
                            candidatos = loaded.get('candidates') or loaded.get('applicants') or loaded.get('rows') or loaded.get('data') or []
                        # if still dict/str, leave candidatos None
                except Exception:
                    candidatos = None

            if candidatos:
                break

    # 3) Try NDJSON (newline-delimited JSON)
    if not candidatos:
        try_paths = [
            os.path.normpath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'bronze', 'applicants.ndjson'))
        ]
        for p in try_paths:
            if os.path.exists(p):
                candidatos = []
                try:
                    with open(p, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                candidatos.append(json.loads(line))
                            except Exception:
                                continue
                except Exception:
                    candidatos = None
                if candidatos:
                    break

    # 4) If still nothing, provide a small example dataset so the UI can show results
    if not candidatos:
        candidatos = [
            {
                'infos_basicas_nome': 'Maria Silva',
                'informacoes_profissionais_titulo_profissional': 'Software Engineer',
                'informacoes_profissionais_conhecimentos_tecnicos': 'Python, APIs, Docker',
                'informacoes_profissionais_area_atuacao': 'Backend'
            },
            {
                'infos_basicas_nome': 'João Souza',
                'informacoes_profissionais_titulo_profissional': 'Data Scientist',
                'informacoes_profissionais_conhecimentos_tecnicos': 'Python, pandas, ML',
                'informacoes_profissionais_area_atuacao': 'Data'
            }
        ]

    if not USE_OLLAMA or client is None:
        # local heuristic evaluation with multiple signals
        def _normalize_skills(skills_raw):
            if isinstance(skills_raw, list):
                return [s.strip().lower() for s in skills_raw if isinstance(s, str)]
            return [s.strip().lower() for s in str(skills_raw).split(',') if s.strip()]

        def _extract_years(c):
            # common fields
            candidates_fields = [
                c.get('anos_experiencia'),
                c.get('anos_de_experiencia'),
                c.get('experience_years'),
                c.get('experiencia'),
                c.get('informacoes_profissionais_anos_experiencia'),
            ]
            for val in candidates_fields:
                if val is None:
                    continue
                try:
                    return int(val)
                except Exception:
                    # try parse numbers from strings like '5 years'
                    import re
                    s = str(val)
                    m = re.search(r"(\d+)", s)
                    if m:
                        return int(m.group(1))
            return None

        def _infer_desired_years(job):
            # infer from role_summary or seniority keywords
            text = ''
            if isinstance(job, dict):
                text = (job.get('role_summary') or '') + ' ' + ' '.join(job.get('responsibilities', []))
            text = text.lower()
            if 'senior' in text:
                return 6
            if 'mid' in text or 'pleno' in text:
                return 3
            if 'junior' in text or 'júnior' in text:
                return 1
            return 3

        required = [s.lower() for s in descricao_vaga.get('required_skills', []) if isinstance(s, str)]
        nice = [s.lower() for s in descricao_vaga.get('nice_to_have', []) if isinstance(s, str)]
        desired_years = _infer_desired_years(descricao_vaga)

        results = []
        for c in candidatos:
            name = c.get('infos_basicas_nome') or c.get('name') or 'N/A'
            title = c.get('informacoes_profissionais_titulo_profissional') or c.get('title') or ''
            skills_raw = c.get('informacoes_profissionais_conhecimentos_tecnicos') or c.get('technical_skills') or ''
            cand_skills = _normalize_skills(skills_raw)

            matched_required = [r for r in required if any(r in ks for ks in cand_skills)]
            matched_nice = [n for n in nice if any(n in ks for ks in cand_skills)]
            missing_required = [r for r in required if r not in matched_required]

            # experience
            years = _extract_years(c) or 0
            exp_score = min(years / max(1, desired_years), 1.0)

            # title/area match
            area = descricao_vaga.get('area') or ''
            title_match = 1.0 if (title and any(tok in title.lower() for tok in (descricao_vaga.get('role_summary') or '').lower().split()[:2])) else 0.0
            area_match = 1.0 if (area and area.lower() in (c.get('informacoes_profissionais_area_atuacao') or '').lower()) else 0.0
            title_area_score = max(title_match, area_match)

            # skill ratios
            req_ratio = (len(matched_required) / max(1, len(required))) if required else 0
            nice_ratio = (len(matched_nice) / max(1, len(nice))) if nice else 0

            # weighted score
            score = 0.6 * (0.8 * req_ratio + 0.2 * nice_ratio) + 0.25 * exp_score + 0.15 * title_area_score
            fit_score = int(max(0, min(1, score)) * 100)

            strengths = matched_required + matched_nice
            gaps = missing_required

            results.append({
                'name': name,
                'title': title,
                'technical_skills': cand_skills,
                'strengths': strengths,
                'gaps': gaps,
                'years_experience': years,
                'fit_score': fit_score
            })

        results.sort(key=lambda x: x.get('fit_score', 0), reverse=True)
        return {'selected_candidates': results[:10]}

    # Otherwise use Ollama
    try:
        user_prompt = build_user_prompt(descricao_vaga, candidatos)

        response = client.chat(
            model='llama3.2:1b',
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]
        )

        content = response['message']['content']

        try:
            return json.loads(content)
        except:
            return content

    except Exception as e:
        return {"error": str(e)}