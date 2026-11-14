
-- ==========================================
-- 1. DIMENSAO TEMPO
-- ==========================================

INSERT INTO gold.dim_tempo (
    data,
    ano,
    mes,
    trimestre
)
SELECT DISTINCT
    data_coleta,
    EXTRACT(YEAR FROM data_coleta)::SMALLINT,
    EXTRACT(MONTH FROM data_coleta)::SMALLINT,
    EXTRACT(QUARTER FROM data_coleta)::SMALLINT
FROM stage_preco
ON CONFLICT (data) DO NOTHING;


-- ==========================================
-- 2. DIMENSAO LOCALIDADE
-- ==========================================

INSERT INTO gold.dim_localidade (
    regiao,
    uf,
    municipio
)
SELECT DISTINCT ON (uf, municipio)
    regiao,
    uf,
    municipio
FROM stage_preco
ORDER BY
    uf,
    municipio,
    regiao NULLS LAST
ON CONFLICT (uf, municipio) DO NOTHING;


-- ==========================================
-- 3. DIMENSAO COMBUSTIVEL
-- ==========================================

INSERT INTO gold.dim_combustivel (
    nome,
    unidade_medida
)
SELECT DISTINCT
    combustivel,
    unidade_medida
FROM stage_preco
ON CONFLICT (nome, unidade_medida) DO NOTHING;


-- ==========================================
-- 4. DIMENSAO REVENDA
-- ==========================================

INSERT INTO gold.dim_revenda (
    cnpj,
    nome,
    bandeira
)
SELECT DISTINCT ON (cnpj)
    cnpj,
    revenda,
    bandeira
FROM stage_preco
ORDER BY
    cnpj,
    revenda NULLS LAST,
    bandeira NULLS LAST
ON CONFLICT (cnpj) DO NOTHING;


-- ==========================================
-- 5. TABELA FATO PRECO
-- ==========================================

INSERT INTO gold.fato_preco (
    data_coleta,
    localidade_id,
    combustivel_id,
    revenda_id,
    preco_venda
)
SELECT
    s.data_coleta,
    l.id,
    c.id,
    r.id,
    s.preco_venda
FROM stage_preco s

INNER JOIN gold.dim_localidade l
    ON l.uf = s.uf
    AND l.municipio = s.municipio

INNER JOIN gold.dim_combustivel c
    ON c.nome = s.combustivel
    AND c.unidade_medida = s.unidade_medida

INNER JOIN gold.dim_revenda r
    ON r.cnpj = s.cnpj

ON CONFLICT (
    data_coleta,
    revenda_id,
    combustivel_id
)
DO UPDATE SET
    preco_venda = EXCLUDED.preco_venda
WHERE
    gold.fato_preco.preco_venda
    IS DISTINCT FROM EXCLUDED.preco_venda;
