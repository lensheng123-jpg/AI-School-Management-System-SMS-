"""
AI-SMS Flask application.
Human-in-the-loop decision support prototype.
AI advises only. Human approval mandatory.
"""
from flask import Flask, render_template, request, redirect, url_for, flash, abort, jsonify, session
from functools import wraps
import sqlite3
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Make sure to import the new evaluate_options function
from ai_service import generate_summary, generate_gaps, evaluate_options

app = Flask(__name__)
app.secret_key = 'ai-sms-fyp-2026-change-in-production'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'database', 'ai_sms.db')
AI_CACHE = {}

# --- AUTHENTICATION SETUP ---
USERS = {
    'leader': {'password': 'leader123', 'role': 'School Leader'},
    'admin': {'password': 'admin123', 'role': 'Admin'}
}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in USERS and USERS[username]['password'] == password:
            session['username'] = username
            session['role'] = USERS[username]['role']
            flash(f'Welcome, {username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))
# ----------------------------

def get_db():
    if not os.path.exists(DATABASE):
        abort(500, description="Database not found. Run 'python init_db.py' first.")
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
@login_required
def index():
    conn = get_db()
    cases = conn.execute('''
        SELECT c.*,
            (SELECT COUNT(*) FROM evidence e WHERE e.case_id = c.case_id) AS evidence_count,
            (SELECT COUNT(*) FROM case_options o WHERE o.case_id = c.case_id) AS option_count,
            (SELECT confirmation_status FROM human_decisions d
                WHERE d.case_id = c.case_id LIMIT 1) AS decision_status
        FROM cases c
        ORDER BY c.case_id
    ''').fetchall()
    conn.close()

    dev = [c for c in cases if c['case_id'].startswith('DEV')]
    live = [c for c in cases if c['case_id'].startswith('LIVE')]

    return render_template('index.html', dev_cases=dev, live_cases=live, total=len(cases))

@app.route('/case/<case_id>')
@login_required
def case_detail(case_id):
    conn = get_db()
    case = conn.execute('SELECT * FROM cases WHERE case_id = ?', (case_id,)).fetchone()
    if not case:
        conn.close()
        flash('Case not found.', 'danger')
        return redirect(url_for('index'))

    evidence = conn.execute('SELECT * FROM evidence WHERE case_id = ? ORDER BY evidence_id', (case_id,)).fetchall()
    policy_links = conn.execute('''
        SELECT pl.*, p.title AS policy_title FROM case_policy_links pl
        LEFT JOIN policies p ON pl.policy_id = p.policy_id WHERE pl.case_id = ? ORDER BY pl.policy_id
    ''', (case_id,)).fetchall()
    clauses = conn.execute('''
        SELECT pc.*, p.title AS policy_title FROM policy_clauses pc
        JOIN policies p ON pc.policy_id = p.policy_id
        WHERE pc.policy_id IN (SELECT policy_id FROM case_policy_links WHERE case_id = ?)
        ORDER BY pc.policy_id, pc.section
    ''', (case_id,)).fetchall()
    analysis = conn.execute('SELECT * FROM case_analysis WHERE case_id = ?', (case_id,)).fetchone()
    options = conn.execute('SELECT * FROM case_options WHERE case_id = ? ORDER BY display_order', (case_id,)).fetchall()
    decision = conn.execute('SELECT * FROM human_decisions WHERE case_id = ? LIMIT 1', (case_id,)).fetchone()

    roles = []
    if analysis and analysis['consultation_role_ids']:
        ids = [r.strip() for r in analysis['consultation_role_ids'].split(';') if r.strip()]
        if ids:
            placeholders = ','.join(['?'] * len(ids))
            roles = conn.execute(f'SELECT * FROM roles WHERE role_id IN ({placeholders})', ids).fetchall()

    conn.close()
    cached = AI_CACHE.get(case_id)

    return render_template('case_detail.html', case=case, evidence=evidence, policy_links=policy_links,
                           clauses=clauses, analysis=analysis, options=options, decision=decision, roles=roles, cached_ai=cached)

@app.route('/case/<case_id>/ai')
@login_required
def case_ai(case_id):
    if case_id in AI_CACHE:
        summary, gaps = AI_CACHE[case_id]
        return jsonify({'summary': summary, 'gaps': gaps, 'cached': True})

    conn = get_db()
    case = conn.execute('SELECT * FROM cases WHERE case_id = ?', (case_id,)).fetchone()
    if not case:
        conn.close()
        return jsonify({'summary': None, 'gaps': None, 'error': 'Case not found'}), 404

    evidence = conn.execute('SELECT * FROM evidence WHERE case_id = ? ORDER BY evidence_id', (case_id,)).fetchall()
    conn.close()

    import time
    t0 = time.time()
    summary = generate_summary(case, evidence)
    gaps = generate_gaps(case, evidence)
    elapsed = time.time() - t0

    print(f"[ai] Case {case_id} — {elapsed:.2f}s — summary: {bool(summary)}, gaps: {bool(gaps)}")
    AI_CACHE[case_id] = (summary, gaps)

    return jsonify({'summary': summary, 'gaps': gaps, 'elapsed': round(elapsed, 2), 'cached': False})

@app.route('/case/<case_id>/options')
@login_required
def options(case_id):
    conn = get_db()
    case = conn.execute('SELECT * FROM cases WHERE case_id = ?', (case_id,)).fetchone()
    if not case:
        conn.close()
        flash('Case not found.', 'danger')
        return redirect(url_for('index'))
    options = conn.execute('SELECT * FROM case_options WHERE case_id = ? ORDER BY display_order', (case_id,)).fetchall()
    decision = conn.execute('SELECT * FROM human_decisions WHERE case_id = ? LIMIT 1', (case_id,)).fetchone()
    conn.close()
    return render_template('options.html', case=case, options=options, decision=decision)

# --- NEW ROUTE FOR AI TRADE-OFF ANALYSIS ---
@app.route('/case/<case_id>/ai-options')
@login_required
def case_ai_options(case_id):
    cache_key = f"{case_id}_options"
    if cache_key in AI_CACHE:
        return jsonify({'analysis': AI_CACHE[cache_key]})

    conn = get_db()
    case = conn.execute('SELECT * FROM cases WHERE case_id = ?', (case_id,)).fetchone()
    if not case:
        conn.close()
        return jsonify({'error': 'Case not found'}), 404

    evidence = conn.execute('SELECT * FROM evidence WHERE case_id = ?', (case_id,)).fetchall()
    options = conn.execute('SELECT * FROM case_options WHERE case_id = ? ORDER BY display_order', (case_id,)).fetchall()
    conn.close()

    analysis = evaluate_options(case, evidence, options)
    AI_CACHE[cache_key] = analysis

    return jsonify({'analysis': analysis})
# -------------------------------------------

@app.route('/case/<case_id>/decide', methods=['GET', 'POST'])
@login_required
def decide(case_id):
    conn = get_db()
    case = conn.execute('SELECT * FROM cases WHERE case_id = ?', (case_id,)).fetchone()
    if not case:
        conn.close()
        flash('Case not found.', 'danger')
        return redirect(url_for('index'))

    options = conn.execute('SELECT * FROM case_options WHERE case_id = ? ORDER BY display_order', (case_id,)).fetchall()
    decision = conn.execute('SELECT * FROM human_decisions WHERE case_id = ? LIMIT 1', (case_id,)).fetchone()

    if request.method == 'POST':
        selected = request.form.get('selected_option', '').strip()
        decision_text = request.form.get('decision_text', '').strip()
        rationale = request.form.get('rationale', '').strip()
        review_date = request.form.get('review_date', '').strip()

        if not decision_text or not rationale:
            flash('Decision text and rationale are both required.', 'warning')
            conn.close()
            return redirect(url_for('decide', case_id=case_id))

        if decision and decision['confirmation_status'] == 'human_confirmed':
            flash('Decision already confirmed.', 'info')
            conn.close()
            return redirect(url_for('action_plan', case_id=case_id))

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        decision_id = f'{case_id}-HD'

        # FIXED FORMATTING HERE
        if decision:
            conn.execute('''
                UPDATE human_decisions
                SET selected_option_id = ?, human_decision_text = ?,
                    human_rationale = ?, confirmation_status = ?,
                    decision_date = ?, review_date = ?
                WHERE case_id = ?
            ''', (selected, decision_text, rationale, 'human_confirmed',
                  now, review_date, case_id))
        else:
            conn.execute('''INSERT INTO human_decisions (decision_id, case_id, selected_option_id, human_decision_text, human_rationale,
                confirmation_status, decision_date, review_date, outcome_status, outcome_notes, data_origin) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (decision_id, case_id, selected, decision_text, rationale, 'human_confirmed', now, review_date, 'pending_review', 'Human-authored decision recorded.', 'synthetic'))

        conn.commit()
        conn.close()
        flash('Human decision confirmed. Action plan unlocked.', 'success')
        return redirect(url_for('action_plan', case_id=case_id))

    conn.close()
    return render_template('decision.html', case=case, options=options, decision=decision)

@app.route('/case/<case_id>/action-plan')
@login_required
def action_plan(case_id):
    conn = get_db()
    case = conn.execute('SELECT * FROM cases WHERE case_id = ?', (case_id,)).fetchone()
    decision = conn.execute('SELECT * FROM human_decisions WHERE case_id = ? LIMIT 1', (case_id,)).fetchone()
    conn.close()
    if not case:
        flash('Case not found.', 'danger')
        return redirect(url_for('index'))
    if not decision or decision['confirmation_status'] != 'human_confirmed':
        flash('Action plan is locked until a human decision is confirmed.', 'danger')
        return redirect(url_for('decide', case_id=case_id))
    return render_template('action_plan.html', case=case, decision=decision)

@app.route('/case/<case_id>/audit')
@login_required
def audit(case_id):
    conn = get_db()
    case = conn.execute('SELECT * FROM cases WHERE case_id = ?', (case_id,)).fetchone()
    if not case:
        conn.close()
        flash('Case not found.', 'danger')
        return redirect(url_for('index'))

    evidence = conn.execute('SELECT * FROM evidence WHERE case_id = ?', (case_id,)).fetchall()
    analysis = conn.execute('SELECT * FROM case_analysis WHERE case_id = ?', (case_id,)).fetchone()
    decision = conn.execute('SELECT * FROM human_decisions WHERE case_id = ? LIMIT 1', (case_id,)).fetchone()
    options = conn.execute('SELECT * FROM case_options WHERE case_id = ? ORDER BY display_order', (case_id,)).fetchall()
    conn.close()
    return render_template('audit.html', case=case, evidence=evidence, analysis=analysis, decision=decision, options=options)

@app.errorhandler(500)
def internal_error(e):
    return render_template('base.html', error=str(e)), 500

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)