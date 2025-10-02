from modules.logs import write_block, write_line
import psycopg, pyodbc, os

class PostgreSQLConnection:
    """
    A database connection class for executing queries on a SQL database.

    This class handles establishing a connection to the database,
    executing queries, and fetching results. It supports both 
    read (SELECT) and write (INSERT, UPDATE, DELETE) operations.
    """

    def __init__(self):
        self.pghost = os.getenv("PGHOST")
        self.pguser = os.getenv("PGUSER")
        self.pgpassword = os.getenv("PGPASSWORD")
        self.pgdatabase = os.getenv("PGDATABASE")
        self.pgport = os.getenv("PGPORT", 5432)

    def start_connection(self):
        """
        Establishes and returns a new connection to the database.

        Returns:
            A connection object for interacting with the database.
        """
        try:
            conn = psycopg.connect(
                host=self.pghost,
                user=self.pguser,
                password=self.pgpassword,
                dbname=self.pgdatabase,
                port=int(self.pgport),
                sslmode="require",
                autocommit=True
            )
            return conn
        except Exception as e:
            logs = []
            logs.append("---ERROR---")
            logs.append(f"{e}")
            logs.append("---ERROR---")
            write_block(logs, "Database")
            return None

    
    def fetch_all(self, query):
        """
        Executes a SELECT query and returns all results.

        Args:
            query (str): The SQL query to execute.

        Returns:
            dict: A dictionary containing:
                - 'columns': A list of column names.
                - 'rows': A list of dictionaries representing the result rows,
                        with column names as keys.
            If an error occurs, returns a dictionary with an 'error' key containing the error message.
        """
        conn = self.start_connection()
        if not conn:
            logs = []
            logs.append("---ERROR---")
            logs.append("Unable to connect with database")
            logs.append("---ERROR---")
            write_block(logs, "Database")
            return None
        try:
            with conn.cursor() as cur:
                cur.execute(query)
                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
                
                result_rows = [dict(zip(columns, row)) for row in rows]
                return {
                    "columns": columns,
                    "rows": result_rows
                }

        except Exception as e:
            logs = []
            logs.append("---ERROR---")
            logs.append(f"{e}")
            logs.append("---ERROR---")
            write_block(logs, "Database")
            return {"error": str(e)}
        finally:
            conn.close()

    def fetch_one_value(self, query):
        conn = self.start_connection()
        if not conn:
            logs = []
            logs.append("---ERROR---")
            logs.append("Unable to connect with database")
            logs.append("---ERROR---")
            write_block(logs, "Database")
            return ""
        try:
            with conn.cursor() as cur:
                cur.execute(query)
                row = cur.fetchone()  # first row only
                return row[0] if row else ""
        except Exception as e:
            logs = []
            logs.append("---ERROR---")
            logs.append(f"{e}")
            logs.append("---ERROR---")
            write_block(logs, "Database")
            return ""
        finally:
            conn.close()

    def execute_one(self, query):
        """
        Executes a query that modifies data (INSERT, UPDATE, DELETE, etc.).

        Args:
            query (str): The SQL query to execute.

        Returns:
            None. Prints error messages if an exception occurs.
        """
        conn = self.start_connection()
        if not conn:
            logs = []
            logs.append("---ERROR---")
            logs.append("Unable to connect with database")
            logs.append("---ERROR---")
            write_block(logs, "Database")
            return False
        try:
            with conn.cursor() as cur:
                cur.execute(query)
            conn.commit()
            return True
        except Exception as e:
            logs = []
            logs.append("---ERROR---")
            if 'already exists' in str(e):
                logs.append(f"Table already exists: {e}")
            else:
                logs.append(f"{e}")
            logs.append("---ERROR---")
            write_block(logs, "Database")
            return False
        finally:
            conn.close()

    def execute_many(self, query: str, values: list):
        """
        Executes a query with different data

        Args:
            query (str): The SQL query to execute.
            values (list): All the row values

        Returns:
            None. Prints error messages if an exception occurs.
        """
        conn = self.start_connection()
        if not conn:
            logs = []
            logs.append("---ERROR---")
            logs.append("Unable to connect with database")
            logs.append("---ERROR---")
            write_block(logs, "Database")
            return False
        try:
            with conn.cursor() as cur:
                cur.executemany(query, values)
            return True
        except Exception as e:
            logs = []
            logs.append("---ERROR---")
            logs.append(f"{e}")
            logs.append("---ERROR---")
            write_block(logs, "Database")
            return False
        finally:
            conn.close()


class SQLServerConnection:
    """
    A database connection class for executing queries on a SQL database.

    This class handles establishing a connection to the database,
    executing queries, and fetching results. It supports both 
    read (SELECT) and write (INSERT, UPDATE, DELETE) operations.
    """

    def __init__(self):
        self.driver = "ODBC Driver 17 for SQL Server"
        self.server = os.getenv("SQLSSERVER")
        self.database = os.getenv("SQLSDATABASE")
        self.uid = os.getenv("SQLSUID")
        self.pwd = os.getenv("SQLSPWD")

    def start_connection(self):
        """
        Establishes and returns a new connection to the database.

        Returns:
            A connection object for interacting with the database.
        """
        conn = pyodbc.connect(
            f"DRIVER={self.driver};"
            f"SERVER={self.server};"
            f"DATABASE={self.database};"
            f"UID={self.uid};"
            f"PWD={self.pwd};"
        )
        return conn

    def fetch_all(self, query):
        """
        Executes a SELECT query and returns all results.

        Args:
            query (str): The SQL query to execute.

        Returns:
            dict: A dictionary containing:
                - 'columns': A list of column names.
                - 'rows': A list of dictionaries representing the result rows,
                        with column names as keys.
            If an error occurs, returns a dictionary with an 'error' key containing the error message.
        """
        conn = self.start_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query)
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()

            # Convert rows into list of dicts (column-name keys)
            result_rows = [dict(zip(columns, row)) for row in rows]

            return { 
                "columns": columns,
                "rows": result_rows
            }

        except Exception as e:
            logs = []
            logs.append("---ERROR---")
            logs.append(f"{e}")
            logs.append("---ERROR---")
            write_block(logs, "Database")
            return {"error": str(e)}
        finally:
            conn.close()


    def execute_one(self, query):
        """
        Executes a query that modifies data (INSERT, UPDATE, DELETE, etc.).

        Args:
            query (str): The SQL query to execute.

        Returns:
            None. Prints error messages if an exception occurs.
        """
        conn = self.start_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query)
            conn.commit()
        except Exception as e:
            logs = []
            logs.append("---ERROR---")
            logs.append(f"{e}")
            logs.append("---ERROR---")
            write_block(logs, "Database")
        finally:
            conn.close()

    def execute_many(self, query, values):
        """
        Executes a batch query on SQL Server with multiple sets of values.
        """
        conn = self.start_connection()
        try:
            with conn.cursor() as cur:
                cur.fast_executemany = True  # SQL Server optimization
                cur.executemany(query, values)
                conn.commit()
        except Exception as e:
            logs = []
            logs.append("---ERROR---")
            logs.append(f"{e}")
            logs.append("---ERROR---")
            write_block(logs, "Database")
        finally:
            conn.close()

    def get_primary_key(self, table: str):
        """
        Gets the primary key of a given table

        Args:
            table (str): Name of the table to get the primary key

        Returns:
            A list of n elements with the name of each column used for the primary key
        """
        query = f"""
            SELECT 
                c.COLUMN_NAME
            FROM 
                INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
            INNER JOIN 
                INFORMATION_SCHEMA.KEY_COLUMN_USAGE c
                ON c.CONSTRAINT_NAME = tc.CONSTRAINT_NAME
            WHERE 
                tc.TABLE_NAME = '{table}'
                AND tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
            ORDER BY 
                c.ORDINAL_POSITION;
        """
        result = self.fetch_all(query)
        if result:
            return [row["COLUMN_NAME"] for row in result["rows"]]
        

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    sql_server = SQLServerConnection()
    keys = sql_server.get_primary_key("TD_Accounts_Receivable_Cleared")