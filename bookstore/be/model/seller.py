import logging
from be.model import error
from be.model import db_conn

class Seller(db_conn.DBConn):
    def __init__(self):
        super().__init__()

    def add_book(
        self,
        user_id: str,
        store_id: str,
        book_id: str,
        book_json_str: str,
        stock_level: int,
    ):
        try:
            # 检查用户是否存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            # 检查商店是否存在
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            # 检查书籍是否已经存在
            if self.book_id_exist(store_id, book_id):
                return error.error_exist_book_id(book_id)

            # 将书籍插入到 store 表中
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO store (store_id, book_id, book_info, stock_level) "
                "VALUES (%s, %s, %s, %s)",
                (store_id, book_id, book_json_str, stock_level),
            )
            self.conn.commit()
            cursor.close()
        except Exception as e:
            logging.error(f"Error adding book: {str(e)}")
            return 530, "{}".format(str(e))
        return 200, "ok"

    def add_stock_level(
        self, 
        user_id: str, 
        store_id: str, 
        book_id: str, 
        add_stock_level: int
    ):
        try:
            # 检查用户、商店和书籍是否存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            if not self.book_id_exist(store_id, book_id):
                return error.error_non_exist_book_id(book_id)

            # 更新库存数量
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE store SET stock_level = stock_level + %s "
                "WHERE store_id = %s AND book_id = %s",
                (add_stock_level, store_id, book_id),
            )
            self.conn.commit()
            cursor.close()
        except Exception as e:
            logging.error(f"Error adding stock level: {str(e)}")
            return 530, "{}".format(str(e))
        return 200, "ok"

    def create_store(self, user_id: str, store_id: str) -> (int, str): # type: ignore
        try:
            # 检查用户是否存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            # 检查商店是否已经存在
            if self.store_id_exist(store_id):
                return error.error_exist_store_id(store_id)

            # 创建商店，插入到 user_store 表中
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO user_store (store_id, user_id) "
                "VALUES (%s, %s)",
                (store_id, user_id),
            )
            self.conn.commit()
            cursor.close()
        except Exception as e:
            logging.error(f"Error creating store: {str(e)}")
            return 530, "{}".format(str(e))
        return 200, "ok"

    def ship(
            self,
            user_id: str,
            store_id: str,
            order_id: str,
            ):
        try:
            # 检查用户是否存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            # 检查商店是否存在
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            # 检查订单是否存在
            if not self.order_id_exist(order_id):
                return error.error_invalid_order_id(order_id)
            # 检查订单是否已经支付
            if not self.order_is_paid(order_id):
                return error.error_not_be_paid(order_id)
            # 检查订单是否已经发货
            if self.order_is_shipped(order_id):
                return error.error_order_is_shipped(order_id)
            # 更新订单状态
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE new_order SET is_shipped = TRUE "
                "WHERE order_id = %s AND store_id = %s",
                (order_id, store_id),
            )
            self.conn.commit()
            cursor.close()
        except Exception as e:
            logging.error(f"Error shipping order: {str(e)}")
            return 520, "{}".format(str(e))
        return 200, "ok"

    def query_one_store_orders(self, user_id: str, store_id: str, password) -> (int, str, list): # type: ignore
        try:
            # 检查用户与商店是否存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + ("None",)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id) + ("None",)
            
            # 检查用户密码是否正确
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT password FROM \"user\" WHERE user_id = %s",
                (user_id,),
            )
            user = cursor.fetchone()
            cursor.close()
            if user is None or user['password'] != password:
                return error.error_authorization_fail() + ("None",)

            # 查找用户是否存在该商店
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT * FROM user_store WHERE user_id = %s AND store_id = %s",
                (user_id, store_id),
            )
            user_store = cursor.fetchone()
            cursor.close()
            if user_store is None:
                return error.error_no_store_found(user_id) + ("None",)

            # 查找该商店的所有订单
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT * FROM new_order WHERE store_id = %s",
                (store_id,),
            )
            orders = cursor.fetchall()
            cursor.close()
        except Exception as e:
            logging.error(f"Error querying store orders: {str(e)}")
            return 530, "{}".format(str(e)), "None"
        return 200, "ok", str(orders)

    def query_all_store_orders(self, user_id: str, password) -> (int, str, list): # type: ignore
        try:
            # 检查用户是否存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + ("None",)

            # 检查用户密码是否正确
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT password FROM \"user\" WHERE user_id = %s",
                (user_id,),
            )
            user = cursor.fetchone()
            cursor.close()
            if user is None or user['password'] != password:
                return error.error_authorization_fail() + ("None",)

            # 查找用户的商店
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT store_id FROM user_store WHERE user_id = %s",
                (user_id,),
            )
            user_stores = cursor.fetchall()
            cursor.close()

            # 检查是否有商店
            if len(user_stores) == 0:
                return error.error_no_store_found(user_id) + ("None",)

            all_store_orders = {}
            for user_store in user_stores:
                store_id = user_store['store_id']
                # 查找该商店的所有订单
                cursor = self.conn.cursor()
                cursor.execute(
                    "SELECT * FROM new_order WHERE store_id = %s",
                    (store_id,),
                )
                orders = cursor.fetchall()
                cursor.close()
                all_store_orders[store_id] = orders

        except Exception as e:
            logging.error(f"Error querying all store orders: {str(e)}")
            return 530, "{}".format(str(e)), "None"
        return 200, "ok", str(all_store_orders)