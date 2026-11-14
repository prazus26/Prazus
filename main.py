from flask import Flask,session
from controller.index_controller import index_bp
from controller.cadastrar_controller import cadastrar_bp
from controller.login_controller import login_bp
from controller.calendario_controller import calendario_bp
from controller.publicadosHoje_controller import publicadosHoje_bp
from controller.notificacoes_controller import notificacoes_bp
from controller.minhaContaUsuario_controller import minhaContaUsuario_bp
from controller.escalaDeCores_controller import escalaDeCores_bp

from controller.usuario_controller import usuario_bp

import os
from dotenv import load_dotenv

from service.usuario_service import buscar_usuario_por_id

from service.agendador_service import iniciar_agendador


load_dotenv()

app = Flask(__name__)

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