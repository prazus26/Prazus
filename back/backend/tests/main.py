import sys
from pathlib import Path
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from flask import Flask,session, request, abort
import secrets
import hmac
from backend.controller.admin_controller import admin_bp
from backend.controller.index_controller import index_bp
from backend.controller.cadastrar_controller import cadastrar_bp
from backend.controller.login_controller import login_bp
from backend.controller.calendario_controller import calendario_bp
from backend.controller.publicadosHoje_controller import publicadosHoje_bp
from backend.controller.notificacoes_controller import notificacoes_bp
from backend.controller.minhaContaUsuario_controller import minhaContaUsuario_bp
from backend.controller.escalaDeCores_controller import escalaDeCores_bp
from pathlib import Path

from backend.controller.usuario_controller import usuario_bp

import os
from dotenv import load_dotenv

from backend.service.usuario_service import buscar_usuario_por_id
from backend.service.apresentacao_documento_service import documento_texto

from backend.service.agendador_service import iniciar_agendador


load_dotenv()



FRONTEND = Path(__file__).resolve().parent.parent / "frontend"

app = Flask(
    __name__,
    template_folder=str(FRONTEND / "templates"),
    static_folder=str(FRONTEND / "static"),
    static_url_path="/static"
)

app.add_template_filter(documento_texto, "documento_texto")

app.secret_key = os.getenv("SECRET_KEY")
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")

@app.context_processor
def carregar_usuario():

    usuario = None

    usuario_id = session.get("usuario_id")

    if usuario_id:
        usuario = buscar_usuario_por_id(usuario_id)

    return {
        "usuario_logado": usuario
    }

app.register_blueprint(admin_bp)
app.register_blueprint(index_bp)
app.register_blueprint(cadastrar_bp)
app.register_blueprint(login_bp)
app.register_blueprint(calendario_bp)
app.register_blueprint(publicadosHoje_bp)
app.register_blueprint(notificacoes_bp)
app.register_blueprint(minhaContaUsuario_bp)
app.register_blueprint(escalaDeCores_bp)
app.register_blueprint(usuario_bp)

@app.before_request
def proteger_formularios():
    if request.method == 'POST':
        token = session.get('csrf_token', '')
        if not token or not hmac.compare_digest(request.form.get('csrf_token', ''), token):
            abort(403)


@app.context_processor
def contexto_csrf():
    return {'csrf_token': session.setdefault('csrf_token', secrets.token_hex(32))}


if __name__ == "__main__":

    iniciar_agendador()

    app.run(
        host="127.0.0.1",
        port=9001,
        debug=os.getenv("FLASK_DEBUG", "0") == "1",
        use_reloader=False
    )