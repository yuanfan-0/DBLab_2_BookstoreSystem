from be.model import error
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_READ_COMMITTED

class DBTransaction:
    def __init__(self, db_conn):
        self.conn = db_conn.conn
        self.transaction_status = False
        
    def __enter__(self):
        try:
            # 设置隔离级别为读已提交
            self.conn.set_isolation_level(ISOLATION_LEVEL_READ_COMMITTED)
            # 开始事务
            self.transaction_status = True
            return self
        except psycopg2.Error as e:
            return error.db_operation_error(e)

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None and self.transaction_status:
                # 如果没有异常发生，提交事务
                self.conn.commit()
            else:
                # 如果有异常发生，回滚事务
                self.conn.rollback()
        except psycopg2.Error as e:
            self.conn.rollback()
            return error.db_operation_error(e)
        finally:
            self.transaction_status = False

    def commit(self):
        try:
            if self.transaction_status:
                self.conn.commit()
                self.transaction_status = False
        except psycopg2.Error as e:
            return error.db_operation_error(e)

    def rollback(self):
        try:
            if self.transaction_status:
                self.conn.rollback()
                self.transaction_status = False
        except psycopg2.Error as e:
            return error.db_operation_error(e) 