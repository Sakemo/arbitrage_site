from modules import create_app, start_background_tasks
from flask import request, render_template
from modules.socketio_custom import socketio

app, config = create_app()

@app.route('/calculadora')
def calculadora():
    odd1 = request.args.get('odd1')
    odd2 = request.args.get('odd2')
    odd3 = request.args.get('odd3')
    return render_template("calculadora.html", odd1=odd1, odd2=odd2, odd3=odd3)

if __name__ == '__main__':
    import os
    # Pega a porta do servidor, ou usa 8001 se estiver rodando local
    port = int(os.environ.get("PORT", 8001))
    
    start_background_tasks(app, config)
    
    # IMPORTANTE: host="0.0.0.0" permite acesso externo
    socketio.run(app, host="0.0.0.0", port=port, debug=False, use_reloader=False)