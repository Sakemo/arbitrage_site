from flask import Blueprint
from flask_socketio import SocketIO, emit
from ..models import BettingOpportunity
from datetime import datetime

socketio_bp = Blueprint('socketio', __name__)
socketio = SocketIO(cors_allowed_origins="*")

@socketio.on('connect')
def handle_connect():
    print(f"Client connected at {datetime.now()}")
    get_opportunities()

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('get_opportunities')
def get_opportunities():
    print("Fetching fresh data from database")
    opportunities = BettingOpportunity.query\
        .order_by(BettingOpportunity.created_at.desc())\
        .all()
    
    opportunities_data = [{
        'id': opp.id,
        'profit': float(opp.profit),
        'age': opp.age,
        'bookmaker1': opp.bookmaker1,
        'sport1': opp.sport1,
        'time1': opp.time1,
        'event1': opp.event1,
        'league1': opp.league1,
        'market1': opp.market1,
        'odds1': float(opp.odds1) if opp.odds1 else None,
        'stake_limit1': opp.stake_limit1,
        'bookmaker2': opp.bookmaker2,
        'sport2': opp.sport2,
        'time2': opp.time2,
        'event2': opp.event2,
        'league2': opp.league2,
        'market2': opp.market2,
        'odds2': float(opp.odds2) if opp.odds2 else None,
        'stake_limit2': opp.stake_limit2
    } for opp in opportunities]
    
    print(f"Emitting {len(opportunities_data)} opportunities")
    emit('opportunities', opportunities_data)
