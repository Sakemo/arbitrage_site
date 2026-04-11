from flask_socketio import SocketIO

socketio = SocketIO(cors_allowed_origins="*", async_mode="threading")

def register_socketio_blueprint(app):
    from .routes import socketio_bp
    app.register_blueprint(socketio_bp)
    socketio.init_app(app)
