from fastapi import FastAPI, UploadFile, Request, Path, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import fitz  # PyMuPDF

from openai_chat import formatar_com_gpt
from db import (
    criar_tabela_se_nao_existir,
    criar_tabelas_usuario_e_musica,
    salvar_cifra,
    listar_cifras,
    buscar_cifra_por_id,
    buscar_cifra_por_titulo,
    verificar_login
)

# Inicialização
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="uma_chave_muito_secreta")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Criação das tabelas
criar_tabela_se_nao_existir()
criar_tabelas_usuario_e_musica()

# Utilitário de sessão
def usuario_logado(request: Request):
    return "usuario_id" in request.session

# Redirecionar raiz para login
@app.get("/", response_class=HTMLResponse)
def root():
    return RedirectResponse("/login", status_code=302)

# Tela de login
@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, email: str = Form(...), senha: str = Form(...)):
    usuario = verificar_login(email, senha)
    if usuario:
        request.session["usuario_id"] = usuario[0]
        return RedirectResponse("/historico", status_code=302)
    return HTMLResponse("Login inválido", status_code=401)

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)

@app.get("/historico", response_class=HTMLResponse)
def historico(request: Request):
    if not usuario_logado(request):
        return RedirectResponse("/login", status_code=302)
    cifras = listar_cifras()
    cifras_ordenadas = sorted(cifras, key=lambda x: x[1].lower())
    return templates.TemplateResponse("historico.html", {
        "request": request,
        "cifras": cifras_ordenadas
    })

@app.post("/upload", response_class=HTMLResponse)
async def upload(request: Request, file: UploadFile):
    if not usuario_logado(request):
        return RedirectResponse("/login", status_code=302)
    conteudo_pdf = await file.read()
    texto_extraido = extrair_texto_pdf(conteudo_pdf)
    resposta = formatar_com_gpt(texto_extraido)
    titulo = resposta.get("titulo", "Sem título")
    autor = resposta.get("autor", "Desconhecido")
    cifra = resposta.get("cifra", "")
    salvar_cifra(titulo, autor, cifra)
    linhas = separar_cifras_letra(cifra)
    return templates.TemplateResponse("presentation.html", {
        "request": request,
        "titulo": titulo,
        "autor": autor,
        "linhas": linhas
    })

@app.get("/cifra/{id}", response_class=HTMLResponse)
def ver_cifra(request: Request, id: int = Path(...)):
    if not usuario_logado(request):
        return RedirectResponse("/login", status_code=302)
    resultado = buscar_cifra_por_id(id)
    if not resultado:
        return HTMLResponse(content="Cifra não encontrada", status_code=404)
    _, titulo, autor, cifra = resultado
    linhas = separar_cifras_letra(cifra)
    return templates.TemplateResponse("presentation.html", {
        "request": request,
        "titulo": titulo,
        "autor": autor,
        "linhas": linhas
    })

@app.get("/cifra/titulo/{titulo}", response_class=HTMLResponse)
def exibir_cifra_por_titulo(request: Request, titulo: str = Path(...)):
    if not usuario_logado(request):
        return RedirectResponse("/login", status_code=302)
    cifra = buscar_cifra_por_titulo(titulo)
    if cifra is None:
        return HTMLResponse(content="Cifra não encontrada", status_code=404)
    linhas = separar_cifras_letra(cifra["cifra"])
    return templates.TemplateResponse("presentation.html", {
        "request": request,
        "titulo": cifra["titulo"],
        "autor": cifra["autor"],
        "linhas": linhas
    })

# Utilitários

def extrair_texto_pdf(pdf_bytes):
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        texto = "\n".join(page.get_text() for page in doc)
    return texto

def separar_cifras_letra(cifra: str):
    linhas_processadas = []
    for linha in cifra.split('\n'):
        cifra_linha = ""
        letra_linha = ""
        i = 0
        while i < len(linha):
            if linha[i] == '[':
                j = linha.find(']', i)
                if j != -1:
                    acorde = linha[i:j+1]
                    cifra_linha += acorde
                    letra_linha += ' ' * (j + 1 - i)
                    i = j + 1
                else:
                    cifra_linha += linha[i]
                    letra_linha += ' '
                    i += 1
            else:
                cifra_linha += ' '
                letra_linha += linha[i]
                i += 1
        linhas_processadas.append({"cifra": cifra_linha, "letra": letra_linha})
    return linhas_processadas
