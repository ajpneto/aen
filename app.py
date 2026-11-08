"""
AENTECH — Backend Flask & RESTful API Unificada
Gestão Completa de Ordens de Serviço (OS), Autenticação JWT, SQLite + SQLAlchemy,
Painel Administrativo e Notificações por E-mail via SMTP.

Compatível com:
- PythonAnywhere (https://aen.pythonanywhere.com)
- GitHub Pages (https://fazhoje.com/aentech)
- Ambientes de desenvolvimento local (http://localhost:5000)
"""

import os
import json
import smtplib
import time
import hashlib
import hmac
from datetime import datetime
from functools import wraps
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header

import jwt
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, send_from_directory, abort
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

# Carrega variáveis de ambiente do .env se existir
load_dotenv()

# ========================
# INICIALIZAÇÃO DA APLICAÇÃO
# ========================
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Carrega variáveis de ambiente do .env explicitamente pelo caminho absoluto
load_dotenv(os.path.join(BASE_DIR, ".env"))
load_dotenv()

app = Flask(
    __name__,
    static_folder=os.path.join(BASE_DIR, "static"),
    template_folder=BASE_DIR
)

# Chave secreta da aplicação (sessões e assinatura JWT)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "aentech-chave-secreta-2026")

# Configuração do banco de dados (SQLite por padrão; suporta PostgreSQL via DATABASE_URL)
db_uri = os.environ.get("DATABASE_URL")
if not db_uri:
    db_uri = "sqlite:///" + os.path.join(BASE_DIR, "aentech.db")
elif db_uri.startswith("postgres://"):
    db_uri = db_uri.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Habilita CORS com cabeçalhos autorizados para requisições cross-origin do GitHub Pages e localhost
CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
)

db = SQLAlchemy(app)


# ========================
# MODELOS DE BANCO DE DADOS (SQLALCHEMY)
# ========================
class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    admin = db.Column(db.Boolean, default=False, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

    def set_senha(self, senha):
        """Calcula o hash seguro da senha combinada com o username."""
        self.senha_hash = hashlib.sha256((self.username + senha).encode()).hexdigest()

    def verifica_senha(self, senha):
        """Verifica se a senha informada corresponde ao hash cadastrado."""
        if not senha:
            return False

        # 1. Validação direta com a senha do .env para contas de administrador (evita dessincronização)
        env_pass = (os.environ.get("ADMIN_PASSWORD") or "").strip()
        if self.admin and env_pass and (senha == env_pass or hmac.compare_digest(senha, env_pass)):
            return True

        if not self.senha_hash:
            return False

        # 2. Hash SHA-256 com username (padrão: username + senha)
        hash_com_user = hashlib.sha256((self.username + senha).encode()).hexdigest()
        if hmac.compare_digest(hash_com_user, self.senha_hash):
            return True

        # 3. Hash SHA-256 com username em minúsculo
        hash_com_user_lower = hashlib.sha256((self.username.lower() + senha).encode()).hexdigest()
        if hmac.compare_digest(hash_com_user_lower, self.senha_hash):
            return True

        # 4. Hash SHA-256 direto da senha
        hash_puro = hashlib.sha256(senha.encode()).hexdigest()
        if hmac.compare_digest(hash_puro, self.senha_hash):
            return True

        # 5. Compatibilidade com werkzeug se aplicável
        try:
            from werkzeug.security import check_password_hash
            if check_password_hash(self.senha_hash, senha):
                return True
        except Exception:
            pass

        # 6. Comparação direta se a senha foi salva em texto puro
        if hmac.compare_digest(senha, self.senha_hash):
            return True

        return False

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "admin": self.admin,
            "data_criacao": self.data_criacao.strftime("%d/%m/%Y %H:%M") if self.data_criacao else None,
        }


class OrdemServico(db.Model):
    __tablename__ = "ordens_servico"

    id = db.Column(db.Integer, primary_key=True)
    os_numero = db.Column(db.String(50), unique=True, nullable=False, index=True)
    data = db.Column(db.String(20), nullable=True)
    tecnico = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(50), default="Pendente", index=True)
    valor = db.Column(db.String(50), nullable=True, default="0,00")

    # Dados do Cliente
    cliente_nome = db.Column(db.String(150), nullable=False)
    cliente_telefone = db.Column(db.String(50), nullable=False)
    cliente_endereco = db.Column(db.String(200), nullable=True)
    cliente_email = db.Column(db.String(150), nullable=True)
    cliente_bairro_cidade = db.Column(db.String(150), nullable=True)
    cliente_cep = db.Column(db.String(20), nullable=True)

    # Equipamento
    marca = db.Column(db.String(50), nullable=True)
    modelo = db.Column(db.String(100), nullable=True)
    cor = db.Column(db.String(50), nullable=True)
    imei1 = db.Column(db.String(50), nullable=True)
    imei2 = db.Column(db.String(50), nullable=True)
    numero_serie = db.Column(db.String(50), nullable=True)
    bateria = db.Column(db.String(50), nullable=True)
    acessorios = db.Column(db.String(200), nullable=True)
    senha_padrao = db.Column(db.String(100), nullable=True)

    # Descrição do Problema e Laudo
    problemas = db.Column(db.Text, nullable=True)  # JSON lista de checkboxes
    problemas_adicionais = db.Column(db.Text, nullable=True)
    laudo_tecnico = db.Column(db.Text, nullable=True)

    # Notificação SMTP
    email_notificado = db.Column(db.Boolean, default=False)
    email_notificado_em = db.Column(db.DateTime, nullable=True)

    # Timestamps
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_problemas_list(self):
        if not self.problemas:
            return []
        try:
            val = json.loads(self.problemas)
            return val if isinstance(val, list) else [str(val)]
        except Exception:
            return [p.strip() for p in self.problemas.split(",") if p.strip()]

    def to_dict(self):
        """Retorna todos os campos (para técnicos autenticados)."""
        return {
            "id": self.id,
            "os_numero": self.os_numero,
            "data": self.data,
            "tecnico": self.tecnico,
            "status": self.status,
            "valor": self.valor,
            "cliente_nome": self.cliente_nome,
            "cliente_telefone": self.cliente_telefone,
            "cliente_endereco": self.cliente_endereco,
            "cliente_email": self.cliente_email,
            "cliente_bairro_cidade": self.cliente_bairro_cidade,
            "cliente_cep": self.cliente_cep,
            "marca": self.marca,
            "modelo": self.modelo,
            "cor": self.cor,
            "imei1": self.imei1,
            "imei2": self.imei2,
            "numero_serie": self.numero_serie,
            "bateria": self.bateria,
            "acessorios": self.acessorios,
            "senha_padrao": self.senha_padrao,
            "problemas": self.get_problemas_list(),
            "problemas_adicionais": self.problemas_adicionais,
            "laudo_tecnico": self.laudo_tecnico,
            "email_notificado": self.email_notificado,
            "email_notificado_em": self.email_notificado_em.strftime("%d/%m/%Y %H:%M") if self.email_notificado_em else None,
            "criado_em": self.criado_em.strftime("%d/%m/%Y %H:%M") if self.criado_em else None,
            "atualizado_em": self.atualizado_em.strftime("%d/%m/%Y %H:%M") if self.atualizado_em else None,
        }

    def to_public_dict(self):
        """Campos seguros para consulta pública pelo cliente (não expõe senhas ou contatos sensíveis)."""
        return {
            "id": self.id,
            "os_numero": self.os_numero,
            "data": self.data,
            "tecnico": self.tecnico,
            "status": self.status,
            "valor": self.valor,
            "cliente_nome": self.cliente_nome,
            "marca": self.marca,
            "modelo": self.modelo,
            "cor": self.cor,
            "imei1": self.imei1,
            "problemas": self.get_problemas_list(),
            "problemas_adicionais": self.problemas_adicionais,
            "laudo_tecnico": self.laudo_tecnico,
        }


# ========================
# AUTENTICAÇÃO JWT (HS256 via PyJWT)
# ========================
JWT_EXPIRES_SECONDS = int(os.environ.get("JWT_EXPIRES_SECONDS", "86400"))
JWT_ALGORITHM = "HS256"


def gerar_jwt(usuario, expires_in=None):
    """Gera um token JWT assinado (HS256) para o usuário autenticado."""
    if expires_in is None:
        expires_in = JWT_EXPIRES_SECONDS
    now = int(time.time())
    payload = {
        "sub": str(usuario.id),
        "username": usuario.username,
        "admin": bool(usuario.admin),
        "iat": now,
        "exp": now + int(expires_in),
    }
    token = jwt.encode(payload, app.config["SECRET_KEY"], algorithm=JWT_ALGORITHM)
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token


def verificar_jwt(token):
    """Valida a assinatura e a expiração do JWT e retorna (payload, erro)."""
    try:
        payload = jwt.decode(
            token or "",
            app.config["SECRET_KEY"],
            algorithms=[JWT_ALGORITHM],
            options={"require": ["sub", "exp", "iat"]},
        )
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, "Token expirado. Por favor, faça login novamente."
    except jwt.InvalidTokenError:
        return None, "Token inválido."


def _extrair_bearer_token():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:].strip()
    return None


def login_obrigatorio(f):
    """Decorator que exige token JWT assinado válido na requisição."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method == "OPTIONS":
            return f(*args, **kwargs)
        token = _extrair_bearer_token()
        if not token:
            return jsonify({"ok": False, "erro": "Token de autenticação necessário."}), 401
        payload, err = verificar_jwt(token)
        if err:
            return jsonify({"ok": False, "erro": err}), 401
        try:
            usuario_id = int(payload.get("sub"))
        except Exception:
            return jsonify({"ok": False, "erro": "Token inválido."}), 401
        usuario = Usuario.query.get(usuario_id)
        if not usuario or usuario.username != payload.get("username"):
            return jsonify({"ok": False, "erro": "Usuário não encontrado ou inativo."}), 401
        request.usuario = usuario
        request.jwt_payload = payload
        return f(*args, **kwargs)
    return decorated


def admin_obrigatorio(f):
    """Decorator que exige login ativo com privilégios de administrador."""
    @wraps(f)
    @login_obrigatorio
    def decorated(*args, **kwargs):
        if request.method == "OPTIONS":
            return f(*args, **kwargs)
        if not getattr(request, "usuario", None) or not request.usuario.admin:
            return jsonify({"ok": False, "erro": "Acesso restrito a administradores."}), 403
        return f(*args, **kwargs)
    return decorated


# ========================
# BOOTSTRAP DO BANCO DE DADOS
# ========================
with app.app_context():
    db.create_all()
    try:
        from sqlalchemy import func
        admin_user = (os.environ.get("ADMIN_USERNAME") or "ajpneto").strip()
        admin_pass = (os.environ.get("ADMIN_PASSWORD") or "admin123").strip()
        admin_email = (os.environ.get("ADMIN_EMAIL") or "ajpneto@fazhoje.com").strip()

        # Cria ou sincroniza o usuário administrador definido no .env
        if admin_user and admin_pass:
            u = Usuario.query.filter(func.lower(Usuario.username) == admin_user.lower()).first()
            if not u:
                u = Usuario(username=admin_user, email=admin_email, admin=True)
                u.set_senha(admin_pass)
                db.session.add(u)
                db.session.commit()
                print(f"[AUTH] Usuário admin criado com sucesso: {admin_user}")
            elif not u.verifica_senha(admin_pass):
                u.set_senha(admin_pass)
                db.session.commit()
                print(f"[AUTH] Senha do admin sincronizada com .env: {admin_user}")

            # Garante também a existência do usuário 'admin' para conveniência
            if admin_user.lower() != "admin":
                u_alias = Usuario.query.filter(func.lower(Usuario.username) == "admin").first()
                if not u_alias:
                    u_alias = Usuario(username="admin", email="admin@fazhoje.com", admin=True)
                    u_alias.set_senha(admin_pass)
                    db.session.add(u_alias)
                    db.session.commit()
                    print("[AUTH] Usuário alias 'admin' criado para conveniência.")
                elif not u_alias.verifica_senha(admin_pass):
                    u_alias.set_senha(admin_pass)
                    db.session.commit()
    except Exception as e:
        print(f"[AUTH] Falha no bootstrap de admin: {e}")


# ========================
# CONFIGURAÇÕES DO NEGÓCIO
# ========================
WHATSAPP_NUMBER = os.environ.get("WHATSAPP_NUMBER", "5541984512660").strip()
WHATSAPP_DISPLAY = os.environ.get("WHATSAPP_DISPLAY", "(41) 98451-2660").strip()
WHATSAPP_LINK = os.environ.get("WHATSAPP_LINK", f"https://wa.me/{WHATSAPP_NUMBER}").strip()

EMPRESA = {
    "nome": os.environ.get("BUSINESS_NAME", "AENTECH").strip(),
    "slogan": os.environ.get("BUSINESS_SLOGAN", "Assistência Técnica Especializada em Celulares e Tablets").strip(),
    "cidade": os.environ.get("BUSINESS_CITY", "Ourinhos - SP").strip(),
    "endereco": os.environ.get("BUSINESS_ADDRESS", "Rua João Rafael, Nº 383, Jardim Industrial, Ourinhos - SP").strip(),
    "email": os.environ.get("BUSINESS_EMAIL", "contato@fazhoje.com").strip(),
    "telefone": os.environ.get("BUSINESS_PHONE", "(41) 98451-2660").strip(),
    "whatsapp": WHATSAPP_NUMBER,
    "whatsapp_display": WHATSAPP_DISPLAY,
    "whatsapp_link": WHATSAPP_LINK,
    "horario": os.environ.get("BUSINESS_HORARIO", "Seg a Sáb — 09h às 19h").strip(),
    "garantia_dias": int(os.environ.get("BUSINESS_GARANTIA_DIAS", 90)),
}

SERVICOS = [
    {
        "icone": "fa-mobile-screen-button",
        "icon": "fa-mobile-screen-button",
        "titulo": "Troca de Tela",
        "descricao": "Substituição de displays com peças de qualidade e teste completo de touch.",
        "msg_whats": f"Olá {EMPRESA['nome']}! Preciso de orçamento para troca de tela.",
    },
    {
        "icone": "fa-battery-full",
        "icon": "fa-battery-full",
        "titulo": "Troca de Bateria",
        "descricao": "Troca de bateria para recuperar autonomia e segurança do aparelho.",
        "msg_whats": f"Olá {EMPRESA['nome']}! Preciso de orçamento para troca de bateria.",
    },
    {
        "icone": "fa-plug-circle-bolt",
        "icon": "fa-plug",
        "titulo": "Conector de Carga",
        "descricao": "Reparo/substituição do conector USB/Lightning e testes de carregamento.",
        "msg_whats": f"Olá {EMPRESA['nome']}! Meu celular não está carregando direito.",
    },
    {
        "icone": "fa-droplet",
        "icon": "fa-droplet",
        "titulo": "Desoxidação / Banho Químico",
        "descricao": "Atendimento emergencial para aparelhos que tiveram contato com líquidos.",
        "msg_whats": f"Olá {EMPRESA['nome']}! Meu aparelho teve contato com líquido.",
    },
    {
        "icone": "fa-microchip",
        "icon": "fa-microchip",
        "titulo": "Reparo em Placa",
        "descricao": "Diagnóstico e reparos eletrônicos avançados em microcomponentes.",
        "msg_whats": f"Olá {EMPRESA['nome']}! Preciso de diagnóstico/reparo em placa.",
    },
    {
        "icone": "fa-laptop-code",
        "icon": "fa-unlock",
        "titulo": "Software e Desbloqueio",
        "descricao": "Restauração de sistema, remoção de vírus, backup e desbloqueios conforme avaliação.",
        "msg_whats": f"Olá {EMPRESA['nome']}! Preciso de manutenção de software no meu celular.",
    },
]

PASSOS = [
    {
        "numero": "01",
        "icone": "fa-clipboard-list",
        "titulo": "Ordem de Serviço (OS)",
        "descricao": "Registramos os dados do cliente, identificação do aparelho (marca, modelo e IMEI) e checklist completo de defeitos.",
    },
    {
        "numero": "02",
        "icone": "fa-magnifying-glass-chart",
        "titulo": "Orçamento e Diagnóstico",
        "descricao": "O técnico testa os componentes e define o valor do conserto e o prazo de entrega antes de iniciar o reparo. Sem surpresas!",
    },
    {
        "numero": "03",
        "icone": "fa-circle-check",
        "titulo": "Execução e Garantia",
        "descricao": f"Após a aprovação, realizamos o reparo com peças de qualidade e entregamos com {EMPRESA['garantia_dias']} dias de garantia por escrito.",
    },
]

DEPOIMENTOS = [
    {
        "nome": "Mariana Silva",
        "texto": "Levei meu iPhone com a tela trincada e em pouco tempo estava pronto. Atendimento excelente e preço justo!",
        "nota": 5,
        "estrelas": 5,
    },
    {
        "nome": "Carlos Eduardo",
        "texto": "Meu aparelho tinha parado de carregar. Diagnóstico rápido e conserto no mesmo dia. Recomendo demais!",
        "nota": 5,
        "estrelas": 5,
    },
    {
        "nome": "Juliana Prado",
        "texto": "Meu celular caiu na água e achei que tinha perdido. A AENTECH desoxidou e recuperou o aparelho com tudo salvo!",
        "nota": 5,
        "estrelas": 5,
    },
]

FAQ = [
    {
        "pergunta": "Quanto tempo demora o conserto?",
        "resposta": "A maioria dos reparos comuns (tela, bateria, conector de carga) é concluída rapidamente. Reparos em placa podem levar de 24h a 72h conforme disponibilidade de peças.",
    },
    {
        "pergunta": "Vocês dão garantia?",
        "resposta": f"Sim! Todos os serviços contam com {EMPRESA['garantia_dias']} dias de garantia por escrito cobrindo peças e mão de obra.",
    },
    {
        "pergunta": "Como posso acompanhar minha Ordem de Serviço?",
        "resposta": "Você pode consultar em tempo real na página 'Consultar OS' informando o número da OS ou seu telefone.",
    },
    {
        "pergunta": "Quais marcas vocês atendem?",
        "resposta": "Atendemos Apple, Samsung, Xiaomi, Motorola, Realme, LG, Asus e outras.",
    },
]

MARCAS = ["Apple", "Samsung", "Xiaomi", "Motorola", "Realme", "LG", "Asus", "Nokia"]


@app.context_processor
def inject_globals():
    return {
        "empresa": EMPRESA,
        "servicos": SERVICOS,
        "passos": PASSOS,
        "depoimentos": DEPOIMENTOS,
        "faq": FAQ,
        "marcas": MARCAS,
        "whatsapp_link": WHATSAPP_LINK,
        "whatsapp_number": WHATSAPP_NUMBER,
        "ano_atual": datetime.now().year,
    }


# ========================
# FUNÇÕES AUXILIARES (OS & SMTP)
# ========================
def gerar_proximo_numero_os():
    """Gera número sequencial único para a OS, ex: OS-2026-0001."""
    ano = datetime.now().year
    prefixo = f"OS-{ano}-"
    ultima = OrdemServico.query.filter(OrdemServico.os_numero.like(f"{prefixo}%")).order_by(OrdemServico.id.desc()).first()
    if ultima and ultima.os_numero:
        try:
            seq = int(ultima.os_numero.split("-")[-1]) + 1
        except Exception:
            seq = OrdemServico.query.count() + 1
    else:
        seq = 1
    return f"{prefixo}{seq:04d}"


def enviar_email_orcamento_aprovado(os_obj):
    """
    Envia e-mail de notificação SMTP para o cliente com detalhes do orçamento aprovado.
    Lida graciosamente com ausência de credenciais em ambiente de desenvolvimento (simulação com log).
    """
    destinatario = os_obj.cliente_email
    if not destinatario or "@" not in destinatario:
        return False, "Cliente não possui e-mail cadastrado ou o e-mail é inválido."

    mail_enabled = (os.environ.get("MAIL_ENABLED") or "True").lower() in ("true", "1", "t", "yes")
    if not mail_enabled:
        return False, "Envio de e-mail desativado nas configurações (MAIL_ENABLED=False)."

    smtp_server = os.environ.get("MAIL_SERVER") or os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("MAIL_PORT") or os.environ.get("SMTP_PORT", 587))
    smtp_user = os.environ.get("MAIL_USERNAME") or os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("MAIL_PASSWORD") or os.environ.get("SMTP_PASSWORD", "")
    smtp_sender = os.environ.get("MAIL_DEFAULT_SENDER") or os.environ.get(
        "SMTP_SENDER", f"{EMPRESA['nome']} Assistência Técnica <{smtp_user or 'contato@fazhoje.com'}>"
    )
    use_tls = (os.environ.get("MAIL_USE_TLS") or os.environ.get("SMTP_USE_TLS", "True")).lower() in ("true", "1", "t", "yes")

    assunto = f"{EMPRESA['nome']} — Orçamento Aprovado para Ordem de Serviço #{os_obj.os_numero}"

    problemas_lista = os_obj.get_problemas_list()
    problemas_str = ", ".join(problemas_lista) if problemas_lista else "Revisão geral e diagnóstico"
    if os_obj.problemas_adicionais:
        problemas_str += f" (Obs: {os_obj.problemas_adicionais})"

    valor_display = os_obj.valor or "0,00"
    if not valor_display.startswith("R$"):
        valor_display = f"R$ {valor_display}"

    # Template HTML responsivo do e-mail
    html_body = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f8; margin: 0; padding: 20px; }}
            .email-container {{ max-width: 620px; margin: 0 auto; background: #ffffff; border-radius: 8px; overflow: hidden; border: 1px solid #dcdfe6; box-shadow: 0 4px 12px rgba(0,0,0,0.06); }}
            .header {{ background-color: #1a202c; color: #ffffff; padding: 25px; text-align: center; border-bottom: 4px solid #dc3545; }}
            .header h1 {{ margin: 0; font-size: 24px; letter-spacing: 1px; color: #ffffff; }}
            .header p {{ margin: 5px 0 0; font-size: 13px; color: #a0aec0; }}
            .badge-status {{ display: inline-block; background-color: #198754; color: #ffffff; padding: 6px 16px; border-radius: 20px; font-weight: bold; font-size: 13px; margin-top: 15px; }}
            .content {{ padding: 25px; color: #2d3748; line-height: 1.6; font-size: 14px; }}
            .info-card {{ background-color: #f7fafc; border-left: 4px solid #198754; border-radius: 4px; padding: 15px; margin: 20px 0; }}
            .info-row {{ display: flex; justify-content: space-between; margin-bottom: 8px; border-bottom: 1px dashed #e2e8f0; padding-bottom: 4px; }}
            .info-row:last-child {{ border-bottom: none; margin-bottom: 0; }}
            .label {{ font-weight: 600; color: #4a5568; }}
            .val {{ font-weight: 700; color: #1a202c; text-align: right; }}
            .price {{ font-size: 18px; color: #198754; font-weight: 800; }}
            .btn-whats {{ display: inline-block; background-color: #25d366; color: #ffffff; text-decoration: none; padding: 12px 24px; border-radius: 6px; font-weight: bold; font-size: 14px; margin-top: 15px; text-align: center; }}
            .footer {{ background-color: #edf2f7; padding: 20px; text-align: center; font-size: 12px; color: #718096; border-top: 1px solid #e2e8f0; }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <h1>{EMPRESA['nome']}</h1>
                <p>{EMPRESA['slogan']}</p>
                <div class="badge-status">ORÇAMENTO APROVADO</div>
            </div>
            <div class="content">
                <p>Olá, <strong>{os_obj.cliente_nome}</strong>!</p>
                <p>Confirmamos a <strong>aprovação do orçamento</strong> da sua <strong>Ordem de Serviço #{os_obj.os_numero}</strong>. Nosso corpo técnico já iniciou a execução do serviço com total cuidado e agilidade.</p>

                <div class="info-card">
                    <div class="info-row">
                        <span class="label">Nº da Ordem:</span>
                        <span class="val">{os_obj.os_numero}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">Aparelho:</span>
                        <span class="val">{os_obj.marca or ''} {os_obj.modelo or 'Não informado'}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">Cor:</span>
                        <span class="val">{os_obj.cor or '-'}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">IMEI 1:</span>
                        <span class="val">{os_obj.imei1 or '-'}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">Serviço/Defeito:</span>
                        <span class="val">{problemas_str}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">Técnico Responsável:</span>
                        <span class="val">{os_obj.tecnico or 'Corpo Técnico AENTECH'}</span>
                    </div>
                    <div class="info-row" style="margin-top: 8px;">
                        <span class="label" style="font-size: 16px;">Valor Aprovado:</span>
                        <span class="val price">{valor_display}</span>
                    </div>
                </div>

                <p>🛡 <strong>Garantia por escrito de {EMPRESA['garantia_dias']} dias:</strong> Garantimos a qualidade das peças e da mão de obra empregadas no reparo do seu aparelho.</p>
                <p>Você será notificado imediatamente assim que o reparo for concluído para realizar a retirada.</p>

                <div style="text-align: center; margin: 25px 0;">
                    <a href="https://wa.me/{WHATSAPP_NUMBER}?text=Ol%C3%A1%20{EMPRESA['nome']}!%20Gostaria%20de%20informa%C3%A7%C3%B5es%20sobre%20a%20OS%20{os_obj.os_numero}" class="btn-whats">
                        Falar no WhatsApp da {EMPRESA['nome']}
                    </a>
                </div>
            </div>
            <div class="footer">
                <strong>{EMPRESA['nome']} — {EMPRESA['slogan']}</strong><br>
                {EMPRESA['endereco']}<br>
                WhatsApp: {EMPRESA['telefone']} | E-mail: {EMPRESA['email']}<br>
                Horário de Atendimento: {EMPRESA['horario']}
            </div>
        </div>
    </body>
    </html>
    """

    text_body = f"""
    {EMPRESA['nome']} — Orçamento Aprovado para Ordem de Serviço #{os_obj.os_numero}

    Olá, {os_obj.cliente_nome}!
    O orçamento para o seu aparelho ({os_obj.marca} {os_obj.modelo}) foi APROVADO.
    Valor Aprovado: {valor_display}
    Defeitos/Serviços: {problemas_str}
    Técnico Responsável: {os_obj.tecnico or 'Corpo Técnico AENTECH'}
    Garantia: {EMPRESA['garantia_dias']} dias por escrito.

    Assim que o reparo for concluído, entraremos em contato para retirada.
    WhatsApp: {EMPRESA['telefone']}
    Endereço: {EMPRESA['endereco']}
    """

    # Modo simulação se credenciais não estiverem fornecidas
    if not smtp_user or not smtp_pass:
        print(f"[SMTP SIMULADO] Notificação registrada para {destinatario} | OS #{os_obj.os_numero}")
        os_obj.email_notificado = True
        os_obj.email_notificado_em = datetime.utcnow()
        db.session.commit()
        return True, "E-mail de orçamento aprovado registrado com sucesso! (Modo simulação: configure MAIL_USERNAME e MAIL_PASSWORD no .env para envio SMTP real)."

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = Header(assunto, "utf-8")
        msg["From"] = smtp_sender
        msg["To"] = destinatario
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=12)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=12)
            if use_tls:
                server.starttls()

        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_sender, [destinatario], msg.as_string())
        server.quit()

        os_obj.email_notificado = True
        os_obj.email_notificado_em = datetime.utcnow()
        db.session.commit()
        return True, f"E-mail de aprovação enviado com sucesso para {destinatario}!"
    except Exception as e:
        print(f"[ERRO SMTP] Falha ao enviar e-mail: {str(e)}")
        return False, f"Falha no envio do e-mail SMTP: {str(e)}"


# ========================
# ROTAS DE AUTENTICAÇÃO
# ========================
@app.route("/api/login", methods=["POST"])
def api_login():
    """Autenticação de administrador / técnico. Retorna token JWT."""
    data = request.get_json() or request.form.to_dict()
    if not data:
        return jsonify({"ok": False, "erro": "Dados de login não fornecidos."}), 400

    username = (data.get("username") or "").strip()
    senha = (data.get("senha") or "").strip()

    if not username or not senha:
        return jsonify({"ok": False, "erro": "Usuário e senha são obrigatórios."}), 400

    # Busca por username OU email (case-insensitive)
    from sqlalchemy import func
    usuario = Usuario.query.filter(
        db.or_(
            func.lower(Usuario.username) == username.lower(),
            func.lower(Usuario.email) == username.lower()
        )
    ).first()

    # Fallback inteligente: se digitou 'admin' e não achou usuário específico, vincula ao primeiro admin
    if not usuario and username.lower() in ("admin", "administrador"):
        usuario = Usuario.query.filter_by(admin=True).first()

    if not usuario or not usuario.verifica_senha(senha):
        return jsonify({"ok": False, "erro": "Usuário ou senha incorretos."}), 401

    token = gerar_jwt(usuario)

    return jsonify({
        "ok": True,
        "msg": "Login realizado com sucesso!",
        "token": token,
        "usuario": usuario.to_dict(),
    })


@app.route("/api/logout", methods=["POST"])
def api_logout():
    """Encerra a sessão no cliente (invalida localmente)."""
    return jsonify({"ok": True, "msg": "Logout realizado com sucesso."})


@app.route("/api/me", methods=["GET"])
@login_obrigatorio
def api_me():
    """Retorna dados do usuário atualmente autenticado."""
    return jsonify({
        "ok": True,
        "usuario": request.usuario.to_dict(),
    })


@app.route("/api/usuarios", methods=["GET"])
@admin_obrigatorio
def api_listar_usuarios():
    """Lista todos os usuários cadastrados (apenas administradores)."""
    usuarios = Usuario.query.order_by(Usuario.id.asc()).all()
    return jsonify({
        "ok": True,
        "total": len(usuarios),
        "usuarios": [u.to_dict() for u in usuarios],
    })


@app.route("/api/usuarios", methods=["POST"])
@admin_obrigatorio
def api_criar_usuario():
    """Cria novo usuário (apenas administradores)."""
    data = request.get_json() or request.form.to_dict()
    if not data:
        return jsonify({"ok": False, "erro": "Dados não fornecidos."}), 400

    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    senha = data.get("senha", "").strip()
    is_admin = bool(data.get("admin", False))

    if not username or not email or not senha:
        return jsonify({"ok": False, "erro": "Usuário, e-mail e senha são obrigatórios."}), 400

    if Usuario.query.filter_by(username=username).first():
        return jsonify({"ok": False, "erro": f"Usuário '{username}' já existe."}), 400

    if Usuario.query.filter_by(email=email).first():
        return jsonify({"ok": False, "erro": f"E-mail '{email}' já está em uso."}), 400

    novo_usuario = Usuario(username=username, email=email, admin=is_admin)
    novo_usuario.set_senha(senha)

    db.session.add(novo_usuario)
    db.session.commit()

    return jsonify({
        "ok": True,
        "msg": "Usuário criado com sucesso!",
        "usuario": novo_usuario.to_dict(),
    }), 201


@app.route("/api/usuarios/<int:id>", methods=["DELETE"])
@admin_obrigatorio
def api_excluir_usuario(id):
    """Exclui usuário cadastrado (apenas administradores)."""
    if request.usuario.id == id:
        return jsonify({"ok": False, "erro": "Você não pode excluir sua própria conta conectada."}), 400

    usuario = Usuario.query.get(id)
    if not usuario:
        return jsonify({"ok": False, "erro": "Usuário não encontrado."}), 404

    username = usuario.username
    db.session.delete(usuario)
    db.session.commit()
    return jsonify({"ok": True, "msg": f"Usuário '{username}' excluído com sucesso."})


# ========================
# RESTFUL API — ORDENS DE SERVIÇO & CONSULTAS
# ========================
@app.route("/api/config", methods=["GET"])
def api_config():
    """Retorna dados de configuração pública da empresa e status da API."""
    mail_user = os.environ.get("MAIL_USERNAME") or os.environ.get("SMTP_USER")
    mail_pass = os.environ.get("MAIL_PASSWORD") or os.environ.get("SMTP_PASSWORD")
    return jsonify({
        "ok": True,
        "empresa": EMPRESA,
        "smtp_configurado": bool(mail_user and mail_pass),
        "versao": "2.1.0",
    })


@app.route("/api/consulta", methods=["GET"])
def api_consulta_publica():
    """Consulta pública e segura por número da OS, ID ou telefone do cliente."""
    id_param = (request.args.get("id") or "").strip()
    termo = (request.args.get("os") or request.args.get("termo") or request.args.get("busca") or "").strip()
    os_obj = None

    if id_param.isdigit():
        os_obj = OrdemServico.query.get(int(id_param))

    if not os_obj and termo:
        if termo.upper().startswith("OS-"):
            os_obj = OrdemServico.query.filter_by(os_numero=termo.strip()).first()
        if not os_obj:
            t = f"%{termo}%"
            os_obj = OrdemServico.query.filter(
                db.or_(OrdemServico.os_numero.ilike(t), OrdemServico.cliente_telefone.ilike(t))
            ).order_by(OrdemServico.id.desc()).first()

    if not os_obj and not id_param and not termo:
        return jsonify({"ok": False, "erro": "Informe o número da OS ou telefone para consulta."}), 400

    if not os_obj:
        return jsonify({"ok": False, "erro": "Ordem de Serviço não encontrada."}), 404

    return jsonify({"ok": True, "ordem": os_obj.to_public_dict()})


@app.route("/api/stats", methods=["GET"])
@login_obrigatorio
def api_stats():
    """Retorna métricas em tempo real para o painel administrativo."""
    total = OrdemServico.query.count()
    pendentes = OrdemServico.query.filter(OrdemServico.status.in_(["Pendente", "Recebido"])).count()
    diagnostico = OrdemServico.query.filter_by(status="Em Diagnóstico").count()
    aguardando = OrdemServico.query.filter_by(status="Aguardando Aprovação").count()
    aprovados = OrdemServico.query.filter(OrdemServico.status.in_(["Orçamento Aprovado", "Aprovado"])).count()
    reparo = OrdemServico.query.filter_by(status="Em Reparo").count()
    concluidos = OrdemServico.query.filter(OrdemServico.status.in_(["Concluído", "Entregue"])).count()
    cancelados = OrdemServico.query.filter_by(status="Cancelado").count()

    todas = OrdemServico.query.filter(
        OrdemServico.status.in_(["Orçamento Aprovado", "Aprovado", "Em Reparo", "Concluído", "Entregue"])
    ).all()
    faturamento = 0.0
    for item in todas:
        try:
            val_limpo = item.valor.replace("R$", "").replace(".", "").replace(",", ".").strip()
            faturamento += float(val_limpo)
        except Exception:
            pass

    return jsonify({
        "ok": True,
        "total": total,
        "pendentes": pendentes,
        "diagnostico": diagnostico,
        "aguardando_aprovacao": aguardando,
        "aprovados": aprovados,
        "em_reparo": reparo,
        "concluidos": concluidos,
        "cancelados": cancelados,
        "faturamento_estimado": f"{faturamento:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
    })


@app.route("/api/os", methods=["GET"])
@login_obrigatorio
def api_listar_os():
    """Lista Ordens de Serviço completas com filtros de status e busca textual."""
    status_filter = request.args.get("status", "").strip()
    busca = request.args.get("busca", "").strip()

    query = OrdemServico.query

    if status_filter:
        if status_filter == "Aprovado":
            query = query.filter(OrdemServico.status.in_(["Orçamento Aprovado", "Aprovado"]))
        else:
            query = query.filter_by(status=status_filter)

    if busca:
        termo = f"%{busca}%"
        query = query.filter(
            db.or_(
                OrdemServico.os_numero.ilike(termo),
                OrdemServico.cliente_nome.ilike(termo),
                OrdemServico.cliente_telefone.ilike(termo),
                OrdemServico.modelo.ilike(termo),
                OrdemServico.marca.ilike(termo),
                OrdemServico.imei1.ilike(termo),
            )
        )

    ordens = query.order_by(OrdemServico.id.desc()).all()
    return jsonify({
        "ok": True,
        "total": len(ordens),
        "ordens": [o.to_dict() for o in ordens],
    })


@app.route("/api/os", methods=["POST"])
@login_obrigatorio
def api_criar_os():
    """Cria uma nova Ordem de Serviço."""
    data = request.get_json() or request.form.to_dict()
    if not data:
        return jsonify({"ok": False, "erro": "Dados da requisição vazios."}), 400

    cliente_nome = data.get("cliente_nome", "").strip()
    cliente_telefone = data.get("cliente_telefone", "").strip()

    if not cliente_nome:
        return jsonify({"ok": False, "erro": "O nome do cliente é obrigatório."}), 400

    # Determina o número da OS sequencial
    os_numero = data.get("os_numero", "").strip()
    if not os_numero:
        os_numero = gerar_proximo_numero_os()
    else:
        existe = OrdemServico.query.filter_by(os_numero=os_numero).first()
        if existe:
            os_numero = gerar_proximo_numero_os()

    # Data de entrada
    data_os = data.get("data", "").strip()
    if not data_os:
        data_os = datetime.now().strftime("%d/%m/%Y")

    # Tratamento da lista de defeitos/checklist
    raw_problemas = data.get("problemas", [])
    if isinstance(raw_problemas, list):
        problemas_json = json.dumps(raw_problemas)
    else:
        problemas_json = json.dumps([str(raw_problemas)]) if raw_problemas else "[]"

    nova_os = OrdemServico(
        os_numero=os_numero,
        data=data_os,
        tecnico=data.get("tecnico", "").strip(),
        status=data.get("status", "Pendente").strip() or "Pendente",
        valor=data.get("valor", "0,00").strip() or "0,00",
        cliente_nome=cliente_nome,
        cliente_telefone=cliente_telefone,
        cliente_endereco=data.get("cliente_endereco", "").strip(),
        cliente_email=data.get("cliente_email", "").strip(),
        cliente_bairro_cidade=data.get("cliente_bairro_cidade", "").strip(),
        cliente_cep=data.get("cliente_cep", "").strip(),
        marca=data.get("marca", "").strip(),
        modelo=data.get("modelo", "").strip(),
        cor=data.get("cor", "").strip(),
        imei1=data.get("imei1", "").strip(),
        imei2=data.get("imei2", "").strip(),
        numero_serie=data.get("numero_serie", "").strip(),
        bateria=data.get("bateria", "").strip(),
        acessorios=data.get("acessorios", "").strip(),
        senha_padrao=data.get("senha_padrao", "").strip(),
        problemas=problemas_json,
        problemas_adicionais=data.get("problemas_adicionais", "").strip(),
        laudo_tecnico=data.get("laudo_tecnico", "").strip(),
    )

    db.session.add(nova_os)
    db.session.commit()

    # Dispara e-mail se criada com status aprovado e notificação solicitada
    email_status = None
    if nova_os.status in ["Orçamento Aprovado", "Aprovado"] and data.get("notificar_email", False):
        _, email_status = enviar_email_orcamento_aprovado(nova_os)

    return jsonify({
        "ok": True,
        "msg": "Ordem de Serviço criada com sucesso!",
        "ordem": nova_os.to_dict(),
        "email_msg": email_status,
    }), 201


@app.route("/api/os/<int:id>", methods=["GET"])
@login_obrigatorio
def api_obter_os(id):
    """Busca os detalhes completos de uma OS pelo ID."""
    os_obj = OrdemServico.query.get(id)
    if not os_obj:
        return jsonify({"ok": False, "erro": "Ordem de Serviço não encontrada."}), 404
    return jsonify({"ok": True, "ordem": os_obj.to_dict()})


@app.route("/api/os/numero/<string:os_numero>", methods=["GET"])
@login_obrigatorio
def api_obter_os_por_numero(os_numero):
    """Busca os detalhes completos de uma OS pelo código (ex: OS-2026-0001)."""
    os_obj = OrdemServico.query.filter_by(os_numero=os_numero.strip()).first()
    if not os_obj:
        return jsonify({"ok": False, "erro": f"Ordem de Serviço {os_numero} não encontrada."}), 404
    return jsonify({"ok": True, "ordem": os_obj.to_dict()})


@app.route("/api/os/<int:id>", methods=["PUT", "PATCH"])
@login_obrigatorio
def api_atualizar_os(id):
    """Atualiza dados de uma OS existente."""
    os_obj = OrdemServico.query.get(id)
    if not os_obj:
        return jsonify({"ok": False, "erro": "Ordem de Serviço não encontrada."}), 404

    data = request.get_json() or request.form.to_dict()
    if not data:
        return jsonify({"ok": False, "erro": "Nenhum dado enviado para atualização."}), 400

    status_anterior = os_obj.status

    campos_texto = [
        "tecnico", "status", "valor", "cliente_nome", "cliente_telefone",
        "cliente_endereco", "cliente_email", "cliente_bairro_cidade",
        "cliente_cep", "marca", "modelo", "cor", "imei1", "imei2",
        "numero_serie", "bateria", "acessorios", "senha_padrao",
        "problemas_adicionais", "laudo_tecnico", "data"
    ]

    for campo in campos_texto:
        if campo in data:
            setattr(os_obj, campo, str(data[campo]).strip())

    if "problemas" in data:
        raw_prob = data["problemas"]
        if isinstance(raw_prob, list):
            os_obj.problemas = json.dumps(raw_prob)
        else:
            os_obj.problemas = json.dumps([str(raw_prob)]) if raw_prob else "[]"

    novo_status = os_obj.status
    db.session.commit()

    email_msg = None
    transicao_aprovado = (
        novo_status in ["Orçamento Aprovado", "Aprovado"] and
        status_anterior not in ["Orçamento Aprovado", "Aprovado"]
    )

    if transicao_aprovado or data.get("notificar_email", False):
        _, email_msg = enviar_email_orcamento_aprovado(os_obj)

    return jsonify({
        "ok": True,
        "msg": "Ordem de Serviço atualizada com sucesso!",
        "ordem": os_obj.to_dict(),
        "email_msg": email_msg,
    })


@app.route("/api/os/<int:id>/aprovar", methods=["POST"])
@login_obrigatorio
def api_aprovar_orcamento(id):
    """
    Ação expressa: Define o status como 'Orçamento Aprovado',
    atualiza o valor se fornecido e dispara a notificação SMTP por e-mail.
    """
    os_obj = OrdemServico.query.get(id)
    if not os_obj:
        return jsonify({"ok": False, "erro": "Ordem de Serviço não encontrada."}), 404

    data = request.get_json() or {}
    if "valor" in data and str(data["valor"]).strip():
        os_obj.valor = str(data["valor"]).strip()

    os_obj.status = "Orçamento Aprovado"
    db.session.commit()

    sucesso_email, msg_email = enviar_email_orcamento_aprovado(os_obj)

    return jsonify({
        "ok": True,
        "msg": "Orçamento aprovado com sucesso!",
        "email_enviado": sucesso_email,
        "email_msg": msg_email,
        "ordem": os_obj.to_dict(),
    })


@app.route("/api/os/<int:id>/notificar", methods=["POST"])
@login_obrigatorio
def api_reenviar_notificacao(id):
    """Reenvia notificação por e-mail para uma OS com orçamento aprovado."""
    os_obj = OrdemServico.query.get(id)
    if not os_obj:
        return jsonify({"ok": False, "erro": "Ordem de Serviço não encontrada."}), 404

    sucesso, msg = enviar_email_orcamento_aprovado(os_obj)
    return jsonify({
        "ok": sucesso,
        "msg": msg,
        "ordem": os_obj.to_dict(),
    })


@app.route("/api/os/<int:id>", methods=["DELETE"])
@login_obrigatorio
def api_excluir_os(id):
    """Exclui uma Ordem de Serviço."""
    os_obj = OrdemServico.query.get(id)
    if not os_obj:
        return jsonify({"ok": False, "erro": "Ordem de Serviço não encontrada."}), 404

    num = os_obj.os_numero
    db.session.delete(os_obj)
    db.session.commit()
    return jsonify({"ok": True, "msg": f"Ordem de Serviço {num} excluída com sucesso."})


# ========================
# ROTAS FRONTEND / TEMPLATES
# ========================
@app.route("/")
def index():
    """Renderiza a página institucional ou serve a interface configurada."""
    if os.path.exists(os.path.join(BASE_DIR, "templates", "index.html")):
        return render_template(
            "templates/index.html",
            empresa=EMPRESA,
            servicos=SERVICOS,
            passos=PASSOS,
            depoimentos=DEPOIMENTOS,
            faq=FAQ,
            marcas=MARCAS,
        )
    if os.path.exists(os.path.join(BASE_DIR, "index.html")):
        return send_from_directory(BASE_DIR, "index.html")
    return send_from_directory(BASE_DIR, "admin.html")


@app.route("/ordem-de-servico")
@app.route("/ordem-de-servico.html")
@app.route("/os")
def rota_ordem_servico():
    if os.path.exists(os.path.join(BASE_DIR, "ordem-de-servico.html")):
        return send_from_directory(BASE_DIR, "ordem-de-servico.html")
    fazhoje_path = os.path.abspath(os.path.join(BASE_DIR, "..", "fazhoje", "aentech"))
    if os.path.exists(os.path.join(fazhoje_path, "ordem-de-servico.html")):
        return send_from_directory(fazhoje_path, "ordem-de-servico.html")
    abort(404)


@app.route("/admin")
@app.route("/admin.html")
def rota_admin():
    if os.path.exists(os.path.join(BASE_DIR, "admin.html")):
        return send_from_directory(BASE_DIR, "admin.html")
    fazhoje_path = os.path.abspath(os.path.join(BASE_DIR, "..", "fazhoje", "aentech"))
    if os.path.exists(os.path.join(fazhoje_path, "admin.html")):
        return send_from_directory(fazhoje_path, "admin.html")
    abort(404)


@app.route("/consultar-os")
@app.route("/consultar-os.html")
def rota_consultar_os():
    if os.path.exists(os.path.join(BASE_DIR, "consultar-os.html")):
        return send_from_directory(BASE_DIR, "consultar-os.html")
    fazhoje_path = os.path.abspath(os.path.join(BASE_DIR, "..", "fazhoje", "aentech"))
    if os.path.exists(os.path.join(fazhoje_path, "consultar-os.html")):
        return send_from_directory(fazhoje_path, "consultar-os.html")
    abort(404)


@app.route("/contato", methods=["POST"])
def contato():
    """Recebe formulário de contato da página inicial."""
    data = request.get_json() or request.form.to_dict()
    nome = data.get("nome", "").strip()
    telefone = data.get("telefone", "").strip()
    mensagem = data.get("mensagem", "").strip()

    if not nome or not telefone:
        return jsonify({"ok": False, "erro": "Nome e telefone são obrigatórios."}), 400

    print(f"[NOVO CONTATO] {nome} | {telefone} | {mensagem}")
    return jsonify({"ok": True, "msg": "Recebemos sua mensagem! Em breve nossa equipe entrará em contato."})


# ========================
# TRATAMENTO DE ERROS
# ========================
@app.errorhandler(404)
def erro_404(e):
    if request.path.startswith("/api/"):
        return jsonify({"ok": False, "erro": "Recurso ou endpoint não encontrado."}), 404
    return ("Página não encontrada.", 404)


@app.errorhandler(500)
def erro_500(e):
    if request.path.startswith("/api/"):
        return jsonify({"ok": False, "erro": "Erro interno do servidor."}), 500
    return ("Erro interno do servidor.", 500)


if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 5000))
    debug_mode = (os.environ.get("FLASK_DEBUG") or "True").lower() in ("true", "1", "yes")
    app.run(debug=debug_mode, host="0.0.0.0", port=porta)
