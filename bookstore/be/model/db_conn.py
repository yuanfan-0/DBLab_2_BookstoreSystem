from be.model import store
import logging

class DBConn:
    def __init__(self):
        self.conn, self.mongodb = store.get_db_conn()

    def user_id_exist(self, user_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT user_id FROM \"user\" WHERE user_id = %s;", (user_id,)  # user 是保留关键字，需要标识表名
            )
            row = cursor.fetchone()
            cursor.close()
            return row is not None
        except Exception as e:
            logging.error(f"Error checking user_id existence: {e}")
            return False

    def book_id_exist(self, store_id, book_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT book_id FROM store WHERE store_id = %s AND book_id = %s;",
                (store_id, book_id),
            )
            row = cursor.fetchone()
            cursor.close()
            return row is not None
        except Exception as e:
            logging.error(f"Error checking book_id existence: {e}")
            return False

    def store_id_exist(self, store_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT store_id FROM user_store WHERE store_id = %s;", (store_id,)
            )
            row = cursor.fetchone()
            cursor.close()
            return row is not None
        except Exception as e:
            logging.error(f"Error checking store_id existence: {e}")
            return False

    def order_id_exist(self, order_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT order_id FROM new_order WHERE order_id = %s;", (order_id,)
            )
            row = cursor.fetchone()
            cursor.close()
            return row is not None
        except Exception as e:
            logging.error(f"Error checking order_id existence: {e}")
            return False