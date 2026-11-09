# SobraBoa IA — Triagem Inteligente de Alimentos

> Módulo de Inteligência Artificial da plataforma SobraBoa  
> Global Solution 2026/2 · CitizenTech · FIAP

## Integrantes

| Nome | RM |
|------|----|
| Felipe Kirschner Modesto | RM561810 |
| João Victor Luiz Oliveira Resende | RM565139 |
| Pedro Vaz Ferreira | RM566551 |
| Vitor Dias dos Santos | RM565422 |

---

## Descrição da Funcionalidade

O SobraBoa conecta pequenos comércios (padarias, feiras, restaurantes) que têm excedente de alimentos a ONGs e cozinhas comunitárias. Um dos maiores atritosos no fluxo de doação é o doador não saber se o alimento ainda está próprio para doação, qual categoria usar ou quais cuidados tomar no transporte.

Este módulo resolve esse problema com uma **IA de triagem**: o doador tira uma foto do alimento que deseja publicar, e a IA analisa a imagem e responde com uma avaliação completa — tudo antes de publicar a doação na plataforma.

### Fluxo na plataforma

```
Doador tira foto do alimento
         │
         ▼
   [SobraBoa IA]
   Gemini 3.5 Flash-Lite
   + System Prompt com regras do domínio (RAG básico)
         │
         ├──► JSON estruturado
         │    - categoria do sistema
         │    - próprio para doação (true/false)
         │    - necessidade de refrigeração
         │    - validade estimada
         │    - cuidados de transporte
         │
         └──► Chat contextual
              Doador tira dúvidas sobre aquele alimento específico
```

---

## Tecnologias e Modelos

| Componente | Tecnologia |
|------------|------------|
| Modelo de IA | Gemini 3.5 Flash-Lite (Google DeepMind) |
| Visão Computacional | Gemini Vision (análise de imagem nativa) |
| IA Generativa | Gemini (chat contextual) |
| RAG básico | System prompt com categorias e regras do SobraBoa |
| Ambiente de desenvolvimento | Google Colab |
| Linguagem | Python 3 |

---

## Diagrama da Arquitetura

```
┌─────────────────────────────────────────────────────┐
│                   App Mobile (React Native)          │
│              [tela de publicar doação]               │
└─────────────────────┬───────────────────────────────┘
                      │  imagem (base64) + descrição
                      ▼
┌─────────────────────────────────────────────────────┐
│              sobraboa-api-java (Spring Boot)         │
│         POST /api/ia/analisar-alimento               │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│              Gemini API (Google AI Studio)           │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │  System Prompt (RAG básico)                 │   │
│  │  - 8 categorias do SobraBoa                 │   │
│  │  - regras de refrigeração                   │   │
│  │  - Lei nº 14.016/2020                       │   │
│  │  - critérios de aprovação/recusa            │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  Visão Computacional ──► classifica a imagem        │
│  IA Generativa       ──► responde o chat            │
│                                                     │
│  Modelo: gemini-3.5-flash-lite                      │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
              JSON estruturado
         + chat conversacional contextual
```

---

## Estrutura do Repositório

```
sobraboa-ia/
├── notebook/
│   └── sobraboa_ia.ipynb       # Notebook principal com todos os testes
├── evidencias/
│   ├── teste1_pao_fresco.png   # Print do resultado — alimento aprovado
│   ├── teste2_mofado.png       # Print do resultado — alimento recusado
│   └── teste3_laticinios.png   # Print do resultado — alerta de refrigeração
└── README.md
```

---

## Como Executar

### Pré-requisitos

- Conta Google (para o Colab)
- Chave de API do Gemini — obter em [Google AI Studio](https://aistudio.google.com)

### Passo a passo

1. Acesse [Google Colab](https://colab.research.google.com)
2. **Arquivo → Fazer upload de notebook** → selecione `notebook/sobraboa_ia.ipynb`
3. No menu lateral, clique no ícone de **chave (🔑) → Secrets**
4. Adicione um secret com nome `GEMINI_API_KEY` e cole sua chave de API
5. Execute as células em ordem (**Runtime → Run all**)

---

## Casos de Teste e Resultados

Foram testados três cenários representativos do fluxo real da plataforma:

### Teste 1 — Alimento aprovado (pão fresco)
- **Entrada:** imagem de pão francês + "Saiu do forno há 2 horas"
- **Resultado esperado:** aprovado, categoria Pães e Confeitaria, sem refrigeração, validade ~1 dia
- **Resultado obtido:** ✅ conforme esperado *(ver evidencias/teste1_pao_fresco.png)*

### Teste 2 — Alimento recusado (mofado)
- **Entrada:** imagem de alimento com mofo visível
- **Resultado esperado:** recusado, motivo de recusa informado
- **Resultado obtido:** ✅ conforme esperado *(ver evidencias/teste2_mofado.png)*

### Teste 3 — Alerta de cadeia fria (laticínio)
- **Entrada:** imagem de queijos artesanais + "foram refrigerados até agora"
- **Resultado esperado:** aprovado, categoria Laticínios, refrigeração obrigatória
- **Resultado obtido:** ✅ conforme esperado *(ver evidencias/teste3_laticinios.png)*

---

## Justificativas Técnicas

**Por que Gemini 3.5 Flash-Lite?**  
Modelo multimodal nativo — processa imagem e texto numa única chamada de API, sem necessidade de um modelo separado de visão computacional. É o modelo mais leve e rápido da família Gemini 3.5, ideal para chamadas de alta frequência em produção (cada publicação de doação dispara uma análise).

**Por que RAG básico via system prompt?**  
O domínio do SobraBoa é fechado e bem definido: 8 categorias, regras sanitárias, lei de doação e critérios de aprovação. Um RAG com vector database seria over-engineering para esse volume de contexto. O system prompt fixo garante que a IA sempre responda dentro das regras da plataforma, sem alucinações sobre categorias inexistentes.

**Por que chat contextual pós-análise?**  
O JSON da análise vira o contexto do chat, então o doador não precisa descrever o alimento de novo. Isso reduz atrito na publicação — um dos diferenciais do SobraBoa é "publicar em até 3 toques".

---

## Limitações

- A IA não substitui a inspeção sanitária presencial
- A análise depende da qualidade da foto (iluminação, ângulo)
- Validade estimada é uma orientação — o doador é responsável pela informação real
- A plataforma não certifica a qualidade do alimento (conforme RN09 do SobraBoa)

---

## Declaração de Uso de IA

Este projeto utiliza o modelo Gemini 3.5 Flash-Lite da Google como componente central da funcionalidade de triagem. O código foi desenvolvido pela equipe com apoio de ferramentas de IA generativa para revisão e sugestões. Todo o código foi compreendido e validado pelos integrantes do grupo.

---

## 🔗 Repositórios do Projeto

- **API Java:** [sobraboa-api-java](https://github.com/[org]/sobraboa-api-java)
- **IA:** este repositório
