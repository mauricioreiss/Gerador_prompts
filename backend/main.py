from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from pathlib import Path
from datetime import datetime
import json

from schemas import PromptRequest, PromptResponse, RefineRequest, RefineResponse, GoogleFormWebhook
from ai_service import refine_prompt, preprocess_briefing

app = FastAPI(
    title="Gerador de Prompts para IA",
    description="API para gerar e refinar prompts de atendentes de WhatsApp",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Caminho do index.html (pasta pai do backend)
index_path = Path(__file__).parent.parent / "index.html"

# Configuração do Jinja2
templates_dir = Path(__file__).parent / "templates"
jinja_env = Environment(loader=FileSystemLoader(templates_dir), trim_blocks=True, lstrip_blocks=True)

# Pasta para salvar prompts gerados
prompts_dir = Path(__file__).parent / "prompts_gerados"
prompts_dir.mkdir(exist_ok=True)


def save_prompt_to_file(nome_empresa: str, prompt: str, dados_originais: dict):
    """Salva o prompt gerado em um arquivo .md"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{nome_empresa.replace(' ', '_')}.md"
    filepath = prompts_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"<!-- Gerado em: {datetime.now().isoformat()} -->\n")
        f.write(f"<!-- Cliente: {nome_empresa} -->\n\n")
        f.write(prompt)

    # Salva também os dados originais em JSON
    json_filepath = prompts_dir / f"{timestamp}_{nome_empresa.replace(' ', '_')}_dados.json"
    with open(json_filepath, "w", encoding="utf-8") as f:
        json.dump(dados_originais, f, ensure_ascii=False, indent=2)

    return filepath


@app.get("/")
async def root():
    """Serve o frontend"""
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "API Gerador de Prompts"}


@app.post("/generate", response_model=PromptResponse)
async def generate_prompt(request: PromptRequest, background_tasks: BackgroundTasks):
    """
    Gera um prompt completo baseado nos dados fornecidos.
    Usa IA para pré-processar e interpretar o briefing (Anti-Papagaio).
    """
    try:
        template = jinja_env.get_template("base_atendente.jinja2")
    except TemplateNotFound:
        raise HTTPException(status_code=500, detail="Template não encontrado")

    # Pré-processar briefing com IA (interpreta campos vagos)
    dados_originais = request.model_dump()
    try:
        dados_processados = await preprocess_briefing(dados_originais)
    except Exception:
        # Se IA falhar, usa dados originais
        dados_processados = dados_originais

    # Renderizar o template com os dados processados
    prompt = template.render(**dados_processados)

    # Salvar em background
    background_tasks.add_task(
        save_prompt_to_file,
        request.nome_empresa,
        prompt,
        dados_processados
    )

    return PromptResponse(prompt=prompt)


@app.post("/webhook/google-forms")
async def webhook_google_forms(data: GoogleFormWebhook, background_tasks: BackgroundTasks):
    """
    Recebe dados do Google Forms via Apps Script e gera o prompt.

    O Google Apps Script deve mapear os campos do form para este schema.
    """
    try:
        template = jinja_env.get_template("base_atendente.jinja2")
    except TemplateNotFound:
        raise HTTPException(status_code=500, detail="Template não encontrado")

    # Converter para PromptRequest (com valores padrão para campos não preenchidos)
    prompt_data = {
        "nome_empresa": data.nome_empresa,
        "nome_atendente": data.nome_atendente,
        "papel_ia": data.papel_ia,
        "estilo_comunicacao": data.estilo_comunicacao or "Máximo 2 frases curtas por parágrafo",
        "proibicoes_texto": data.proibicoes_texto,
        "possui_menu": data.possui_menu if data.possui_menu is not None else bool(data.menu_opcoes),
        "mensagem_boas_vindas": data.mensagem_boas_vindas,
        "menu_opcoes": data.menu_opcoes or [],
        "frase_autoridade": data.frase_autoridade,
        "servicos_lista": data.servicos_lista or [],
        "endereco": data.endereco,
        "horario_funcionamento": data.horario_funcionamento,
        "regras_personalizadas": data.regras_personalizadas or [],
        "regra_marcas_texto": data.regra_marcas_texto,
        "regra_preco_texto": data.regra_preco_texto,
        "produtos_catalogo": [{"nome": p.nome, "precos": p.precos} for p in (data.produtos_catalogo or [])],
        "frase_sondagem": data.frase_sondagem,
        "pergunta_experiencia": data.pergunta_experiencia,
        "possui_treinamento": data.possui_treinamento or False,
        "texto_treinamento": data.texto_treinamento,
        "pergunta_data": data.pergunta_data,
        "texto_verificacao_cadastro": data.texto_verificacao_cadastro,
        "texto_documentacao": data.texto_documentacao,
        "possui_objecoes": data.possui_objecoes or False,
        "texto_objecoes": data.texto_objecoes,
        "regras_comunicacao": data.regras_comunicacao or [],
        "opcoes_transbordo_imediato": data.opcoes_transbordo_imediato,
        "opcoes_transbordo_extras": data.opcoes_transbordo_extras,
        "team_id": data.team_id,
        "url_chatwoot": data.url_chatwoot,
        "apikey_chatwoot": data.apikey_chatwoot,
        "guardrails_extras": data.guardrails_extras or [],
        "instrucao_final": data.instrucao_final,
    }

    # Renderizar o template
    prompt = template.render(**prompt_data)

    # Salvar em background
    background_tasks.add_task(
        save_prompt_to_file,
        data.nome_empresa,
        prompt,
        prompt_data
    )

    return {
        "success": True,
        "message": f"Prompt gerado para {data.nome_empresa}",
        "prompt": prompt
    }


@app.post("/refine", response_model=RefineResponse)
async def refine_prompt_endpoint(request: RefineRequest):
    """
    Refina um prompt existente usando IA (GPT-4).
    """
    if not request.prompt_atual.strip():
        raise HTTPException(status_code=400, detail="Prompt atual não pode estar vazio")

    if not request.instrucao.strip():
        raise HTTPException(status_code=400, detail="Instrução não pode estar vazia")

    try:
        prompt_refinado = await refine_prompt(request.prompt_atual, request.instrucao)
        return RefineResponse(prompt_refinado=prompt_refinado)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao refinar prompt: {str(e)}")


@app.get("/prompts")
async def list_prompts():
    """Lista todos os prompts gerados."""
    prompts = []
    for file in sorted(prompts_dir.glob("*.md"), reverse=True):
        prompts.append({
            "filename": file.name,
            "created_at": file.stat().st_mtime,
            "size": file.stat().st_size
        })
    return {"prompts": prompts[:50]}  # Últimos 50


@app.get("/prompts/{filename}")
async def get_prompt(filename: str):
    """Retorna um prompt específico."""
    filepath = prompts_dir / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Prompt não encontrado")

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    return {"filename": filename, "content": content}


@app.put("/prompts/{filename}")
async def update_prompt(filename: str, data: dict):
    """Atualiza um prompt existente."""
    filepath = prompts_dir / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Prompt não encontrado")

    content = data.get("content", "")
    if not content:
        raise HTTPException(status_code=400, detail="Conteúdo não pode estar vazio")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return {"success": True, "filename": filename}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
