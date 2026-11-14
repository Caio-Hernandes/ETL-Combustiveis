-- criando schema gold, tabelas dimensoes e tabela fato

CREATE SCHEMA IF NOT EXISTS gold;

-- Dimensao de tempo
CREATE TABLE IF NOT EXISTS gold.dim_tempo (
    data DATE PRIMARY KEY,
    ano SMALLINT NOT NULL,
    mes SMALLINT NOT NULL CHECK (mes BETWEEN 1 AND 12),
    trimestre SMALLINT NOT NULL CHECK (trimestre BETWEEN 1 AND 4)
);

-- Dimensao de localidade
CREATE TABLE IF NOT EXISTS gold.dim_localidade (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    regiao VARCHAR(2),
    uf CHAR(2) NOT NULL,
    municipio TEXT NOT NULL,

    CONSTRAINT uq_localidade UNIQUE (uf, municipio)
);

-- Dimensao de combustivel
CREATE TABLE IF NOT EXISTS gold.dim_combustivel (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome TEXT NOT NULL,
    unidade_medida TEXT NOT NULL,

    CONSTRAINT uq_combustivel UNIQUE (nome, unidade_medida)
);

-- Dimensao de revenda
CREATE TABLE IF NOT EXISTS gold.dim_revenda (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cnpj TEXT NOT NULL UNIQUE,
    nome TEXT,
    bandeira TEXT
);

-- Tabela fato
CREATE TABLE IF NOT EXISTS gold.fato_preco (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    data_coleta DATE NOT NULL
        REFERENCES gold.dim_tempo(data),

    localidade_id BIGINT NOT NULL
        REFERENCES gold.dim_localidade(id),

    combustivel_id BIGINT NOT NULL
        REFERENCES gold.dim_combustivel(id),

    revenda_id BIGINT NOT NULL
        REFERENCES gold.dim_revenda(id),

    preco_venda NUMERIC(12, 4) NOT NULL
        CHECK (preco_venda > 0),

    CONSTRAINT uq_fato_preco UNIQUE (
        data_coleta,
        revenda_id,
        combustivel_id
    )
);

-- Indices para consultas analiticas
CREATE INDEX IF NOT EXISTS idx_fato_localidade
    ON gold.fato_preco(localidade_id);

CREATE INDEX IF NOT EXISTS idx_fato_combustivel
    ON gold.fato_preco(combustivel_id);

CREATE INDEX IF NOT EXISTS idx_fato_revenda
    ON gold.fato_preco(revenda_id);
