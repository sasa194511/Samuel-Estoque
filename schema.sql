CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

CREATE TABLE produtos (
    codigo TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    quantidade INTEGER NOT NULL
);

CREATE TABLE movimentacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL,
    tipo TEXT NOT NULL,
    quantidade INTEGER NOT NULL,
    data TEXT NOT NULL,
    observacao TEXT,
    FOREIGN KEY (codigo) REFERENCES produtos (codigo)
);

-- Usuário padrão para testes (senha não criptografada para simplicidade)
INSERT INTO usuarios (username, password) VALUES ('admin', '1234');