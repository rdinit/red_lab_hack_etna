import duckdb
import pandas as pd
from loguru import logger

QUERIES = {}

QUERIES[
    "web_response"
] = """
    select
     point as time,
     sum(total_call_time) / sum(call_count) as "web_response"
    from metrics_collector
    where
     language = 'java'
     and app_name = '[GMonit] Collector'
     and scope is NULL
     and name = 'HttpDispatcher'
    group by point
    order by point
    """

QUERIES[
    "throughput"
] = """
    select
     point as time,
     sum(call_count) as "throughput"
    from metrics_collector
    where
     language = 'java'
     and app_name = '[GMonit] Collector'
     and scope is NULL
     and name = 'HttpDispatcher'
    group by point
    order by point
"""

QUERIES[
    "apdex"
] = """
    select
     point as time,
     (sum(call_count) + sum(total_call_time)/2) / (sum(call_count) + sum(total_call_time) + sum(total_exclusive_time)) as "apdex"
    from metrics_collector
    where
     language = 'java'
     and app_name = '[GMonit] Collector'
     and scope is NULL
     and name = 'Apdex'
    group by time
    order by time
"""

QUERIES[
    "error"
] = """
    select
     point as time,
     sum(call_count * cast(name = 'Errors/allWeb' as INT)) / sum(call_count * cast(name = 'HttpDispatcher' as INT)) as "error"
    from metrics_collector
    where
     language = 'java'
     and app_name = '[GMonit] Collector'
     and scope is NULL
     and name in ('HttpDispatcher', 'Errors/allWeb')
    group by point
    order by point
"""


def select_metric(metric_name):
    metric_series = duckdb.sql(f"select * from {metric_name}").df()
    metric_series = metric_series.set_index("time")[metric_name]
    return metric_series


def _select_metric(metric_name):
    logger.info(f"Selecting Metric '{metric_name}'")
    metric_series = duckdb.sql(QUERIES[metric_name]).df()
    metric_series = metric_series.set_index("time")[metric_name]

    metric_series = metric_series.asfreq("T")
    metric_series = metric_series.fillna(method="ffill")

    return pd.DataFrame(metric_series)


def create_tables_with_metrics():
    logger.info("Creating Tables")
    for metric in QUERIES:
        metric_df = _select_metric(metric)
        metric_df.to_parquet(f"data/{metric}.parquet")
        duckdb.sql(f"CREATE TABLE {metric} AS FROM read_parquet('data/{metric}.parquet')")

    duckdb.sql("DROP TABLE metrics_collector")


def create_database():
    logger.info("Creating Database")

    column_names = [
        "account_id",
        "name",
        "point",
        "call_count",
        "total_call_time",
        "total_exclusive_time",
        "min_call_time",
        "max_call_time",
        "sum_of_squares",
        "instances",
        "language",
        "app_name",
        "app_id",
        "scope",
        "host",
        "display_host",
        "pid",
        "agent_version",
        "labels",
    ]

    duckdb.sql(
        f"""
        CREATE TABLE metrics_collector AS FROM read_csv(
            'data/metrics_collector.tsv.gz',
            delim = '\t',
            header = false
        )
    """
    )

    for i, column in enumerate(column_names):
        duckdb.sql(f"ALTER TABLE metrics_collector RENAME column{i:02d} TO {column};")

    create_tables_with_metrics()


if __name__ == "__main__":
    create_database()
