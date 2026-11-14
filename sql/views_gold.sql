
-- ==========================================
-- 1. PRECO MENSAL POR UF E COMBUSTIVEL
-- ==========================================

CREATE OR REPLACE VIEW gold.vw_preco_mensal_uf AS
SELECT
    DATE_TRUNC('month', f.data_coleta)::DATE AS mes,
    l.uf,
    c.nome AS combustivel,
    c.unidade_medida,

    ROUND(AVG(f.preco_venda), 4) AS preco_medio,
    MIN(f.preco_venda) AS preco_minimo,
    MAX(f.preco_venda) AS preco_maximo,

    COUNT(*) AS total_coletas,
    COUNT(DISTINCT f.revenda_id) AS postos_pesquisados

FROM gold.fato_preco f

JOIN gold.dim_localidade l
    ON l.id = f.localidade_id

JOIN gold.dim_combustivel c
    ON c.id = f.combustivel_id

GROUP BY
    DATE_TRUNC('month', f.data_coleta)::DATE,
    l.uf,
    c.nome,
    c.unidade_medida;


-- ==========================================
-- 2. PRECO MENSAL NACIONAL
-- ==========================================

CREATE OR REPLACE VIEW gold.vw_preco_mensal_brasil AS
SELECT
    DATE_TRUNC('month', f.data_coleta)::DATE AS mes,
    c.nome AS combustivel,
    c.unidade_medida,

    ROUND(AVG(f.preco_venda), 4) AS preco_medio,
    MIN(f.preco_venda) AS preco_minimo,
    MAX(f.preco_venda) AS preco_maximo,

    COUNT(*) AS total_coletas,
    COUNT(DISTINCT f.revenda_id) AS postos_pesquisados

FROM gold.fato_preco f

JOIN gold.dim_combustivel c
    ON c.id = f.combustivel_id

GROUP BY
    DATE_TRUNC('month', f.data_coleta)::DATE,
    c.nome,
    c.unidade_medida;


-- ==========================================
-- 3. VARIACAO MENSAL POR UF
-- ==========================================

CREATE OR REPLACE VIEW gold.vw_variacao_mensal_uf AS

WITH evolucao AS (
    SELECT
        mes,
        uf,
        combustivel,
        unidade_medida,
        preco_medio,

        LAG(mes) OVER (
            PARTITION BY uf, combustivel, unidade_medida
            ORDER BY mes
        ) AS mes_anterior,

        LAG(preco_medio) OVER (
            PARTITION BY uf, combustivel, unidade_medida
            ORDER BY mes
        ) AS preco_mes_anterior

    FROM gold.vw_preco_mensal_uf
)

SELECT
    mes,
    uf,
    combustivel,
    unidade_medida,
    preco_medio,
    preco_mes_anterior,

    CASE
        WHEN mes_anterior = (mes - INTERVAL '1 month')::DATE
             AND preco_mes_anterior > 0
        THEN ROUND(
            (
                (preco_medio / preco_mes_anterior) - 1
            ) * 100,
            2
        )
        ELSE NULL
    END AS variacao_percentual

FROM evolucao;
