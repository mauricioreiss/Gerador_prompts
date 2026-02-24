from pydantic import BaseModel, Field
from typing import Optional, Literal


class Produto(BaseModel):
    nome: str = ""
    precos: str = ""


class CategoriaEquipamento(BaseModel):
    categoria: str = ""
    itens: list[str] = Field(default_factory=list)


class PromptRequest(BaseModel):
    """Todos os campos são opcionais com valores padrão."""

    template_type: Literal["atendente_geral"] = "atendente_geral"

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


class LocadoraPromptRequest(BaseModel):
    """Schema para o template de locadora de equipamentos (estilo JundMega)."""

    template_type: Literal["locadora_equipamentos"] = "locadora_equipamentos"

    # Identidade
    nome_atendente: str = "Assistente"
    nome_empresa: str = "Empresa"
    papel_atendente: str = "acolher, puxar necessidade e agilizar o processo"
    tom_comunicacao: str = "informal, direto/comercial"
    proibicoes: str = "sem emojis, sem formalês, sem parecer IA"

    # Sobre a Empresa
    descricao_empresa: str = ""
    anos_experiencia: str = ""
    diferenciais: str = ""
    foco_atuacao: str = ""
    ticket_medio: str = ""

    # Catálogo de Equipamentos
    categorias_equipamentos: list[CategoriaEquipamento] = Field(default_factory=list)

    # Fluxo de Coleta
    etapas_fluxo: list[str] = Field(default_factory=lambda: [
        "Cumprimentar e perguntar o que precisa",
        "Identificar equipamento necessário",
        "Perguntar período de locação",
        "Solicitar local de entrega",
        "Confirmar data de entrega",
        "Verificar se já tem cadastro",
        "Se não tem cadastro, solicitar documentos",
        "Transferir para vendedor",
    ])

    # Objeções
    objecao_preco: str = ""
    objecao_urgencia: str = ""
    objecao_pechincha: str = ""

    # Comunicação
    max_linhas: int = 3
    regra_sem_valores: bool = True
    regras_comunicacao_extras: list[str] = Field(default_factory=list)

    # Transferência
    condicoes_transferencia: list[str] = Field(default_factory=lambda: [
        "Triagem concluída (equipamento, período, local, data identificados)",
        "Cliente já informou se tem cadastro ou não",
        "Cliente pede falar com vendedor/humano",
        "Conversa sem progresso após 2 tentativas",
    ])
    team_id: str = "1"

    # Guardrails
    guardrails: list[str] = Field(default_factory=list)

    # Instrução Final
    instrucao_final: Optional[str] = None
