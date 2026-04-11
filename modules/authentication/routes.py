from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from . import authentication_bp
from .forms import LoginForm
from modules.models import db, User
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

@authentication_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            if user.date_expiry is None or user.date_expiry > datetime.utcnow().date():
                login_user(user)
                return redirect(url_for('views.index'))
            else:
                flash('Seu plano expirou.', 'danger')
                return render_template('home/plan_expired.html')
        else:
            flash('Nome de usuário ou senha inválidos.', 'danger')
    return render_template('home/login.html', form=form, msg=None)

@authentication_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado.', 'success')
    return redirect(url_for('authentication.login'))







@authentication_bp.route('/get_users')
@login_required
def get_users():
    try:
        search = request.args.get('search')
        print(f"Buscando usuários com filtro: {search}")
        
        # Verifica se o usuário atual é admin
        if not current_user.is_admin:
            return jsonify({'error': 'Acesso não autorizado'}), 403
            
        # Desativa a conversão automática de datas
        from sqlalchemy import text
        
        # Busca os usuários com SQL bruto para evitar a conversão automática
        if search:
            query = text("SELECT id, username, is_admin, date_expiry FROM user WHERE username LIKE :search")
            result = db.session.execute(query, {'search': f'%{search}%'})
        else:
            query = text("SELECT id, username, is_admin, date_expiry FROM user")
            result = db.session.execute(query)
        
        # Converte o resultado para dicionário
        users = [dict(row._mapping) for row in result]
        print(f"Encontrados {len(users)} usuários")
        
        # Processa cada usuário
        for user in users:
            try:
                if user['date_expiry']:
                    if isinstance(user['date_expiry'], str):
                        # Tenta converter a string para datetime
                        try:
                            from datetime import datetime
                            # Tenta com o formato com segundos primeiro
                            try:
                                dt = datetime.strptime(user['date_expiry'], '%Y-%m-%d %H:%M:%S')
                            except ValueError:
                                # Se falhar, tenta sem os segundos
                                dt = datetime.strptime(user['date_expiry'], '%Y-%m-%d')
                            user['date_expiry'] = dt.strftime('%Y-%m-%d')
                        except Exception as e:
                            print(f"Erro ao converter data string {user['date_expiry']}: {e}")
                    else:
                        # Se for um objeto date/datetime
                        try:
                            user['date_expiry'] = user['date_expiry'].strftime('%Y-%m-%d')
                        except Exception as e:
                            print(f"Erro ao formatar data {user['date_expiry']}: {e}")
                            user['date_expiry'] = str(user['date_expiry'])
            except Exception as e:
                print(f"Erro ao processar data do usuário {user.get('id')}: {e}")
                user['date_expiry'] = None
        
        print(f"Retornando {len(users)} usuários")
        return jsonify(users)
        
    except Exception as e:
        import traceback
        error_msg = f"Erro em get_users: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        return jsonify({'error': error_msg, 'trace': traceback.format_exc()}), 500

@authentication_bp.route('/add_user', methods=['POST'])
def add_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    date_expiry_str = data.get('date_expiry')
    
    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Usuário já existe'}), 400
    
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    
    if date_expiry_str:
        date_expiry = datetime.strptime(date_expiry_str, '%Y-%m-%d').date()
    else:
        date_expiry = None
    
    new_user = User(username=username, password_hash=hashed_password, date_expiry=date_expiry)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'Usuário adicionado com sucesso'})

@authentication_bp.route('/delete_user/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = User.query.get(id)
    if not user:
        return jsonify({'message': 'Usuário não encontrado'}), 404
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'Usuário deletado com sucesso'})

@authentication_bp.route('/update_user', methods=['POST'])
def update_user():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    if not user:
        return jsonify({'message': 'Usuário não encontrado'}), 404
    
    user.is_admin = data.get('is_admin', user.is_admin)
    if data.get('newPassword'):
        user.password_hash = generate_password_hash(data.get('newPassword'), method='pbkdf2:sha256')
    
    date_expiry_str = data.get('date_expiry')
    if date_expiry_str:
        user.date_expiry = datetime.strptime(date_expiry_str, '%Y-%m-%d').date()
    else:
        user.date_expiry = None
    
    db.session.commit()
    return jsonify({'message': 'Usuário atualizado com sucesso'})

@authentication_bp.route('/info_user')
def info_user():
    username = request.args.get('username')
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'message': 'Usuário não encontrado'}), 404
    user_info = {
        'username': user.username,
        'is_admin': user.is_admin,
        'date_expiry': user.date_expiry.strftime('%Y-%m-%d') if user.date_expiry else ''
    }
    return jsonify(user_info)

@authentication_bp.route('/edit_user/<int:id>')
@login_required
def edit_user(id):
    user = User.query.get_or_404(id)
    date_expiry = user.date_expiry.strftime('%Y-%m-%d') if user.date_expiry else ''
    return render_template('home/edit_user.html', user=user, date_expiry=date_expiry)


@authentication_bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    current_password = request.form.get('currentPassword')
    new_password = request.form.get('newPassword')
    confirm_new_password = request.form.get('confirmNewPassword')

    if not check_password_hash(current_user.password_hash, current_password):
        flash('Senha atual incorreta.', 'danger')
        return redirect(url_for('views.user'))

    if new_password != confirm_new_password:
        flash('As novas senhas não coincidem.', 'danger')
        return redirect(url_for('views.user'))

    current_user.password_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
    db.session.commit()
    flash('Senha atualizada com sucesso.', 'success')
    return redirect(url_for('views.user'))