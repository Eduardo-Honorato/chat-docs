# Chat com a biblioteca padrão do Python

Chat que responde perguntas sobre a **biblioteca padrão do Python** com base na documentação oficial
(Library Reference), citando as fontes com links para docs.python.org.

Funciona em português ou inglês: os embeddings são multilíngues, então você pergunta em português e a
busca encontra os trechos em inglês.

## Como funciona

1. `ingest.py` lê o HTML da documentação, divide em seções e guarda os trechos no ChromaDB.
2. A cada pergunta, `rag.py` busca os trechos mais relevantes.
3. Os trechos vão para o Claude, que responde só com base neles e cita as fontes.
4. `app.py` é a interface de chat em Streamlit.

## Requisitos

- Python 3.12 ou 3.13
- Uma chave da API da Anthropic (ou um gateway compatível, veja abaixo)

## Instalação

```powershell
git clone https://github.com/Eduardo-Honorato/chat-docs.git
cd chat-docs
python -m venv .venv
.venv\Scripts\Activate.ps1          # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

## Documentação do Python

A documentação **não** está neste repositório. Baixe o zip **HTML** em
https://docs.python.org/3/download.html, extraia na pasta do projeto e indexe:

```powershell
python ingest.py .\python-3.13-docs-html --version 3.13
```

A indexação roda uma vez (alguns minutos) e cria a pasta `chroma_db/`.

## Executar

```powershell
$env:ANTHROPIC_API_KEY="sua-chave"  # Mac/Linux: export ANTHROPIC_API_KEY="sua-chave"
streamlit run app.py
```

Abra http://localhost:8501.

### Usando um gateway compatível com a API da Anthropic

O SDK lê `ANTHROPIC_BASE_URL`, então dá para apontar para um servidor local compatível:

```powershell
$env:ANTHROPIC_BASE_URL="http://127.0.0.1:8082"
$env:ANTHROPIC_AUTH_TOKEN="seu-token"
$env:ANTHROPIC_API_KEY="seu-token"
```

Nesse caso, quem responde é o modelo configurado no gateway, e a qualidade das respostas e o
cumprimento das regras do prompt (citar fontes, não inventar) dependem dele.

## Configuração

| Variável | Uso | Padrão |
|---|---|---|
| `ANTHROPIC_API_KEY` | chave da API | obrigatória |
| `CLAUDE_MODEL` | modelo usado nas respostas | `claude-sonnet-5-5` |

Outras opções (modelo de embeddings, pasta do banco) ficam em `config.py`.

## Estrutura

```
chat-docs/
├── app.py            # interface de chat (Streamlit)
├── rag.py            # busca + resposta com o Claude
├── ingest.py         # leitura e indexação da documentação
├── config.py         # configurações
├── assets/           # logo
└── requirements.txt
```

## Avisos

- Projeto independente, sem vínculo com a Python Software Foundation nem com a Anthropic.
- "Python" e o logo do Python são marcas da Python Software Foundation.
- A documentação do Python tem licença própria (PSF); por isso ela não é redistribuída aqui.