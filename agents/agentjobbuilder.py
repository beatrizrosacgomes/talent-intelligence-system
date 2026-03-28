import os
import json

USE_OLLAMA = os.environ.get('USE_OLLAMA', '0') == '1'
client = None
if USE_OLLAMA:
    try:
        from ollama import Client
        client = Client(host='http://localhost:11434')
    except Exception:
        client = None


SYSTEM_PROMPT = """
You are a senior HR specialist and employer branding expert.

Your goal is to create high-quality, attractive, and structured job descriptions aligned with market best practices.

Guidelines:
- Use clear, professional, and engaging language.
- Focus on realistic responsibilities and skills.
- Avoid generic or vague descriptions.
- Tailor the content to the role, seniority, and business area.
- Keep it concise but impactful.

Output must be valid JSON.
"""


def build_user_prompt(company, title, seniority, area, team):
    team_text = f" within the {team} team" if team else ""

    # Use double braces to include literal JSON braces inside an f-string
    return f"""
Create a job description with the following details:

Company: {company}
Role: {title}
Seniority Level: {seniority}
Area: {area}{team_text}

Instructions:
Generate a structured job description including:

1. Role summary (2-3 sentences)
2. Key responsibilities (3-5 bullet points)
3. Required technical skills (3-5 bullet points)
4. Nice-to-have skills (optional)
5. Soft skills (3-4 bullet points)

Output format (JSON):
{{
    "role_summary": "",
    "responsibilities": [],
    "required_skills": [],
    "nice_to_have": [],
    "soft_skills": []
}}
"""


def gerar_descricao_vaga(empresa, titulo, senioridade, area, time=None):
    # If Ollama usage disabled or client unavailable, return a local template
    if not USE_OLLAMA or client is None:
        team_text = f" ({time})" if time else ""
        return {
            "role_summary": (
                f"We are looking for a {senioridade.lower()} {titulo} to join {empresa}{team_text} in the {area} area. "
                "This role will lead delivery of key projects, collaborate with stakeholders across product and engineering, "
                "and be responsible for driving technical excellence and mentorship."),
            "responsibilities": [
                "Own end-to-end delivery of assigned projects and features.",
                "Design, implement and maintain high-quality solutions with strong testing and documentation.",
                "Collaborate closely with product, design and engineering to define roadmaps and priorities.",
                "Provide technical mentorship and code reviews to junior team members.",
                "Continuously improve workflows, CI/CD and observability for the platform.",
                "Participate in hiring and technical interviews when needed.",
            ],
            "required_skills": [
                "Relevant programming languages and frameworks for the role (e.g. Python, JavaScript)",
                "Experience with version control (Git) and collaborative workflows",
                "Solid understanding of software design principles and testing",
            ],
            "nice_to_have": [
                "Experience with large language models or ML pipelines",
                "Familiarity with cloud platforms (AWS/GCP/Azure)",
            ],
            "soft_skills": ["Communication", "Problem solving", "Leadership", "Proactivity"]
        }

    try:
        user_prompt = build_user_prompt(
            company=empresa,
            title=titulo,
            seniority=senioridade,
            area=area,
            team=time
        )

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
