import os
from pathlib import Path
from typing import Dict, Any
from llama_parse import LlamaParse
from dotenv import load_dotenv

load_dotenv()

def parse(
    pdf_path: str | Path,
    output_dir: str | Path = None,
) -> Dict[str, Any]:

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF não encontrado: {pdf_path}")

    api_key = os.getenv("LLAMA_CLOUD_API_KEY")
    if not api_key:
        raise ValueError("LLAMA_CLOUD_API_KEY não encontrada no .env")

    parser = LlamaParse(
        api_key=api_key,
        result_type="markdown",
        verbose=True,
        language="pt",
        system_prompt="""Você é um especialista em extração de documentos financeiros.
        Extraia todo o conteúdo mantendo a estrutura original de:
        - Tabelas financeiras (valuation, P&L, balanço)
        - Cabeçalhos e seções hierárquicas
        - Números com precisão (valores monetários, percentuais, múltiplos)
        - Estruturas de deals (EV, equity, debt, earnout)
        Preserve formatação e contexto.""",
        parse_mode="parse_page_with_llm",
        num_workers=4,
    )

    print(f"Processando...: {pdf_path.name}")

    documents = parser.load_data(str(pdf_path))

    chunks = []
    for i, doc in enumerate(documents, start=1):
        chunks.append(f"=== PAGE {i} ===")
        chunks.append(doc.text)
    full_text = "\n\n".join(chunks)

    result = {
        "filename": pdf_path.name,
        "text": full_text,
        "length": len(full_text),
        "pages": len(documents),
        "output_file": None,
    }

    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{pdf_path.stem}_parsed.txt"
        output_file.write_text(full_text, encoding="utf-8")
        result["output_file"] = str(output_file)
        print(f"   ✓ Salvo: {output_file}")

    print(f"   ✓ {len(documents)} páginas | {len(full_text):,} caracteres\n")
    return result