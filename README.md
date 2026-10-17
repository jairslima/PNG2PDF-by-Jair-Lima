# PNG2PDF by Jair Lima

Ferramenta de linha de comando que varre uma pasta (e as subpastas) atrás de imagens, faz OCR com o Tesseract e gera um **PDF pesquisável** só para as imagens cujo texto contém o termo procurado.

## Requisitos

- Python 3.
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) instalado (no Windows, procura em `C:\Program Files\Tesseract-OCR`), com os idiomas `por` e `eng`.
- `pip install -r requirements.txt`

## Uso

```bash
python png2pdf.py condominio                       # varre a pasta atual
python png2pdf.py condominio --pasta "D:\\Fotos"      # varre outra pasta
```

## Comportamento

- O PDF ganha o mesmo nome base da imagem e copia as datas do arquivo original.
- PDFs que já existem nunca são sobrescritos.
- O OCR usa `por+eng` juntos para documentos em português.
- Imagens sem texto reconhecível (gráficos, QR codes) são contadas como erro e puladas.

## Licença

MIT, veja [LICENSE](LICENSE).
