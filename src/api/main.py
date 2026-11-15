
import psycopg
from psycopg.rows import dict_row

from fastapi import FastAPI, HTTPException, Query

from src.storage.postgres_repository import PostgresRepository
from datetime import date
from decimal import Decimal
from typing import Literal
from fastapi import HTTPException, Query


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

@app.get("/precos/mensais")
def listar_precos_mensais(
    uf: str | None = Query(default=None, min_length=2, max_length=2),
    combustivel: str | None = None,
    ano: int | None = Query(default=None, ge=2000, le=2100),
    mes_inicio: date | None = None,
    mes_fim: date | None = None,
    preco_min: Decimal | None = Query(default=None, ge=0),
    preco_max: Decimal | None = Query(default=None, ge=0),
    ordenar_por: Literal[
        "mes",
        "uf",
        "combustivel",
        "preco_medio",
        "total_coletas",
        "postos_pesquisados",
    ] = "mes",
    ordem: Literal["asc", "desc"] = "asc",
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    if mes_inicio and mes_fim and mes_inicio > mes_fim:
        raise HTTPException(
            status_code=422,
            detail="mes_inicio nao pode ser maior que mes_fim",
        )

    if preco_min is not None and preco_max is not None:
        if preco_min > preco_max:
            raise HTTPException(
                status_code=422,
                detail="preco_min nao pode ser maior que preco_max",
            )

    filtros = []
    params = []

    if uf:
        filtros.append("uf = %s")
        params.append(uf.upper())

    if combustivel:
        filtros.append("UPPER(combustivel) = %s")
        params.append(combustivel.upper())

    if ano:
        filtros.append("EXTRACT(YEAR FROM mes) = %s")
        params.append(ano)

    if mes_inicio:
        filtros.append("mes >= %s")
        params.append(mes_inicio)

    if mes_fim:
        filtros.append("mes <= %s")
        params.append(mes_fim)

    if preco_min is not None:
        filtros.append("preco_medio >= %s")
        params.append(preco_min)

    if preco_max is not None:
        filtros.append("preco_medio <= %s")
        params.append(preco_max)

    where = (
        "WHERE " + " AND ".join(filtros)
        if filtros
        else ""
    )

    # Campos e direcoes validados pelo Literal
    query = f"""
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
        {where}
        ORDER BY {ordenar_por} {ordem},
                 mes, uf, combustivel
        LIMIT %s OFFSET %s
    """

    params.extend([limit, offset])

    repository = PostgresRepository()

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
            detail="Erro ao consultar o banco de dados",
        )
