from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
import openpyxl
from app import app
from flask import send_file
import os


# Route untuk halaman utama
@app.route('/')
def index():
    return render_template('base.html')

# Route untuk halaman login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Verifikasi login dengan MySQL
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['role'] = user[3]
            if user[3] == 'guru':
                return redirect(url_for('dashboard_guru'))
            else:
                return redirect(url_for('dashboard_siswa'))
        else:
            return 'Invalid login credentials'
    
    return render_template('login.html')

# Route untuk halaman registrasi
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']  # Ambil role dari form
        hashed_password = generate_password_hash(password)

        # Simpan ke database MySQL
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (email, password, role) VALUES (%s, %s, %s)", (email, hashed_password, role))
        conn.commit()
        conn.close()

        return redirect(url_for('login'))

    return render_template('register.html')

# Route untuk dashboard guru
@app.route('/dashboard-guru')
def dashboard_guru():
    if 'role' not in session or session['role'] != 'guru':
        return redirect(url_for('login'))
    
    return render_template('dashboard_guru.html')

# Route untuk dashboard siswa
@app.route('/dashboard-siswa')
def dashboard_siswa():
    if 'role' not in session or session['role'] != 'siswa':
        return redirect(url_for('login'))
    
    return render_template('dashboard_siswa.html')

# Route untuk membuat soal
@app.route('/buat-soal', methods=['GET', 'POST'])
def buat_soal():
    if 'role' not in session or session['role'] != 'guru':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        question = request.form['question']
        option_a = request.form['option_a']
        option_b = request.form['option_b']
        option_c = request.form['option_c']
        option_d = request.form['option_d']
        correct_option = request.form['correct_option']
        
        # Simpan soal ke database MySQL
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO questions (question, option_a, option_b, option_c, option_d, correct_option) VALUES (%s, %s, %s, %s, %s, %s)",
                       (question, option_a, option_b, option_c, option_d, correct_option))
        conn.commit()
        conn.close()

        return redirect(url_for('dashboard_guru'))
    
    return render_template('buat_soal.html')

# Pengecekan jawaban
def evaluate_answer(question_id, selected_answer):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True) 
    cursor.execute("SELECT * FROM questions WHERE id = %s", (question_id,))
    question = cursor.fetchone()
    conn.close()

    if question and selected_answer == question['correct_option']:
        return True
    return False

# Lanjut ke soal berikutnya
def get_next_question(question_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM questions WHERE id > %s LIMIT 1", (question_id,))
    next_question = cursor.fetchone()
    conn.close()
    return next_question


# Route untuk mengerjakan soal
@app.route('/kerjakan-soal', methods=['GET', 'POST'])
def kerjakan_soal():
    if 'role' not in session or session['role'] != 'siswa':
        return redirect(url_for('login'))

    if 'score' not in session:
        session['score'] = 0

    if request.method == 'POST':
        selected_answer = request.form.get('answer')
        question_id = request.form.get('question_id')

        if not selected_answer or not question_id:
            flash("Jawaban tidak valid atau tidak ada ID soal.")
            return redirect(url_for('kerjakan_soal'))

        if evaluate_answer(question_id, selected_answer):
            session['score'] += 1

        next_question = get_next_question(question_id)
        if next_question:
            return render_template('kerjakan_soal.html', question=next_question)
        else:
            final_score = session.pop('score', 0)
            return render_template('quiz_result.html', score=final_score)

    # GET method
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM questions ORDER BY id ASC LIMIT 1")
    question = cursor.fetchone()
    conn.close()

    if question:
        return render_template('kerjakan_soal.html', question=question)
    else:
        return "Belum ada soal di database."



# Koneksi ke MySQL
def get_db_connection():
    conn = mysql.connector.connect(
        host='localhost',        # Ganti dengan host MySQL, biasanya 'localhost'
        user='root',             # Ganti dengan username MySQL
        password='',             # Ganti dengan password MySQL
        database='quiz.db'       # Ganti dengan nama database yang telah dibuat di phpMyAdmin
    )
    return conn

# Route untuk logout
@app.route('/logout')
def logout():
    session.clear()  # Menghapus session
    return redirect(url_for('index'))  # Kembali ke halaman utama

# Route untuk home
@app.route('/home')
def home():
    return redirect(url_for('index'))

# Route untuk export ke Excel
@app.route('/export-to-excel')
def export_to_excel():
    # Ambil data dari database MySQL
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM answers')
    data = cursor.fetchall()
    conn.close()

    # Buat workbook dan sheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(['User ID', 'Question ID', 'Answer'])

    # Menambahkan data dari database ke Excel
    for row in data:
        ws.append(row)

    # Simpan file Excel ke folder 'data'
    file_path = 'data/hasil_quiz.xlsx'
    wb.save(file_path)

    # Kirim file untuk diunduh
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
