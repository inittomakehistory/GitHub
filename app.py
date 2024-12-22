from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta 
import statistics 

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fitness.db'
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    activities = db.relationship('Activity', backref='user', lazy=True)
    goals = db.relationship('Goal', backref='user', lazy=True)

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # Duration in minutes
    calories_burned = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)

class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    goal_type = db.Column(db.String(50), nullable=False)
    target_value = db.Column(db.Integer, nullable=False)
    current_value = db.Column(db.Integer, default=0)
    start_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    end_date = db.Column(db.Date, nullable=False)

@app.before_first_request
def create_tables():
    db.create_all()


# Log Activity
@app.route('/activity', methods=['POST'])
def log_activity():
    data = request.json
    new_activity = Activity(
        user_id=data['user_id'],
        activity_type=data['activity_type'],
        duration=data['duration'],
        calories_burned=data['calories_burned'],
        date=datetime.strptime(data['date'], '%Y-%m-%d')
    )
    db.session.add(new_activity)
    db.session.commit()
    return jsonify({'message': 'Activity logged successfully'}), 201

# Get Activity Summary
@app.route('/summary/<int:user_id>', methods=['GET'])
def get_summary(user_id):
    period = request.args.get('period', 'weekly')
    
    if period == 'weekly':
        start_date = datetime.utcnow() - timedelta(days=7)
    else:
        start_date = datetime.utcnow().replace(day=1)
    
    activities = Activity.query.filter(Activity.user_id == user_id, Activity.date >= start_date).all()
    total_duration = sum(a.duration for a in activities)
    total_calories = sum(a.calories_burned for a in activities)
    
    return jsonify({
        'total_duration': total_duration,
        'total_calories': total_calories,
        'activities': [{ 'activity_type': a.activity_type, 'duration': a.duration, 'calories_burned': a.calories_burned, 'date': a.date.strftime('%Y-%m-%d') } for a in activities]
    })

# Set Fitness Goal
@app.route('/goal', methods=['POST'])
def set_goal():
    data = request.json
    new_goal = Goal(
        user_id=data['user_id'],
        goal_type=data['goal_type'],
        target_value=data['target_value'],
        start_date=datetime.strptime(data['start_date'], '%Y-%m-%d'),
        end_date=datetime.strptime(data['end_date'], '%Y-%m-%d')
    )
    db.session.add(new_goal)
    db.session.commit()
    return jsonify({'message': 'Goal set successfully'}), 201

# Track Fitness Goal
@app.route('/goal/<int:user_id>', methods=['GET'])
def track_goal(user_id):
    goals = Goal.query.filter_by(user_id=user_id).all()
    response = []
    for goal in goals:
        response.append({
            'goal_type': goal.goal_type,
            'target_value': goal.target_value,
            'current_value': goal.current_value,
            'start_date': goal.start_date.strftime('%Y-%m-%d'),
            'end_date': goal.end_date.strftime('%Y-%m-%d'),
            'progress': goal.current_value / goal.target_value * 100
        })
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)


