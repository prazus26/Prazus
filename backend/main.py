from flask import Flask,session
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

from backend.service.agendador_service import iniciar_agendador


load_dotenv()



FRONTEND = Path(__file__).resolve().parent.parent / "frontend"

app = Flask(
    __name__,
    template_folder=str(FRONTEND / "templates"),
    static_folder=str(FRONTEND / "static"),
    static_url_path="/static"
)

app.secret_key = os.getenv("SECRET_KEY")

@app.context_processor
def carregar_usuario():

    usuario = None

    usuario_id = session.get("usuario_id")

    if usuario_id:
        usuario = buscar_usuario_por_id(usuario_id)

    return {
        "usuario_logado": usuario
    }

app.register_blueprint(index_bp)
app.register_blueprint(cadastrar_bp)
app.register_blueprint(login_bp)
app.register_blueprint(calendario_bp)
app.register_blueprint(publicadosHoje_bp)
app.register_blueprint(notificacoes_bp)
app.register_blueprint(minhaContaUsuario_bp)
app.register_blueprint(escalaDeCores_bp)
app.register_blueprint(usuario_bp)

if __name__ == "__main__":

    iniciar_agendador()

    app.run(
        host="127.0.0.1",
        port=9001,
        debug=True,
        use_reloader=False
    )