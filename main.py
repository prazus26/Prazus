from flask import Flask
from controller.index_controller import index_bp
from controller.cadastrar_controller import cadastrar_bp
from controller.login_controller import login_bp
from controller.calendario_controller import calendario_bp
from controller.publicadosHoje_controller import publicadosHoje_bp
from controller.notificacoes_controller import notificacoes_bp
from controller.minhaContaUsuario_controller import minhaContaUsuario_bp
from controller.escalaDeCores_controller import escalaDeCores_bp

app = Flask(__name__)

app.register_blueprint(index_bp)
app.register_blueprint(cadastrar_bp)
app.register_blueprint(login_bp)
app.register_blueprint(calendario_bp)
app.register_blueprint(publicadosHoje_bp)
app.register_blueprint(notificacoes_bp)
app.register_blueprint(minhaContaUsuario_bp)
app.register_blueprint(escalaDeCores_bp)

if __name__ == "__main__":
    app.run(port=9001, debug=True)