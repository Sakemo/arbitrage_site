from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin

from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class BettingOpportunity(db.Model):
    __tablename__ = 'betting_opportunities'
    
    id = db.Column(db.Integer, primary_key=True)
    profit = db.Column(db.Float, nullable=False)
    age = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Bookmaker 1
    bookmaker1 = db.Column(db.String(100), nullable=False)
    sport1 = db.Column(db.String(100), nullable=False)
    time1 = db.Column(db.String(50), nullable=False)
    event1 = db.Column(db.String(200), nullable=False)
    event_link1 = db.Column(db.String(500), nullable=False)
    league1 = db.Column(db.String(200), nullable=False)
    market1 = db.Column(db.String(100), nullable=False)
    odds1 = db.Column(db.Float, nullable=False)
    stake_limit1 = db.Column(db.String(50), nullable=False)
    
    # Bookmaker 2
    bookmaker2 = db.Column(db.String(100), nullable=True)
    sport2 = db.Column(db.String(100), nullable=True)
    time2 = db.Column(db.String(50), nullable=True)
    event2 = db.Column(db.String(200), nullable=True)
    event_link2 = db.Column(db.String(500), nullable=True)
    league2 = db.Column(db.String(200), nullable=True)
    market2 = db.Column(db.String(100), nullable=True)
    odds2 = db.Column(db.Float, nullable=True)
    stake_limit2 = db.Column(db.String(50), nullable=True)

    # Bookmaker 3
    bookmaker3 = db.Column(db.String(100), nullable=True)
    sport3 = db.Column(db.String(100), nullable=True)
    time3 = db.Column(db.String(50), nullable=True)
    event3 = db.Column(db.String(200), nullable=True)
    event_link3 = db.Column(db.String(500), nullable=True)
    league3 = db.Column(db.String(200), nullable=True)
    market3 = db.Column(db.String(100), nullable=True)
    odds3 = db.Column(db.Float, nullable=True)
    stake_limit3 = db.Column(db.String(50), nullable=True)

    # Bookmaker 4
    bookmaker4 = db.Column(db.String(100), nullable=True)
    sport4 = db.Column(db.String(100), nullable=True)
    time4 = db.Column(db.String(50), nullable=True)
    event4 = db.Column(db.String(200), nullable=True)
    event_link4 = db.Column(db.String(500), nullable=True)
    league4 = db.Column(db.String(200), nullable=True)
    market4 = db.Column(db.String(100), nullable=True)
    odds4 = db.Column(db.Float, nullable=True)
    stake_limit4 = db.Column(db.String(50), nullable=True)

    @staticmethod
    def add_or_update(bet_data):
        bet = BettingOpportunity.query.filter_by(
            event1=bet_data['event1'],
            market1=bet_data['market1'],
            bookmaker1=bet_data['bookmaker1']
        ).first()
        
        if bet:
            for key, value in bet_data.items():
                setattr(bet, key, value)
        else:
            bet = BettingOpportunity(**bet_data)
            db.session.add(bet)
        
        db.session.commit()
        return bet

    def to_dict(self):
        return {
            'id': self.id,
            'profit': self.profit,
            'age': self.age,
            'bookmaker1': self.bookmaker1,
            'sport1': self.sport1,
            'time1': self.time1,
            'event1': self.event1,
            'league1': self.league1,
            'market1': self.market1,
            'odds1': self.odds1,
            'stake_limit1': self.stake_limit1,
            'bookmaker2': self.bookmaker2,
            'sport2': self.sport2,
            'time2': self.time2,
            'event2': self.event2,
            'league2': self.league2,
            'market2': self.market2,
            'odds2': self.odds2,
            'stake_limit2': self.stake_limit2,
            'bookmaker3': self.bookmaker3,
            'sport3': self.sport3,
            'time3': self.time3,
            'event3': self.event3,
            'league3': self.league3,
            'market3': self.market3,
            'odds3': self.odds3,
            'stake_limit3': self.stake_limit3,
            'bookmaker4': self.bookmaker4,
            'sport4': self.sport4,
            'time4': self.time4,
            'event4': self.event4,
            'league4': self.league4,
            'market4': self.market4,
            'odds4': self.odds4,
            'stake_limit4': self.stake_limit4
        }

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    date_expiry = db.Column(db.Date, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

def init_db(app):
    with app.app_context():
        db.create_all()
        print("Database tables initialized successfully")

def verify_database(app):
    with app.app_context():
        try:
            count = BettingOpportunity.query.count()

            print(f"Database verification: {count} opportunities found")
            return True
        except Exception as e:

            print(f"Database verification failed: {e}")
            return False

