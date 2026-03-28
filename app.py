import os
import streamlit as st
import json
from agents.agentjobbuilder import gerar_descricao_vaga
from agents.agentqualifier import avaliar_candidatos


def _local_generate_job_description(company, title, seniority, area, team):
    team_text = f" ({team})" if team else ""
    return {
        "role_summary": f"{title} at {company}{team_text} — {seniority} level role in {area}.",
        "responsibilities": [
            "Deliver against role objectives",
            "Collaborate with cross-functional teams",
            "Write and maintain technical documentation",
        ],
        "required_skills": ["Communication", "Problem solving", "Relevant technical skill"],
        "nice_to_have": ["Experience with LLMs"],
        "soft_skills": ["Teamwork", "Proactivity"]
    }


def _local_evaluate_candidates(job, json_fallback_path=None):
    # Simple heuristic: count overlaps between required_skills and candidate known skills
    candidates = []

    # try to load provided fallback JSON if path supplied
    if json_fallback_path and os.path.exists(json_fallback_path):
        try:
            with open(json_fallback_path, 'r', encoding='utf-8') as f:
                candidates = json.load(f)
        except Exception:
            candidates = []

    # if no candidates loaded, try default path relative to project
    if not candidates:
        default_path = os.path.join(os.path.dirname(__file__), 'data', 'bronze', 'applicants.json')
        if os.path.exists(default_path):
            try:
                with open(default_path, 'r', encoding='utf-8') as f:
                    candidates = json.load(f)
            except Exception:
                candidates = []

    # normalize: expect list of dicts
    if isinstance(candidates, dict):
        candidates = candidates.get('candidates', [])

    required = [s.lower() for s in job.get('required_skills', []) if isinstance(s, str)]

    results = []
    for c in candidates:
        name = c.get('infos_basicas_nome') or c.get('name') or 'N/A'
        skills_raw = c.get('informacoes_profissionais_conhecimentos_tecnicos') or c.get('technical_skills') or ''
        if isinstance(skills_raw, list):
            cand_skills = [s.lower() for s in skills_raw if isinstance(s, str)]
        else:
            cand_skills = [s.strip().lower() for s in str(skills_raw).split(',') if s.strip()]

        overlap = sum(1 for r in required if any(r in ks for ks in cand_skills))
        fit_score = int((overlap / max(1, len(required))) * 100)

        results.append({
            'name': name,
            'title': c.get('informacoes_profissionais_titulo_profissional', ''),
            'technical_skills': cand_skills,
            'strengths': [],
            'gaps': [],
            'fit_score': fit_score
        })

    # sort desc and pick top 10
    results.sort(key=lambda x: x.get('fit_score', 0), reverse=True)
    return {'selected_candidates': results[:10]}

# Configuração da página
st.set_page_config(
    page_title="AI Recruitment Assistant",
    layout="wide"
)

# Estado
if "job_data" not in st.session_state:
    st.session_state.job_data = None

if "candidates_data" not in st.session_state:
    st.session_state.candidates_data = None


# Header
st.title("🤖 AI Recruitment Assistant")
st.markdown("End-to-end recruitment workflow powered by LLM agents")


# =========================
# FORMULÁRIO
# =========================
with st.container():
    st.subheader("📄 Job Configuration")

    col1, col2 = st.columns(2)

    with col1:
        empresa = st.text_input("Company")
        titulo = st.text_input("Role Title")
        senioridade = st.selectbox("Seniority", ["Junior", "Mid", "Senior"])

    with col2:
        area = st.text_input("Area")
        time = st.text_input("Team (optional)")


# =========================
# GERAR VAGA
# =========================
if st.button("✨ Generate Job Description"):

    with st.spinner("Generating job description..."):
        result = gerar_descricao_vaga(empresa, titulo, senioridade, area, time)

        # result can be dict or JSON string or error dict
        if isinstance(result, dict):
            st.session_state.job_data = result
        else:
            try:
                st.session_state.job_data = json.loads(result)
            except Exception:
                st.session_state.job_data = {"raw": str(result)}

        st.session_state.candidates_data = None

    # If agent returned an error, show it and offer local fallback
    if isinstance(st.session_state.job_data, dict) and st.session_state.job_data.get('error'):
        st.error(f"Agent error: {st.session_state.job_data.get('error')}")
        if st.button("Use local template instead"):
            st.session_state.job_data = _local_generate_job_description(empresa, titulo, senioridade, area, time)
            st.session_state.candidates_data = None


# =========================
# EXIBIR VAGA
# =========================
if st.session_state.job_data:

    st.subheader("📌 Job Description")

    job = st.session_state.job_data

    if isinstance(job, dict) and job.get('error'):
        st.error(f"Agent error: {job.get('error')}")
    elif "raw" in job:
        st.write(job["raw"])
    else:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🧾 Summary")
            st.write(job.get("role_summary", ""))

            st.markdown("### ⚙️ Responsibilities")
            for item in job.get("responsibilities", []):
                st.write(f"- {item}")

        with col2:
            st.markdown("### 🛠 Required Skills")
            for item in job.get("required_skills", []):
                st.write(f"- {item}")

            st.markdown("### ⭐ Nice to Have")
            for item in job.get("nice_to_have", []):
                st.write(f"- {item}")

            st.markdown("### 🤝 Soft Skills")
            for item in job.get("soft_skills", []):
                st.write(f"- {item}")


    # =========================
    # BOTÃO DE MATCH
    # =========================
    if st.button("🔍 Find Best Candidates"):

        with st.spinner("Analyzing candidates..."):
            result = avaliar_candidatos(st.session_state.job_data)

            if isinstance(result, dict):
                st.session_state.candidates_data = result
            else:
                try:
                    st.session_state.candidates_data = json.loads(result)
                except Exception:
                    st.session_state.candidates_data = {"raw": str(result)}

        # If agent errored, show and offer local evaluation
        if isinstance(st.session_state.candidates_data, dict) and st.session_state.candidates_data.get('error'):
            st.error(f"Agent error: {st.session_state.candidates_data.get('error')}")
            if st.button("Use local evaluation instead"):
                # attempt to use fallback JSON in data/bronze
                fallback_json = os.path.join(os.path.dirname(__file__), 'data', 'bronze', 'applicants.json')
                st.session_state.candidates_data = _local_evaluate_candidates(st.session_state.job_data, fallback_json)


# =========================
# EXIBIR CANDIDATOS
# =========================
if st.session_state.candidates_data:

    st.subheader("🏆 Top Candidates")

    data = st.session_state.candidates_data

    if isinstance(data, dict) and data.get('error'):
        st.error(f"Agent error: {data.get('error')}")
    elif "raw" in data:
        st.write(data["raw"])
    else:
        for idx, candidate in enumerate(data.get("selected_candidates", []), 1):

            with st.expander(f"Candidate #{idx} - {candidate.get('name', 'N/A')}"):

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"**Title:** {candidate.get('title', '')}")

                    st.markdown("**💪 Strengths**")
                    for s in candidate.get("strengths", []):
                        st.write(f"- {s}")

                    st.markdown("**⚠️ Gaps**")
                    for g in candidate.get("gaps", []):
                        st.write(f"- {g}")

                with col2:
                    st.markdown("**🛠 Skills**")
                    for skill in candidate.get("technical_skills", []):
                        st.write(f"- {skill}")

                    st.markdown(f"**📊 Fit Score:** {candidate.get('fit_score', 0)}")