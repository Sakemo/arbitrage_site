from modules import create_app
from modules.models import db, User
import time

def create_new_user():
    app, _ = create_app()
    
    with app.app_context():
        time.sleep(1)
        
        new_user = User(username="gabriel")
        new_user.set_password("123456")
        new_user.is_admin = True
        
        db.session.add(new_user)
        db.session.commit()
        
        created_user = User.query.filter_by(username="gabriel").first()
        print(f"Created user: {created_user.username}")

if __name__ == "__main__":
    create_new_user()