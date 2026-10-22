"""Step 5: the SQL validator. Only one read-only SELECT on known tables gets through."""
import sqlglot
from sqlglot import exp


class UnsafeSQL(Exception):
    pass


def validate_sql(sql: str, allowed_tables: set[str]) -> str:
    sql = (sql or "").strip().rstrip(";").strip()
    if not sql:
        raise UnsafeSQL("The query is empty.")
    try:
        statements = sqlglot.parse(sql, read="sqlite")
    except sqlglot.errors.SqlglotError as e:
        raise UnsafeSQL(f"The SQL could not be parsed: {e}")
    if len(statements) != 1 or statements[0] is None:
        raise UnsafeSQL("Exactly one SQL statement is allowed.")
    tree = statements[0]
    if not isinstance(tree, (exp.Select, exp.Union)):
        raise UnsafeSQL("Only SELECT queries are allowed.")
    ctes = {c.alias_or_name.lower() for c in tree.find_all(exp.CTE)}
    for table in tree.find_all(exp.Table):
        name = table.name.lower()
        if name not in allowed_tables and name not in ctes:
            raise UnsafeSQL(f"Unknown table: {table.name}")
    return sql
