import os
import json
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

# Cliente ASYNC inicializado de forma lazy
_client = None


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY não configurada no arquivo .env")
        _client = AsyncOpenAI(api_key=api_key, timeout=30.0)
    return _client


# ============================================================
# PRÉ-PROCESSAMENTO DO BRIEFING (Anti-Papagaio)
# ============================================================

PREPROCESSOR_PROMPT = """Você é um Senior Prompt Engineer especialista em chatbots de WhatsApp.
Sua tarefa é INTERPRETAR e TRANSFORMAR um briefing bruto em dados limpos e profissionais.

⚠️ REGRAS CRÍTICAS:

1. **INTERPRETE, NÃO COPIE (Anti-Papagaio):**
   - Se um campo disser "Gostaria de sugestões", "Preciso de ajuda", ou algo vago → CRIE conteúdo profissional apropriado
   - Se disser "Acredito que preços só no WhatsApp" → Transforme em regra: "Não informe preços. Diga que o consultor enviará os valores pelo WhatsApp."
   - NUNCA copie frases vagas literalmente

2. **HIGIENIZAÇÃO DE DADOS:**
   - Corrija erros de português e pontuação
   - Separe endereço e horário de funcionamento se estiverem juntos
   - Formate horários: "das 7 as. 17" → "07:00 às 17:00"
   - Se catálogo estiver bagunçado ou disser "Precisa de todos os itens?", deixe vazio

3. **REGRAS DE PREÇO:**
   - Se mencionar que não quer dar preço → Crie regra clara proibindo
   - Se mencionar que preço só pelo consultor → Crie regra direcionando

4. **TRATAMENTO DE OBJEÇÕES:**
   - Se disser "Preciso de sugestões" → Crie uma resposta profissional para quando cliente achar caro
   - Exemplo: "Entendo sua preocupação! Nossos preços refletem a qualidade e garantia do serviço. Posso te passar para um especialista que vai encontrar a melhor opção pro seu orçamento?"

5. **MENSAGEM DE BOAS-VINDAS:**
   - Se estiver vaga → Crie uma mensagem acolhedora e profissional para a empresa

6. **LÓGICA DE TRANSFERÊNCIA (Anti-Loop):**
   - Se a opção do menu for o caminho principal (ex: Orçamento, Cotação, Agendar), NUNCA coloque "Transfira imediatamente".
   - A regra deve ser: "Transfira APÓS concluir o Passo Final do Fluxo de Coleta".
   - "Transfira imediatamente" serve APENAS para opções de fuga (ex: "Falar com Atendente", "Suporte", "Reclamação").
   - Se o campo opcoes_transbordo_imediato tiver opção principal como "Orçamento", LIMPE esse campo (deixe vazio/null).

Retorne APENAS um JSON válido com os campos processados. Mantenha campos que já estão bons."""


async def preprocess_briefing(dados: dict) -> dict:
    """
    Usa IA para interpretar e limpar os dados do briefing antes de gerar o prompt.
    """
    client = get_client()

    # Campos que precisam de interpretação inteligente
    campos_para_processar = {
        "mensagem_boas_vindas": dados.get("mensagem_boas_vindas", ""),
        "endereco": dados.get("endereco", ""),
        "horario_funcionamento": dados.get("horario_funcionamento", ""),
        "regra_preco_texto": dados.get("regra_preco_texto", ""),
        "texto_objecoes": dados.get("texto_objecoes", ""),
        "texto_duvida_tecnica": dados.get("texto_duvida_tecnica", ""),
        "produtos_catalogo": dados.get("produtos_catalogo", []),
        "frase_autoridade": dados.get("frase_autoridade", ""),
        "proibicoes_texto": dados.get("proibicoes_texto", ""),
        "nome_empresa": dados.get("nome_empresa", "Empresa"),
        "nome_atendente": dados.get("nome_atendente", "Assistente"),
        "menu_opcoes": dados.get("menu_opcoes", []),
        "opcoes_transbordo_imediato": dados.get("opcoes_transbordo_imediato", ""),
    }

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": PREPROCESSOR_PROMPT},
            {
                "role": "user",
                "content": f"""Processe este briefing e retorne JSON limpo:

```json
{json.dumps(campos_para_processar, ensure_ascii=False, indent=2)}
```

Retorne APENAS o JSON processado, sem explicações."""
            }
        ],
        temperature=0.3,
        max_tokens=2000,
    )

    try:
        # Extrair JSON da resposta
        resposta = response.choices[0].message.content.strip()
        # Remover markdown se presente
        if resposta.startswith("```"):
            resposta = resposta.split("```")[1]
            if resposta.startswith("json"):
                resposta = resposta[4:]

        campos_processados = json.loads(resposta)

        # Mesclar campos processados com dados originais
        dados_finais = dados.copy()
        dados_finais.update(campos_processados)

        return dados_finais

    except (json.JSONDecodeError, IndexError):
        # Se falhar, retorna dados originais
        return dados


# ============================================================
# ESTRUTURAÇÃO DE CATÁLOGO DE PDF
# ============================================================

CATALOG_STRUCTURER_PROMPT = """Você é um especialista em catálogos de locação de equipamentos.
Dado o texto extraído de um PDF de catálogo, organize-o em categorias com seus itens.

Retorne APENAS um JSON válido no formato:
{
  "categorias": [
    {
      "categoria": "Concreto e Alvenaria",
      "itens": ["Betoneira 400L", "Vibrador de Concreto", "Régua Vibratória"]
    },
    {
      "categoria": "Compactação",
      "itens": ["Placa Vibratória", "Rolo Compactador", "Sapo Compactador"]
    }
  ]
}

Categorias típicas: Concreto e Alvenaria, Compactação, Corte e Perfuração, Elevação e Transporte,
Estrutura e Apoio, Ferramentas Elétricas, Containers, Equipamentos Especializados,
Geração de Energia, Demolição, Jardinagem, Pintura, Limpeza, etc.

- Agrupe itens similares na mesma categoria
- Use nomes comerciais dos equipamentos
- Se o texto não parecer um catálogo de equipamentos, retorne categorias vazias."""


async def structure_catalog_from_text(raw_text: str) -> dict:
    """Usa IA para estruturar texto bruto de PDF em categorias de equipamentos."""
    client = get_client()

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": CATALOG_STRUCTURER_PROMPT},
            {"role": "user", "content": f"Texto extraído do PDF:\n\n{raw_text[:4000]}"}
        ],
        temperature=0.2,
        max_tokens=2000,
    )

    resposta = response.choices[0].message.content.strip()
    if resposta.startswith("```"):
        resposta = resposta.split("```")[1]
        if resposta.startswith("json"):
            resposta = resposta[4:]

    return json.loads(resposta)


# ============================================================
# REFINAMENTO DE PROMPT
# ============================================================

SYSTEM_PROMPT = """Você é um especialista em criar e refinar prompts para assistentes de IA de atendimento ao cliente no WhatsApp.

Sua tarefa é modificar o prompt fornecido seguindo a instrução do usuário.

REGRAS IMPORTANTES:
1. Mantenha SEMPRE a estrutura de seções numeradas (## 1) Identidade, ## 2) Menu Inicial, etc.)
2. Preserve as variáveis Jinja2 existentes ({{ variavel }}) quando apropriado
3. Mantenha o tom profissional e as regras de atendimento
4. Retorne APENAS o prompt modificado, sem explicações adicionais
5. Se a instrução pedir para adicionar uma nova seção, adicione no local mais apropriado mantendo a numeração
6. Mantenha o formato Markdown

Retorne apenas o prompt refinado, nada mais."""


async def refine_prompt(prompt_atual: str, instrucao: str) -> str:
    """
    Refina um prompt existente usando GPT-4 baseado na instrução do usuário.
    """
    client = get_client()

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"""PROMPT ATUAL:
{prompt_atual}

---

INSTRUÇÃO DO USUÁRIO:
{instrucao}

---

Retorne o prompt modificado:""",
            },
        ],
        temperature=0.3,
        max_tokens=4000,
    )

    return response.choices[0].message.content.strip()
