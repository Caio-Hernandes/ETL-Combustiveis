
import psycopg
from psycopg.rows import dict_row

from fastapi import FastAPI, HTTPException, Query

from src.storage.postgres_repository import PostgresRepository


app = FastAPI(
    title="API de Preços de Combustíveis - ANP",
    description="Indicadores de preços de combustíveis no Brasil",
    version="1.0.0",
)


@app.get("/health")
def health():
    repository = PostgresRepository()

    try:
        with psycopg.connect(
            **repository.connection_params
        ) as conn:
            conn.execute("SELECT 1")

        return {"status": "ok", "database": "connected"}

    except psycopg.Error:
        raise HTTPException(
            status_code=503,
            detail="Banco de dados indisponivel",
        )


@app.get("/precos/mensais")
def listar_precos_mensais(
    uf: str | None = Query(default=None, min_length=2, max_length=2),
    combustivel: str | None = None,
    ano: int | None = Query(default=None, ge=2000, le=2100),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    repository = PostgresRepository()

    query = """
        SELECT
            mes,
            uf,
            combustivel,
            unidade_medida,
            preco_medio,
            preco_minimo,
            preco_maximo,
            total_coletas,
            postos_pesquisados
        FROM gold.vw_preco_mensal_uf
        WHERE 1 = 1
    """

    params = []

    if uf:
        query += " AND uf = %s"
        params.append(uf.upper())

    if combustivel:
        query += " AND UPPER(combustivel) = %s"
        params.append(combustivel.upper())

    if ano:
        query += " AND EXTRACT(YEAR FROM mes) = %s"
        params.append(ano)

    query += """
        ORDER BY mes, uf, combustivel
        LIMIT %s OFFSET %s
    """

    params.extend([limit, offset])

    try:
        with psycopg.connect(
            **repository.connection_params,
            row_factory=dict_row,
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                resultados = cursor.fetchall()

        return resultados

    except psycopg.Error:
        raise HTTPException(
            status_code=503,
            detail="Nao foi possivel consultar os precos",
        )
