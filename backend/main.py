from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from pathlib import Path
import io

from schemas import PromptRequest, PromptResponse, RefineRequest, RefineResponse, GoogleFormWebhook, LocadoraPromptRequest
from ai_service import refine_prompt, preprocess_briefing, structure_catalog_from_text

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

# Mapeamento de templates
TEMPLATE_MAP = {
    "atendente_geral": "base_atendente.jinja2",
    "locadora_equipamentos": "locadora_equipamentos.jinja2",
}


@app.get("/")
async def root():
    """Serve o frontend"""
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "API Gerador de Prompts"}


@app.post("/generate", response_model=PromptResponse)
async def generate_prompt(request: dict):
    """
    Gera um prompt completo baseado nos dados fornecidos.
    Detecta o tipo de template e usa o schema correto.
    """
    template_type = request.get("template_type", "atendente_geral")
    template_name = TEMPLATE_MAP.get(template_type)

    if not template_name:
        raise HTTPException(status_code=400, detail="Tipo de template inválido")

    try:
        template = jinja_env.get_template(template_name)
    except TemplateNotFound:
        raise HTTPException(status_code=500, detail="Template não encontrado")

    # Validar com o schema correto
    if template_type == "locadora_equipamentos":
        validated = LocadoraPromptRequest(**request)
    else:
        validated = PromptRequest(**request)

    dados_originais = validated.model_dump()

    # Pré-processar briefing com IA (apenas para atendente_geral)
    if template_type == "atendente_geral":
        try:
            dados_processados = await preprocess_briefing(dados_originais)
        except Exception:
            dados_processados = dados_originais
    else:
        dados_processados = dados_originais

    # Renderizar o template com os dados processados
    prompt = template.render(**dados_processados)

    return PromptResponse(prompt=prompt)


@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Recebe um PDF, extrai texto e usa IA para estruturar
    o catálogo de equipamentos em categorias.
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF são aceitos")

    contents = await file.read()

    if len(contents) > 4 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Arquivo muito grande (máx 4MB)")

    # Import lazy para não impactar cold start
    import pdfplumber

    extracted_text = ""
    try:
        with pdfplumber.open(io.BytesIO(contents)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    extracted_text += page_text + "\n"

                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        cleaned = [cell or "" for cell in row]
                        extracted_text += " | ".join(cleaned) + "\n"
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar PDF: {str(e)}")

    if not extracted_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Não foi possível extrair texto do PDF. Verifique se o PDF contém texto selecionável."
        )

    # Usar IA para estruturar o catálogo
    try:
        structured = await structure_catalog_from_text(extracted_text)
    except Exception:
        structured = {"categorias": []}

    return {
        "success": True,
        "raw_text": extracted_text[:5000],
        "categorias": structured.get("categorias", []),
    }


@app.post("/webhook/google-forms")
async def webhook_google_forms(data: GoogleFormWebhook):
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


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
