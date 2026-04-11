from flask import Blueprint, jsonify, request
from .models import BettingOpportunity, db
from sqlalchemy import distinct
import datetime

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/filters', methods=['GET'])
def get_filter_options():
    # Get unique bookmakers
    bookmakers = set()
    for i in range(1, 5):
        column = f'bookmaker{i}'
        values = db.session.query(distinct(getattr(BettingOpportunity, column))).filter(
            getattr(BettingOpportunity, column).isnot(None)
        ).all()
        bookmakers.update([v[0] for v in values])
    
    # Get unique sports
    sports = set()
    for i in range(1, 5):
        column = f'sport{i}'
        values = db.session.query(distinct(getattr(BettingOpportunity, column))).filter(
            getattr(BettingOpportunity, column).isnot(None)
        ).all()
        # Only add sports that don't start with '('
        sports.update([v[0] for v in values if v[0] and not v[0].startswith('(')])
    
    return jsonify({
        'bookmakers': sorted(list(bookmakers)),
        'sports': sorted(list(sports)),  # Will now only contain valid sports
        'min_profit': db.session.query(db.func.min(BettingOpportunity.profit)).scalar() or 0,
        'max_profit': db.session.query(db.func.max(BettingOpportunity.profit)).scalar() or 0
    })
@api_bp.route('/api/opportunities', methods=['GET'])
def get_opportunities():
    query = BettingOpportunity.query
    
    # Get all filter parameters
    # Sempre trate como lista de casas, mesmo se vier string separada por vírgula
    bookmakers = []
    # getlist pode retornar ['A,B'] se enviado como string única, então trate ambos os casos
    raw_bookmakers = request.args.getlist('bookmaker')
    for item in raw_bookmakers:
        if ',' in item:
            bookmakers.extend([b.strip() for b in item.split(',') if b.strip()])
        elif item.strip():
            bookmakers.append(item.strip())
    # Agora 'bookmakers' é sempre lista real de casas, ou vazia
    # --- Suporte multi-select para esportes ---
    sports = []
    raw_sports = request.args.getlist('sport')
    for item in raw_sports:
        if ',' in item:
            sports.extend([s.strip() for s in item.split(',') if s.strip()])
        elif item.strip():
            sports.append(item.strip())
    date = request.args.get('date')
    min_profit = request.args.get('min_profit', type=float)
    max_profit = request.args.get('max_profit', type=float)
    max_age = request.args.get('max_age', type=int)
    sort_order = request.args.get('sort', 'desc')  # Get sort parameter
    
    # Apply existing filters
    if bookmakers:
        print('Bookmakers recebidos:', bookmakers)  # Debug
        # Normaliza para comparar ignorando maiúsculas/minúsculas e espaços
        def normalize(s):
            return s.strip().lower() if s else s
        filters = []
        for b in bookmakers:
            nb = normalize(b)
            filters.append(db.or_(
                db.func.lower(db.func.trim(BettingOpportunity.bookmaker1)) == nb,
                db.func.lower(db.func.trim(BettingOpportunity.bookmaker2)) == nb,
                db.func.lower(db.func.trim(BettingOpportunity.bookmaker3)) == nb,
                db.func.lower(db.func.trim(BettingOpportunity.bookmaker4)) == nb
            ))
        query = query.filter(db.or_(*filters))

    if sports:
        print('Esportes recebidos:', sports)
        def normalize_s(s):
            return s.strip().lower() if s else s
        sport_filters = []
        for s in sports:
            ns = normalize_s(s)
            sport_filters.append(db.or_(
                db.func.lower(db.func.trim(BettingOpportunity.sport1)) == ns,
                db.func.lower(db.func.trim(BettingOpportunity.sport2)) == ns,
                db.func.lower(db.func.trim(BettingOpportunity.sport3)) == ns,
                db.func.lower(db.func.trim(BettingOpportunity.sport4)) == ns
            ))
        query = query.filter(db.or_(*sport_filters))
    
    if date:
        print(f"Date: {date}")
        print("Exemplo time1:", BettingOpportunity.query.first().time1)
        query = query.filter(db.or_(
            BettingOpportunity.time1.like(f"{date}%"),
            BettingOpportunity.time2.like(f"{date}%"),
            BettingOpportunity.time3.like(f"{date}%"),
            BettingOpportunity.time4.like(f"{date}%")
        ))
    
    if min_profit is not None:
        query = query.filter(BettingOpportunity.profit >= min_profit)
    
    if max_profit is not None:
        query = query.filter(BettingOpportunity.profit <= max_profit)
    
    # Apply sorting
    print(f"Sorting order: {sort_order}")  # Debug log
    if sort_order == 'asc':
        query = query.order_by(BettingOpportunity.created_at.asc())
    else:
        query = query.order_by(BettingOpportunity.created_at.desc())
    
    # Paginação
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=20, type=int)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    opportunities = pagination.items
    opportunities_data = [{
        'id': opp.id,
        'profit': float(opp.profit),
        'age': opp.age,
        'bookmaker1': opp.bookmaker1,
        'sport1': opp.sport1,
        'time1': opp.time1,
        'event1': opp.event1,
        'event_link1': opp.event_link1,  # Add event links
        'league1': opp.league1,
        'market1': opp.market1,
        'odds1': float(opp.odds1) if opp.odds1 else None,
        'stake_limit1': opp.stake_limit1,
        'bookmaker2': opp.bookmaker2,
        'sport2': opp.sport2,
        'time2': opp.time2,
        'event2': opp.event2,
        'event_link2': opp.event_link2,  # Add event links
        'league2': opp.league2,
        'market2': opp.market2,
        'odds2': float(opp.odds2) if opp.odds2 else None,
        'stake_limit2': opp.stake_limit2,
        'bookmaker3': opp.bookmaker3,
        'sport3': opp.sport3,
        'time3': opp.time3,
        'event3': opp.event3,
        'event_link3': opp.event_link3,  # Add event links
        'league3': opp.league3,
        'market3': opp.market3,
        'odds3': float(opp.odds3) if opp.odds3 else None,
        'stake_limit3': opp.stake_limit3,
        'bookmaker4': opp.bookmaker4,
        'sport4': opp.sport4,
        'time4': opp.time4,
        'event4': opp.event4,
        'event_link4': opp.event_link4,  # Add event links
        'league4': opp.league4,
        'market4': opp.market4,
        'odds4': float(opp.odds4) if opp.odds4 else None,
        'stake_limit4': opp.stake_limit4,
        'created_at': opp.created_at.isoformat() if opp.created_at else None,
    } for opp in opportunities]
    
    return jsonify({
        'items': opportunities_data,
        'page': page,
        'per_page': per_page,
        'total': pagination.total,
        'pages': pagination.pages,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    })