import uuid
import json
import logging
from datetime import datetime, timedelta
from be.model import db_conn
from be.model import error

class Buyer(db_conn.DBConn):
    ORDER_STATUS = {
        "pending": "待支付",
        "paid": "已支付",
        "shipped": "已发货",
        "received": "已收货",
        "completed": "已完成",
        "canceled": "已取消"
    }

    def __init__(self):
        super().__init__()

    def user_id_exist(self, user_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT user_id FROM \"user\" WHERE user_id = %s",
                (user_id,)
            )
            row = cursor.fetchone()
            cursor.close()
            return row is not None
        except Exception as e:
            logging.error(f"Error checking user_id existence: {e}")
            return False

    def store_id_exist(self, store_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT store_id FROM user_store WHERE store_id = %s",
                (store_id,)
            )
            row = cursor.fetchone()
            cursor.close()
            return row is not None
        except Exception as e:
            logging.error(f"Error checking store_id existence: {e}")
            return False

    def new_order(self, user_id: str, store_id: str, id_and_count: [(str, int)]) -> (int, str, str): # type: ignore
        order_id = ""
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + (order_id,)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id) + (order_id,)

            uid = "{}_{}_{}".format(user_id, store_id, str(uuid.uuid1()))

            cursor = self.conn.cursor()
            for book_id, count in id_and_count:
                cursor.execute(
                    "SELECT stock_level, book_info FROM store WHERE store_id = %s AND book_id = %s",
                    (store_id, book_id)
                )
                store_item = cursor.fetchone()
                if store_item is None:
                    return error.error_non_exist_book_id(book_id) + (order_id,)

                stock_level = store_item[0]
                book_info = json.loads(store_item[1])
                price = book_info.get("price")

                print("--------------------------------------------")

                print(f"stock_level:{stock_level}  count:{count}")
                print("--------------------------------------------")

                if stock_level < count:
                    return error.error_stock_level_low(book_id) + (order_id,)

                cursor.execute(
                    "UPDATE store SET stock_level = stock_level - %s WHERE store_id = %s AND book_id = %s",
                    (count, store_id, book_id)
                )

                cursor.execute(
                    "INSERT INTO new_order_detail (order_id, book_id, count, price) VALUES (%s, %s, %s, %s)",
                    (uid, book_id, count, price)
                )

            cursor.execute(
                "INSERT INTO new_order (order_id, store_id, user_id, is_paid, is_shipped, is_received, order_completed, status, created_time) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (uid, store_id, user_id, False, False, False, False, "pending", datetime.utcnow())
            )
            self.conn.commit()
            cursor.close()
            order_id = uid
        except Exception as e:
            logging.error(f"Error creating new order: {e}")
            return 530, "{}".format(str(e)), ""

        return 200, "ok", order_id

    def pay_to_platform(self, user_id: str, password: str, order_id: str) -> (int, str): # type: ignore
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT user_id, is_paid FROM new_order WHERE order_id = %s",
                (order_id,)
            )
            order = cursor.fetchone()
            if order is None:
                return error.error_invalid_order_id(order_id)

            buyer_id = order[0]

            if buyer_id != user_id:
                return error.error_authorization_fail()

            cursor.execute(
                "SELECT password, balance FROM \"user\" WHERE user_id = %s",
                (buyer_id,)
            )
            user = cursor.fetchone()
            if user is None or user[0] != password:
                return error.error_authorization_fail()

            if order[1]:
                return error.error_order_is_paid(order_id)

            cursor.execute(
                "SELECT count, price FROM new_order_detail WHERE order_id = %s",
                (order_id,)
            )
            order_details = cursor.fetchall()
            total_price = sum(detail[0] * detail[1] for detail in order_details)

            if user[1] < total_price:
                return error.error_not_sufficient_funds(order_id)

            cursor.execute(
                "UPDATE \"user\" SET balance = balance - %s WHERE user_id = %s",
                (total_price, buyer_id)
            )

            cursor.execute(
                "UPDATE new_order SET is_paid = TRUE WHERE order_id = %s",
                (order_id,)
            )
            self.conn.commit()
            cursor.close()
        except Exception as e:
            logging.error(f"Error paying to platform: {e}")
            return 530, "{}".format(str(e))

        return 200, "ok"

    def confirm_receipt_and_pay_to_seller(self, user_id: str, password: str, order_id: str) -> (int, str): # type: ignore
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT user_id, store_id, is_paid, is_received FROM new_order WHERE order_id = %s",
                (order_id,)
            )
            order = cursor.fetchone()

            buyer_id = order[0]

            if buyer_id != user_id:
                return error.error_authorization_fail()

            cursor.execute(
                "SELECT password FROM \"user\" WHERE user_id = %s",
                (buyer_id,)
            )
            user = cursor.fetchone()
            if user is None or user[0] != password:
                return error.error_authorization_fail()

            if not order[2]:
                return error.error_not_be_paid(order_id)

            if order[3]:
                return error.error_order_is_confirmed(order_id)

            store_id = order[1]

            cursor.execute(
                "SELECT user_id FROM user_store WHERE store_id = %s",
                (store_id,)
            )
            seller = cursor.fetchone()
            seller_id = seller[0]

            cursor.execute(
                "SELECT count, price FROM new_order_detail WHERE order_id = %s",
                (order_id,)
            )
            order_details = cursor.fetchall()
            total_price = sum(detail[0] * detail[1] for detail in order_details)

            cursor.execute(
                "UPDATE \"user\" SET balance = balance + %s WHERE user_id = %s",
                (total_price, seller_id)
            )

            cursor.execute(
                "UPDATE new_order SET is_received = TRUE, order_completed = TRUE WHERE order_id = %s",
                (order_id,)
            )
            self.conn.commit()
            cursor.close()
        except Exception as e:
            logging.error(f"Error confirming receipt and paying to seller: {e}")
            return 530, "{}".format(str(e))

        return 200, "ok"

    def add_funds(self, user_id, password, add_value) -> (int, str): # type: ignore
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT password FROM \"user\" WHERE user_id = %s",
                (user_id,)
            )
            user = cursor.fetchone()
            if user is None or user[0] != password:
                return error.error_authorization_fail()

            cursor.execute(
                "UPDATE \"user\" SET balance = balance + %s WHERE user_id = %s",
                (add_value, user_id)
            )
            self.conn.commit()
            cursor.close()
        except Exception as e:
            logging.error(f"Error adding funds: {e}")
            return 530, "{}".format(str(e))

        return 200, "ok"

    def query_order_status(self, user_id: str, order_id: str, password) -> (int, str, str):  # type: ignore
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + ("None",)

            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT password FROM \"user\" WHERE user_id = %s",
                (user_id,)
            )
            user = cursor.fetchone()
            if user[0] != password:
                return error.error_authorization_fail() + ("None",)

            cursor.execute(
                "SELECT status FROM new_order WHERE order_id = %s AND user_id = %s",
                (order_id, user_id)
            )
            order = cursor.fetchone()
            if order is None:
                return error.error_invalid_order_id(order_id) + ("None",)

            order_status = self.ORDER_STATUS[order[0]]
            cursor.close()
            return 200, "ok", order_status
        except Exception as e:
            logging.error(f"Error querying order status: {e}")
            return 530, "{}".format(str(e)) + ("None",)

    def query_buyer_all_orders(self, user_id: str, password) -> (int, str, list):   # type: ignore
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + ("None",)

            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT password FROM \"user\" WHERE user_id = %s",
                (user_id,)
            )
            user = cursor.fetchone()
            if user[0] != password:
                return error.error_authorization_fail() + ("None",)

            cursor.execute(
                "SELECT * FROM new_order WHERE user_id = %s",
                (user_id,)
            )
            orders = cursor.fetchall()
            cursor.close()
            return 200, "ok", str(orders)
        except Exception as e:
            logging.error(f"Error querying buyer all orders: {e}")
            return 530, "{}".format(str(e)), None

    def cancel_order(self, user_id: str, order_id: str, password) -> (int, str):   # type: ignore
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)

            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT password FROM \"user\" WHERE user_id = %s",
                (user_id,)
            )
            user = cursor.fetchone()
            if user[0] != password:
                return error.error_authorization_fail()

            cursor.execute(
                "SELECT is_paid, store_id FROM new_order WHERE order_id = %s AND user_id = %s",
                (order_id, user_id)
            )
            order = cursor.fetchone()
            if order is None:
                return error.error_invalid_order_id(order_id)

            if order[0]:
                return error.error_cannot_be_canceled(order_id)

            cursor.execute(
                "UPDATE new_order SET status = 'canceled' WHERE order_id = %s",
                (order_id,)
            )

            cursor.execute(
                "SELECT book_id, count FROM new_order_detail WHERE order_id = %s",
                (order_id,)
            )
            order_details = cursor.fetchall()
            for detail in order_details:
                cursor.execute(
                    "UPDATE store SET stock_level = stock_level + %s WHERE store_id = %s AND book_id = %s",
                    (detail[1], order[1], detail[0])
                )

            self.conn.commit()
            cursor.close()
        except Exception as e:
            logging.error(f"Error canceling order: {e}")
            return 530, "{}".format(str(e))

        return 200, "ok"

    def auto_cancel_expired_orders(self):
        try:
            now = datetime.utcnow()
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT order_id, created_time, store_id FROM new_order WHERE is_paid = FALSE"
            )
            pending_orders = cursor.fetchall()

            for order in pending_orders:
                created_time = order[1]
                time_diff = abs(now - created_time)

                if time_diff < timedelta(seconds=5):
                    order_id = order[0]
                    cursor.execute(
                        "UPDATE new_order SET status = 'canceled' WHERE order_id = %s",
                        (order_id,)
                    )

                    cursor.execute(
                        "SELECT book_id, count FROM new_order_detail WHERE order_id = %s",
                        (order_id,)
                    )
                    order_details = cursor.fetchall()
                    for detail in order_details:
                        cursor.execute(
                            "UPDATE store SET stock_level = stock_level + %s WHERE store_id = %s AND book_id = %s",
                            (detail[1], order[2], detail[0])
                        )

            self.conn.commit()
            cursor.close()
        except Exception as e:
            logging.error(f"Error auto canceling expired orders: {e}")
            return 530, "not"

        return 200, "ok"