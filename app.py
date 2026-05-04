from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import numpy as np
import pickle
import hashlib
import time
from datetime import datetime
import base64
import face_recognition
from PIL import Image
import io
import traceback
import os

app = Flask(__name__)
app.secret_key = 'hybrid_blockchain_voting_secure_key'

# --- DATABASE CONFIGURATION ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///voting_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ==========================================
# 1. DATABASE MODELS
# ==========================================
class Voter(db.Model):
    __tablename__ = 'voters'
    id = db.Column(db.Integer, primary_key=True)
    voter_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.String(20), nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    face_image = db.Column(db.Text, nullable=False) 
    face_encoding = db.Column(db.PickleType, nullable=True) 
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    face_registered = db.Column(db.Boolean, default=True)
    has_voted = db.Column(db.Boolean, default=False)
    vote_timestamp = db.Column(db.String(50), nullable=True)
    tx_hash = db.Column(db.String(100), nullable=True)

class Block(db.Model):
    __tablename__ = 'blockchain_ledger'
    id = db.Column(db.Integer, primary_key=True)
    block_index = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.String(50), nullable=False)
    voter_hash = db.Column(db.String(100), nullable=False)
    candidate = db.Column(db.String(100), nullable=False)
    previous_hash = db.Column(db.String(100), nullable=False)
    current_hash = db.Column(db.String(100), nullable=False)

# ==========================================
# 2. FACE EXTRACTION (HARD DRIVE METHOD)
# ==========================================
def get_face_encoding_from_base64(b64_string, file_prefix):
    if not b64_string or len(b64_string) < 100: return None
    if not os.path.exists('faces'): os.makedirs('faces')
    
    # Save image to hard drive temporarily to process
    filename = os.path.join('faces', f"{file_prefix}.jpg")

    try:
        if ',' in b64_string:
            b64_string = b64_string.split(',')[1]
        b64_string = b64_string.replace(' ', '+')
            
        img_data = base64.b64decode(b64_string)
        image = Image.open(io.BytesIO(img_data)).convert('RGB')
        image.save(filename)
        
        loaded_image = face_recognition.load_image_file(filename)
        encodings = face_recognition.face_encodings(loaded_image)
        
        if len(encodings) > 0:
            return encodings[0]
            
        # Clean up failed scans immediately
        if os.path.exists(filename):
            os.remove(filename)
        return None
        
    except Exception as e:
        print(f"CRITICAL Face processing error: {e}")
        return None

# ==========================================
# 3. BLOCKCHAIN LOGIC
# ==========================================
class PersistentBlockchain:
    def __init__(self):
        with app.app_context():
            db.create_all() 
            if not Block.query.first():
                self.create_block(previous_hash='0', candidate='GENESIS_BLOCK', voter_hash='0')

    def create_block(self, previous_hash, candidate, voter_hash):
        index = Block.query.count() + 1
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        block_data = f"{index}{timestamp}{voter_hash}{candidate}{previous_hash}".encode()
        current_hash = hashlib.sha256(block_data).hexdigest()
        
        new_block = Block(
            block_index=index, timestamp=timestamp, voter_hash=voter_hash,
            candidate=candidate, previous_hash=previous_hash, current_hash=current_hash
        )
        db.session.add(new_block)
        db.session.commit()
        return new_block

    def get_previous_block(self):
        return Block.query.order_by(Block.id.desc()).first()

    def add_vote(self, voter_id, candidate):
        previous_block = self.get_previous_block()
        voter_hash = hashlib.sha256(voter_id.encode()).hexdigest()
        return self.create_block(previous_block.current_hash, candidate, voter_hash)

blockchain = PersistentBlockchain()

# ==========================================
# 4. LOAD MACHINE LEARNING MODEL
# ==========================================
MODEL_PATH = 'model.pkl'
try:
    with open(MODEL_PATH, 'rb') as file:
        model = pickle.load(file)
    model_loaded = True
except:
    model_loaded = False

# ==========================================
# 5. VOTER ROUTING & BUSINESS LOGIC
# ==========================================
@app.route('/')
def index():
    if 'voter_id' in session: return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    name = request.form.get('reg_name')
    dob = request.form.get('reg_dob')
    gender = request.form.get('reg_gender')
    voter_id = request.form.get('reg_voter_id')
    face_image_data = request.form.get('face_image_data')

    if not (name and dob and gender and voter_id and face_image_data):
        flash('Registration failed. Please fill all fields and capture your face.', 'error')
        return redirect(url_for('index'))

    voter_id = voter_id.strip()
    if Voter.query.filter_by(voter_id=voter_id).first():
        flash('Voter ID is already registered.', 'error')
        return redirect(url_for('index'))

    new_face_encoding = get_face_encoding_from_base64(face_image_data, f"REGISTER_{voter_id}")
    if new_face_encoding is None:
        flash('Security Error: No human face detected in the frame. Please ensure good lighting.', 'error')
        return redirect(url_for('index'))

    all_voters = Voter.query.all()
    for existing_voter in all_voters:
        if existing_voter.face_encoding is not None:
            matches = face_recognition.compare_faces([existing_voter.face_encoding], new_face_encoding, tolerance=0.5)
            if matches[0]:
                flash(f'CRITICAL FRAUD ALERT: Face already registered to Voter ID [{existing_voter.voter_id}].', 'error')
                return redirect(url_for('index'))

    new_voter = Voter(
        voter_id=voter_id, name=name, dob=dob, gender=gender,
        face_image=face_image_data, face_encoding=new_face_encoding
    )
    db.session.add(new_voter)
    db.session.commit()
    flash(f'Registration complete! Face securely mapped for {name}.', 'success')
    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    voter_id = request.form.get('voter_id')
    login_face_data = request.form.get('login_face_data')
    
    if not voter_id or not login_face_data: 
        flash('Voter ID and a live biometric scan are required to login.', 'error')
        return redirect(url_for('index'))
        
    voter_id = voter_id.strip()
    voter = Voter.query.filter_by(voter_id=voter_id).first()
    
    if not voter:
        flash('Voter ID not found. Please register first.', 'error')
        return redirect(url_for('index'))

    # Process the new live scan
    login_encoding = get_face_encoding_from_base64(login_face_data, f"LOGIN_ATTEMPT_{voter_id}")

    if login_encoding is None:
        flash('Security Error: No face detected during login scan. Please look directly at the camera.', 'error')
        return redirect(url_for('index'))

    # Compare the live scan mathematically against the database scan
    if voter.face_encoding is not None:
        matches = face_recognition.compare_faces([voter.face_encoding], login_encoding, tolerance=0.5)
        
        if matches[0]:
            session['voter_id'] = voter.voter_id
            session['login_time'] = time.time()
            return redirect(url_for('dashboard'))
        else:
            flash('CRITICAL: Biometric mismatch. Live scan does not match the registered face for this Voter ID.', 'error')
            return redirect(url_for('index'))
    else:
        flash('Account Error: No face data found on file for this voter.', 'error')
        return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'voter_id' not in session: return redirect(url_for('index'))
    voter = Voter.query.filter_by(voter_id=session['voter_id']).first()
    if not voter:
        session.pop('voter_id', None)
        return redirect(url_for('index'))
    return render_template('dashboard.html', user=voter, voter_id=voter.voter_id)

@app.route('/vote', methods=['GET', 'POST'])
def vote():
    if 'voter_id' not in session: return redirect(url_for('index'))
    voter = Voter.query.filter_by(voter_id=session['voter_id']).first()

    if voter.has_voted:
        flash('Access Denied: You have already cast your vote.', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        selected_candidate = request.form.get('candidate')
        if model_loaded:
            try:
                voter_age = datetime.now().year - int(voter.dob.split('-')[0])
            except: voter_age = 30
            features = np.array([[voter_age, datetime.now().hour, int(time.time() - session.get('login_time', time.time() - 30)), 1, 0]])
            try:
                import pandas as pd
                features_df = pd.DataFrame(features, columns=['voter_age', 'vote_hour', 'time_taken_seconds', 'device_type', 'failed_login_attempts'])
                is_fraud = model.predict(features_df)[0] == 1 
            except: is_fraud = False
        else: is_fraud = False 

        if is_fraud:
            flash('ML Alert: Abnormal voting behavior detected. Vote rejected to protect integrity.', 'error')
            return redirect(url_for('dashboard'))
        else:
            new_block = blockchain.add_vote(voter.voter_id, selected_candidate)
            voter.has_voted = True
            voter.vote_timestamp = new_block.timestamp
            voter.tx_hash = new_block.current_hash
            db.session.commit()
            flash('Success! Your vote was verified and appended to the blockchain.', 'success')
            return redirect(url_for('dashboard'))
    return render_template('vote.html')

@app.route('/logout')
def logout():
    session.pop('voter_id', None)
    flash('You have been securely logged out.', 'info')
    return redirect(url_for('index'))

# ==========================================
# 6. ELECTION COMMISSION ROUTING
# ==========================================
@app.route('/admin_login', methods=['POST'])
def admin_login():
    admin_id = request.form.get('admin_id')
    admin_pass = request.form.get('admin_pass')

    if admin_id == 'ELECTION_COMMISSION' and admin_pass == 'Admin@2026':
        session['admin_logged_in'] = True
        flash('Secure Election Commission connection established.', 'success')
        return redirect(url_for('admin_dashboard'))
    else:
        flash('SECURITY ALERT: Invalid Election Commission credentials.', 'error')
        return redirect(url_for('index'))

@app.route('/admin')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        flash('Access Denied. Election Commission authorization required.', 'error')
        return redirect(url_for('index'))

    blocks = Block.query.filter(Block.id > 1).all()
    voters = Voter.query.all()
    return render_template('admin.html', blocks=blocks, total_votes=len(blocks), voters=voters)

@app.route('/admin_logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('Election Commission connection securely terminated.', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)