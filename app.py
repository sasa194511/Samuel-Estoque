from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import sqlite3, os, csv
from datetime import datetime
from io import StringIO
from markupsafe import escape
import logging

app = Flask(__name__)
app.secret_key = os.urandom(24)
DATABASE = 'estoque.db'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not os.path.exists(DATABASE):
        with get_db_connection() as conn:
            with open('schema.sql', 'r', encoding='utf8') as f:
                conn.executescript(f.read())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = escape(request.form['username'].strip())
        password = escape(request.form['password'].strip())
        if not username or not password:
            flash("Preencha todos os campos!", "danger")
            return redirect(url_for('login'))
        with get_db_connection() as conn:
            user = conn.execute("SELECT * FROM usuarios WHERE username=? AND password=?", (username, password)).fetchone()
        if user:
            session['user'] = username
            return redirect(url_for('index'))
        else:
            flash("Usuário ou senha inválidos!", "danger")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    with get_db_connection() as conn:
        produtos = conn.execute("SELECT * FROM produtos").fetchall()
    return render_template('index.html', produtos=produtos)

@app.route('/produtos', methods=['GET', 'POST'])
def produtos():
    if 'user' not in session:
        return redirect(url_for('login'))
    with get_db_connection() as conn:
        if request.method == 'POST':
            codigo = escape(request.form['codigo'].strip())
            nome = escape(request.form['nome'].strip())
            quantidade = request.form['quantidade'].strip()
            if not codigo or not nome or not quantidade.isdigit():
                flash("Preencha todos os campos corretamente!", "danger")
            else:
                quantidade = int(quantidade)
                try:
                    conn.execute("INSERT INTO produtos (codigo, nome, quantidade) VALUES (?, ?, ?)", (codigo, nome, quantidade))
                    conn.commit()
                    flash(f"Produto {nome} adicionado!", "success")
                except sqlite3.IntegrityError:
                    flash("Código já existente!", "danger")
            return redirect(url_for('produtos'))
        produtos = conn.execute("SELECT * FROM produtos").fetchall()
    return render_template('produtos.html', produtos=produtos)

@app.route('/produto/atualizar', methods=['POST'])
def atualizar_produto():
    if 'user' not in session:
        return redirect(url_for('login'))
    codigo = escape(request.form['codigo'].strip())
    nome = escape(request.form['nome'].strip())
    quantidade = request.form['quantidade'].strip()
    if not codigo or not nome or not quantidade.isdigit():
        flash("Preencha todos os campos corretamente!", "danger")
        return redirect(url_for('produtos'))
    quantidade = int(quantidade)
    with get_db_connection() as conn:
        conn.execute("UPDATE produtos SET nome=?, quantidade=? WHERE codigo=?", (nome, quantidade, codigo))
        conn.commit()
    flash(f"Produto {nome} atualizado!", "success")
    return redirect(url_for('produtos'))

@app.route('/produto/excluir/<codigo>', methods=['GET'])
def excluir_produto(codigo):
    if 'user' not in session:
        return redirect(url_for('login'))
    with get_db_connection() as conn:
        conn.execute("DELETE FROM produtos WHERE codigo=?", (codigo,))
        conn.commit()
    flash("Produto excluído!", "success")
    return redirect(url_for('produtos'))

@app.route('/movimentacoes', methods=['GET', 'POST'])
def movimentacoes():
    if 'user' not in session:
        return redirect(url_for('login'))
    with get_db_connection() as conn:
        if request.method == 'POST':
            codigo = escape(request.form['codigo'].strip())
            tipo = escape(request.form['tipo'].strip())
            quantidade = request.form['quantidade'].strip()
            observacao = escape(request.form['observacao'].strip())
            if not codigo or not quantidade.isdigit():
                flash("Preencha os campos corretamente!", "danger")
                return redirect(url_for('movimentacoes'))
            quantidade = int(quantidade)
            data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            produto = conn.execute("SELECT quantidade, nome FROM produtos WHERE codigo=?", (codigo,)).fetchone()
            if not produto:
                flash("Produto não encontrado!", "danger")
                return redirect(url_for('movimentacoes'))
            quantidade_atual = produto['quantidade']
            nome = produto['nome']
            if tipo == "Saída" and quantidade > quantidade_atual:
                flash("Quantidade insuficiente em estoque!", "warning")
                return redirect(url_for('movimentacoes'))
            nova_quantidade = quantidade_atual + quantidade if tipo == "Entrada" else quantidade_atual - quantidade
            conn.execute("UPDATE produtos SET quantidade=? WHERE codigo=?", (nova_quantidade, codigo))
            conn.execute("INSERT INTO movimentacoes (codigo, tipo, quantidade, data, observacao) VALUES (?, ?, ?, ?, ?)",
                         (codigo, tipo, quantidade, data, observacao))
            conn.commit()
            flash(f"Movimentação de {tipo} para o produto {nome} registrada!", "success")
            return redirect(url_for('movimentacoes'))
        movs = conn.execute("SELECT * FROM movimentacoes ORDER BY data DESC").fetchall()
    return render_template('movimentacoes.html', movimentacoes=movs)

@app.route('/exportar')
def exportar():
    if 'user' not in session:
        return redirect(url_for('login'))
    with get_db_connection() as conn:
        produtos = conn.execute("SELECT codigo, nome, quantidade FROM produtos").fetchall()
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(["Código", "Nome", "Quantidade"])
    for prod in produtos:
        writer.writerow([prod["codigo"], prod["nome"], prod["quantidade"]])
    output = si.getvalue()
    return send_file(StringIO(output), mimetype='text/csv', as_attachment=True, download_name='produtos.csv')

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
