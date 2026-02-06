from pydantic import BaseModel, Field
from typing import Optional


class Produto(BaseModel):
    nome: str = ""
    precos: str = ""


class PromptRequest(BaseModel):
    """Todos os campos são opcionais com valores padrão."""

    # Identidade
    nome_empresa: str = "Empresa"
    nome_atendente: str = "Assistente"
    papel_ia: str = "atender clientes, tirar dúvidas e direcionar para o atendimento humano"
    estilo_comunicacao: Optional[str] = None
    proibicoes_texto: str = "Nunca pareça uma IA"

    # Menu
    possui_menu: bool = False
    mensagem_boas_vindas: Optional[str] = None
    menu_opcoes: list[str] = Field(default_factory=list)

    # Contexto
    frase_autoridade: str = "Empresa estabelecida no mercado"
    servicos_lista: list[str] = Field(default_factory=list)
    endereco: str = "Consulte nosso atendimento"
    horario_funcionamento: str = "Horário comercial"

    # Regras
    regras_personalizadas: list[str] = Field(default_factory=list)
    regra_marcas_texto: Optional[str] = None
    regra_preco_texto: Optional[str] = None

    # Catálogo
    produtos_catalogo: list[Produto] = Field(default_factory=list)

    # Fluxo
    frase_sondagem: str = "Como posso te ajudar hoje?"
    pergunta_experiencia: str = "É sua primeira vez conosco?"
    possui_treinamento: bool = False
    texto_treinamento: Optional[str] = None
    pergunta_data: Optional[str] = None
    texto_verificacao_cadastro: Optional[str] = None
    texto_documentacao: str = "Preciso de alguns dados para continuar"

    # Objeções
    possui_objecoes: bool = False
    texto_objecoes: Optional[str] = None
    texto_duvida_tecnica: Optional[str] = None

    # Comunicação
    regras_comunicacao: list[str] = Field(default_factory=list)

    # Transferência
    opcoes_transbordo_imediato: Optional[str] = None
    opcoes_transbordo_extras: Optional[str] = None
    team_id: str = "1"

    # Integração
    url_chatwoot: Optional[str] = None
    apikey_chatwoot: Optional[str] = None

    # Extras
    guardrails_extras: list[str] = Field(default_factory=list)
    instrucao_final: Optional[str] = None
    itens_adicionais: Optional[str] = None


class PromptResponse(BaseModel):
    prompt: str


class RefineRequest(BaseModel):
    prompt_atual: str
    instrucao: str


class RefineResponse(BaseModel):
    prompt_refinado: str


class GoogleFormWebhook(BaseModel):
    """Todos os campos opcionais com valores padrão."""

    nome_empresa: str = "Empresa"
    nome_atendente: str = "Assistente"
    papel_ia: str = "atender clientes, tirar dúvidas e direcionar para o atendimento humano"
    proibicoes_texto: str = "Nunca pareça uma IA"
    frase_autoridade: str = "Empresa estabelecida no mercado"
    endereco: str = "Consulte nosso atendimento"
    horario_funcionamento: str = "Horário comercial"
    frase_sondagem: str = "Como posso te ajudar hoje?"
    pergunta_experiencia: str = "É sua primeira vez conosco?"
    texto_documentacao: str = "Preciso de alguns dados para continuar"
    team_id: str = "1"

    estilo_comunicacao: Optional[str] = None
    possui_menu: Optional[bool] = None
    mensagem_boas_vindas: Optional[str] = None
    menu_opcoes: Optional[list[str]] = None
    servicos_lista: Optional[list[str]] = None
    regras_personalizadas: Optional[list[str]] = None
    regra_marcas_texto: Optional[str] = None
    regra_preco_texto: Optional[str] = None
    produtos_catalogo: Optional[list[Produto]] = None
    possui_treinamento: Optional[bool] = None
    texto_treinamento: Optional[str] = None
    pergunta_data: Optional[str] = None
    texto_verificacao_cadastro: Optional[str] = None
    possui_objecoes: Optional[bool] = None
    texto_objecoes: Optional[str] = None
    texto_duvida_tecnica: Optional[str] = None
    regras_comunicacao: Optional[list[str]] = None
    opcoes_transbordo_imediato: Optional[str] = None
    opcoes_transbordo_extras: Optional[str] = None
    url_chatwoot: Optional[str] = None
    apikey_chatwoot: Optional[str] = None
    guardrails_extras: Optional[list[str]] = None
    instrucao_final: Optional[str] = None
    itens_adicionais: Optional[str] = None
    email_destino: Optional[str] = None
