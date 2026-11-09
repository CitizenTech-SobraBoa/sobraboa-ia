from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json
import os
import requests
from io import BytesIO
from PIL import Image
import google.generativeai as genai

app = FastAPI(
    title="SobraBoa IA API",
    description="API de triagem inteligente de alimentos para a plataforma SobraBoa",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
genai.configure(api_key=GEMINI_API_KEY)
MODELO = "gemini-3.5-flash-lite"

SYSTEM_PROMPT = """
Você é o assistente de triagem de alimentos do SobraBoa, uma plataforma brasileira
de redistribuição de excedentes alimentares que conecta pequenos comércios
(padarias, feiras, restaurantes) a ONGs e cozinhas comunitárias.

Seu papel é analisar alimentos que doadores desejam publicar na plataforma e retornar
uma avaliação estruturada com base nas seguintes categorias cadastradas no sistema:

CATEGORIAS VÁLIDAS:
- Pães e Confeitaria
- Hortifrúti
- Cozinhados e Refeições Prontas
- Laticínios
- Carnes e Proteínas
- Bebidas
- Mercearia
- Outros

REGRAS DE AVALIAÇÃO:
- Alimentos com mofo visível, odor suspeito descrito ou deterioração aparente devem ser RECUSADOS
- Laticínios e carnes exigem cadeia de frio obrigatória
- Validade estimada deve ser conservadora (melhor pecar pelo excesso de cautela)
- Base legal: Lei nº 14.016/2020 (doação de alimentos no Brasil)
- Em caso de dúvida sobre a segurança, recuse o alimento

FORMATO DE RESPOSTA (sempre retorne JSON válido):
{
  "proprio_para_doacao": true ou false,
  "categoria": "uma das categorias acima",
  "requer_refrigeracao": true ou false,
  "validade_estimada": "ex: 1 dia, 3 dias, 1 semana",
  "cuidados_transporte": "orientação resumida",
  "observacoes": "informações adicionais relevantes",
  "motivo_recusa": "preencher apenas se proprio_para_doacao for false"
}
"""

modelo_analise = genai.GenerativeModel(
    model_name=MODELO,
    system_instruction=SYSTEM_PROMPT
)

modelo_chat = genai.GenerativeModel(
    model_name=MODELO,
    system_instruction=SYSTEM_PROMPT
)


# ---- modelos de dados ----

class AnalisarRequest(BaseModel):
    url_imagem: str
    descricao_extra: Optional[str] = ""

class ChatRequest(BaseModel):
    mensagem: str
    contexto_analise: Optional[dict] = None
    historico: Optional[list] = []


# ---- funções auxiliares ----

def carregar_imagem_url(url: str) -> Image.Image:
    resposta = requests.get(url, timeout=10)
    if resposta.status_code != 200:
        raise HTTPException(status_code=400, detail="Não foi possível carregar a imagem da URL fornecida.")
    return Image.open(BytesIO(resposta.content))


# ---- endpoints ----

@app.get("/")
def root():
    return {"mensagem": "SobraBoa IA API no ar", "versao": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analisar-alimento")
def analisar_alimento(req: AnalisarRequest):
    """
    Recebe a URL de uma imagem e uma descrição opcional do alimento.
    Retorna uma análise estruturada em JSON com a avaliação de doação.
    """
    try:
        imagem = carregar_imagem_url(req.url_imagem)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Erro ao processar a imagem.")

    prompt = "Analise este alimento para doação na plataforma SobraBoa e retorne apenas o JSON de avaliação."
    if req.descricao_extra:
        prompt += f"\n\nInformação adicional do doador: {req.descricao_extra}"

    try:
        resposta = modelo_analise.generate_content([prompt, imagem])
        texto = resposta.text.strip()

        # remove blocos de markdown se o modelo os incluir
        if texto.startswith("```"):
            texto = texto.split("```")[1]
            if texto.startswith("json"):
                texto = texto[4:]

        resultado = json.loads(texto)
        return resultado

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="A IA retornou uma resposta em formato inválido.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na análise: {str(e)}")


@app.post("/chat")
def chat(req: ChatRequest):
    """
    Chat contextual sobre um alimento já analisado.
    Aceita o resultado da análise anterior como contexto.
    """
    contexto = ""
    if req.contexto_analise:
        contexto = f"\n\nContexto da análise anterior:\n{json.dumps(req.contexto_analise, ensure_ascii=False, indent=2)}\n\n"

    prompt_completo = f"{contexto}Pergunta do doador: {req.mensagem}"

    try:
        resposta = modelo_chat.generate_content(prompt_completo)
        return {"resposta": resposta.text.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no chat: {str(e)}")