"""Indexa a Library Reference da documentação do Python (HTML) no ChromaDB.

Uso:
    python ingest.py CAMINHO_DA_DOC_EXTRAIDA [--version 3.13]

CAMINHO_DA_DOC_EXTRAIDA é a pasta que contém `library/` (ou uma pasta acima dela),
obtida ao extrair o zip "HTML" de https://docs.python.org/3/download.html
"""
import argparse
import re
import shutil
from pathlib import Path

import chromadb
from bs4 import BeautifulSoup, Tag
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

from config import COLLECTION, DB_PATH, EMBED_MODEL

MAX_CHARS = 1500
MIN_CHARS = 80
HEADING = re.compile(r"^h[1-6]$")


def clean(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" ?\n ?", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def split_text(text: str, max_chars: int = MAX_CHARS) -> list[str]:
    """Divide em pedaços de até ~max_chars, preferindo quebrar entre parágrafos."""
    pieces, current = [], ""
    for para in text.split("\n\n"):
        if current and len(current) + len(para) + 2 > max_chars:
            pieces.append(current.strip())
            current = ""
        if len(para) > max_chars:
            for line in para.split("\n"):
                if current and len(current) + len(line) + 1 > max_chars:
                    pieces.append(current.strip())
                    current = ""
                current += line + "\n"
            current += "\n"
        else:
            current += para + "\n\n"
    if current.strip():
        pieces.append(current.strip())
    return pieces


def node_text(node) -> str:
    return node.get_text() if isinstance(node, Tag) else str(node)


def extract_chunks(html_file: Path, base_url: str):
    soup = BeautifulSoup(html_file.read_text(encoding="utf-8"), "lxml")
    body = soup.select_one("div.body")
    if body is None:
        return

    for link in body.select("a.headerlink"):
        link.decompose()
    for pre in body.find_all("pre"):
        pre.replace_with("\n\n```\n" + pre.get_text() + "\n```\n\n")

    h1 = body.find("h1")
    page_title = h1.get_text(" ", strip=True) if h1 else html_file.stem

    for section in body.find_all("section"):
        heading = section.find(HEADING, recursive=False)
        if heading is None:
            continue
        title = heading.get_text(" ", strip=True)

        # Só o texto "próprio" da seção; subseções viram chunks separados.
        parts = [
            node_text(child)
            for child in section.children
            if not (isinstance(child, Tag) and (child.name == "section" or HEADING.match(child.name)))
        ]
        text = clean("".join(parts))
        if len(text) < MIN_CHARS:
            continue

        full_title = page_title if title == page_title else f"{page_title} › {title}"
        section_id = section.get("id", "")
        url = base_url + html_file.name + (f"#{section_id}" if section_id else "")

        for piece in split_text(text):
            yield {"text": f"{full_title}\n{piece}", "title": full_title, "url": url}


def find_library_dir(root: Path) -> Path:
    lib = root / "library"
    if lib.is_dir():
        return lib
    found = list(root.glob("*/library"))
    if found:
        return found[0]
    raise SystemExit(f"Não encontrei a pasta 'library' dentro de {root}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("docs_dir", help="pasta com a documentação HTML extraída")
    parser.add_argument("--version", default="3", help="versão usada nas URLs (ex.: 3 ou 3.13)")
    args = parser.parse_args()

    lib_dir = find_library_dir(Path(args.docs_dir))
    base_url = f"https://docs.python.org/{args.version}/library/"

    print(f"Lendo {lib_dir} ...")
    chunks = [
        chunk
        for html_file in sorted(lib_dir.glob("*.html"))
        for chunk in extract_chunks(html_file, base_url)
    ]
    print(f"{len(chunks)} trechos extraídos.")

    model = SentenceTransformer(EMBED_MODEL)
    model.max_seq_length = 512

    shutil.rmtree(DB_PATH, ignore_errors=True)
    collection = chromadb.PersistentClient(path=DB_PATH).create_collection(
        COLLECTION, metadata={"hnsw:space": "cosine"}
    )

    batch_size = 64
    for start in tqdm(range(0, len(chunks), batch_size), desc="Indexando"):
        batch = chunks[start : start + batch_size]
        embeddings = model.encode(
            ["passage: " + c["text"] for c in batch], normalize_embeddings=True
        ).tolist()
        collection.add(
            ids=[str(start + i) for i in range(len(batch))],
            documents=[c["text"] for c in batch],
            embeddings=embeddings,
            metadatas=[{"title": c["title"], "url": c["url"]} for c in batch],
        )

    print("Pronto! Agora rode: streamlit run app.py")


if __name__ == "__main__":
    main()
