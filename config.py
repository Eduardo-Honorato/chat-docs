import os

DB_PATH = "chroma_db"
COLLECTION = "python_stdlib"

# Modelo de embeddings multilíngue: permite perguntar em português
# e encontrar trechos da documentação em inglês.
EMBED_MODEL = "intfloat/multilingual-e5-small"

# Modelo do Claude usado nas respostas (pode ser trocado por variável de ambiente).
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")
