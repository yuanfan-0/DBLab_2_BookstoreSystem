from be.model import error
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_READ_COMMITTED
class DBTransaction:
    def __init__(self, db_conn):
        self.conn = db_conn.conn
        self.transaction_status = False

    def __enter__(self):
        try:
            self.conn.set_isolation_level(ISOLATION_LEVEL_READ_COMMITTED)
            self.transaction_status = True
            return self
        except psycopg2.Error as e:  # pragma: no cover
            return error.db_operation_error(e)

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None and self.transaction_status:
                self.conn.commit()
            else:
                self.conn.rollback()
        except psycopg2.Error as e:   # pragma: no cover
            self.conn.rollback()
            return error.db_operation_error(e)
        finally:
            self.transaction_status = False
            self.conn.reset()  # 重置连接状态

    def commit(self):
        try:
            if self.transaction_status:
                self.conn.commit()
                self.transaction_status = False
        except psycopg2.Error as e:   # pragma: no cover
            return error.db_operation_error(e)
        
    def rollback(self):
        try:
            if self.transaction_status:
                self.conn.rollback()
                self.transaction_status = False
        except psycopg2.Error as e:
            return error.db_operation_error(e) 