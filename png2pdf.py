"""
PNG2PDF by Jair Lima
Converte imagens PNG (e outros formatos) em PDFs pesquisaveis com OCR,
filtrando por conteudo textual extraido via Tesseract.
"""

import argparse
import ctypes
import functools
import os
import sys
import time
from pathlib import Path

# Forcar output sem buffer
print = functools.partial(print, flush=True)

import pytesseract
from PIL import Image

# Caminhos possiveis do Tesseract no Windows
_TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
]

for _path in _TESSERACT_PATHS:
    if os.path.exists(_path):
        pytesseract.pytesseract.tesseract_cmd = _path
        break

# Pasta padrao para busca
PASTA_PADRAO = os.getcwd()

# Extensoes de imagem suportadas
EXTENSOES_PADRAO = ["png"]


def copiar_timestamps(origem: str, destino: str):
    """Copia timestamps (criacao, modificacao, acesso) do arquivo de origem para o destino."""
    stat_origem = os.stat(origem)

    # Copiar mtime e atime
    os.utime(destino, (stat_origem.st_atime, stat_origem.st_mtime))

    # Copiar creation time no Windows via ctypes
    try:
        kernel32 = ctypes.windll.kernel32
        FILE_WRITE_ATTRIBUTES = 0x100
        OPEN_EXISTING = 3
        FILE_FLAG_BACKUP_SEMANTICS = 0x02000000

        handle = kernel32.CreateFileW(
            destino,
            FILE_WRITE_ATTRIBUTES,
            0,
            None,
            OPEN_EXISTING,
            FILE_FLAG_BACKUP_SEMANTICS,
            None,
        )

        if handle != -1:
            # Ler creation time do arquivo de origem
            handle_origem = kernel32.CreateFileW(
                origem,
                0x80000000,  # GENERIC_READ
                1,  # FILE_SHARE_READ
                None,
                OPEN_EXISTING,
                FILE_FLAG_BACKUP_SEMANTICS,
                None,
            )

            if handle_origem != -1:
                creation_time = ctypes.c_ulonglong()
                kernel32.GetFileTime(
                    handle_origem, ctypes.byref(creation_time), None, None
                )
                kernel32.CloseHandle(handle_origem)

                # Aplicar creation time no destino
                kernel32.SetFileTime(
                    handle, ctypes.byref(creation_time), None, None
                )

            kernel32.CloseHandle(handle)
    except Exception:
        pass  # Se falhar no Windows, pelo menos mtime/atime ja foram copiados


def extrair_texto_ocr(caminho_imagem: str) -> str:
    """Extrai texto da imagem usando Tesseract OCR."""
    try:
        img = Image.open(caminho_imagem)
        texto = pytesseract.image_to_string(img, lang="por+eng")
        return texto
    except Exception as e:
        print(f"  ERRO ao fazer OCR de {caminho_imagem}: {e}")
        return ""


def gerar_pdf_pesquisavel(caminho_imagem: str, caminho_pdf: str):
    """Gera um PDF pesquisavel (com camada OCR) a partir da imagem."""
    img = Image.open(caminho_imagem)
    pdf_bytes = pytesseract.image_to_pdf_or_hocr(img, lang="por+eng", extension="pdf")
    with open(caminho_pdf, "wb") as f:
        f.write(pdf_bytes)


def buscar_imagens(pasta: str, extensoes: list[str]) -> list[str]:
    """Busca recursivamente arquivos de imagem na pasta e subpastas."""
    arquivos = []
    for ext in extensoes:
        for caminho in Path(pasta).rglob(f"*.{ext}"):
            arquivos.append(str(caminho))
    arquivos.sort()
    return arquivos


def processar(termo_busca: str | None, pasta: str, extensoes: list[str]):
    """Processa as imagens: faz OCR, filtra por termo e converte para PDF."""
    print(f"PNG2PDF by Jair Lima")
    print(f"{'=' * 40}")
    print(f"Pasta: {pasta}")
    print(f"Extensoes: {', '.join(extensoes)}")
    if termo_busca:
        print(f"Filtro: '{termo_busca}'")
    else:
        print(f"Filtro: nenhum (convertendo todos)")
    print(f"{'=' * 40}\n")

    imagens = buscar_imagens(pasta, extensoes)
    print(f"Encontradas {len(imagens)} imagens.\n")

    convertidos = 0
    pulados_pdf_existe = 0
    pulados_sem_match = 0
    erros = 0

    for i, caminho_img in enumerate(imagens, 1):
        nome_base = os.path.splitext(caminho_img)[0]
        caminho_pdf = nome_base + ".pdf"

        print(f"[{i}/{len(imagens)}] {os.path.basename(caminho_img)}")

        # Verificar se PDF ja existe
        if os.path.exists(caminho_pdf):
            print(f"  PDF ja existe. Pulando.")
            pulados_pdf_existe += 1
            continue

        # Fazer OCR para extrair texto
        texto = extrair_texto_ocr(caminho_img)

        if not texto.strip():
            print(f"  Nenhum texto extraido. Pulando.")
            erros += 1
            continue

        # Filtrar por termo de busca
        if termo_busca:
            if termo_busca.lower() not in texto.lower():
                print(f"  Termo '{termo_busca}' nao encontrado. Pulando.")
                pulados_sem_match += 1
                continue
            else:
                print(f"  Termo '{termo_busca}' encontrado!")

        # Gerar PDF pesquisavel
        try:
            gerar_pdf_pesquisavel(caminho_img, caminho_pdf)
            copiar_timestamps(caminho_img, caminho_pdf)
            convertidos += 1
            print(f"  PDF criado: {os.path.basename(caminho_pdf)}")
        except Exception as e:
            print(f"  ERRO ao gerar PDF: {e}")
            erros += 1

    # Resumo
    print(f"\n{'=' * 40}")
    print(f"RESUMO")
    print(f"{'=' * 40}")
    print(f"Total de imagens: {len(imagens)}")
    print(f"Convertidos: {convertidos}")
    print(f"Pulados (PDF ja existe): {pulados_pdf_existe}")
    if termo_busca:
        print(f"Pulados (sem match): {pulados_sem_match}")
    print(f"Erros: {erros}")


def main():
    parser = argparse.ArgumentParser(
        description="PNG2PDF by Jair Lima: Converte imagens em PDFs pesquisaveis com OCR.",
        epilog="Exemplos:\n"
        "  png2pdf condominio\n"
        "  png2pdf\n"
        '  png2pdf condominio --pasta "D:\\outra\\pasta"\n'
        "  png2pdf condominio --extensoes png,jpg,jpeg\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "termo",
        nargs="?",
        default=None,
        help="Termo de busca no conteudo OCR (case-insensitive). Se omitido, converte todas as imagens.",
    )
    parser.add_argument(
        "--pasta",
        default=PASTA_PADRAO,
        help=f"Pasta raiz para buscar imagens (padrao: {PASTA_PADRAO})",
    )
    parser.add_argument(
        "--extensoes",
        default=",".join(EXTENSOES_PADRAO),
        help="Extensoes de arquivo separadas por virgula (padrao: png)",
    )

    args = parser.parse_args()
    extensoes = [e.strip().lower() for e in args.extensoes.split(",")]

    if not os.path.isdir(args.pasta):
        print(f"ERRO: Pasta nao encontrada: {args.pasta}")
        sys.exit(1)

    processar(args.termo, args.pasta, extensoes)


if __name__ == "__main__":
    main()
