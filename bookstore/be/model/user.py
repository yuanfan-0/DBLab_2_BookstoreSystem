import jwt
import time
import logging
from be.model import error
from be.model import db_conn

# encode a json string like:
#   {
#       "user_id": [user name],
#       "terminal": [terminal code],
#       "timestamp": [ts]} to a JWT
#   }


def jwt_encode(user_id: str, terminal: str) -> str:
    encoded = jwt.encode(
        {"user_id": user_id, "terminal": terminal, "timestamp": time.time()},
        key=user_id,
        algorithm="HS256",
    )
    return encoded


# decode a JWT to a json string like:
#   {
#       "user_id": [user name],
#       "terminal": [terminal code],
#       "timestamp": [ts]} to a JWT
#   }
def jwt_decode(encoded_token, user_id: str) -> str:
    decoded = jwt.decode(encoded_token, key=user_id, algorithms="HS256")
    return decoded


class User(db_conn.DBConn):
    token_lifetime: int = 3600  # 3600 seconds

    def __init__(self):
        super().__init__()

    def __check_token(self, user_id, db_token, token) -> bool:
        try:
            if db_token != token:
                return False
            jwt_text = jwt_decode(encoded_token=token, user_id=user_id)
            ts = jwt_text["timestamp"]
            if ts is not None:
                now = time.time()
                if self.token_lifetime > now - ts >= 0:
                    return True
        except jwt.exceptions.InvalidSignatureError as e:
            logging.error(str(e))
            return False

    def register(self, user_id: str, password: str):
        try:
            # 检查是否已经存在相同的 user_id
            if self.user_id_exist(user_id):
                return error.error_exist_user_id(user_id)

            terminal = "terminal_{}".format(str(time.time()))
            token = jwt_encode(user_id, terminal)

            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO \"user\" (user_id, password, balance, token, terminal) VALUES (%s, %s, %s, %s, %s)",
                (user_id, password, 0, token, terminal)
            )
            self.conn.commit()
            cursor.close()
        except Exception as e:
            logging.error(f"Error during registration: {str(e)}")
            return error.error_exist_user_id(user_id)
        return 200, "ok"

    def check_token(self, user_id: str, token: str) -> (int, str): # type: ignore

        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT token FROM \"user\" WHERE user_id = %s",
            (user_id,),
        )
        row = cursor.fetchone()
        cursor.close()

        if row is None:
            return error.error_authorization_fail()

        db_token = row[0]
        if not self.__check_token(user_id, db_token, token):
            return error.error_authorization_fail()

        return 200, "ok"

    def check_password(self, user_id: str, password: str) -> (int, str): # type: ignore

        # 检查用户密码是否正确
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT password FROM \"user\" WHERE user_id = %s",
            (user_id,),
        )
        row = cursor.fetchone()
        cursor.close()

        if row is None:
            return error.error_authorization_fail()

        if row[0] != password:
            return error.error_authorization_fail()

        return 200, "ok"

    def login(self, user_id: str, password: str, terminal: str) -> (int, str, str): # type: ignore
        token = ""
        try:
            code, message = self.check_password(user_id, password)
            if code != 200:
                return code, message, ""

            token = jwt_encode(user_id, terminal)
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE \"user\" SET token = %s, terminal = %s WHERE user_id = %s",
                (token, terminal, user_id)
            )
            self.conn.commit()
            cursor.close()
            if cursor.rowcount == 0:
                return error.error_authorization_fail() + ("",)
        except Exception as e:
            return 530, "{}".format(str(e)), ""
        return 200, "ok", token
 
    def logout(self, user_id: str, token: str) -> (int, str): # type: ignore
        try:
            code, message = self.check_token(user_id, token)
            if code != 200:
                return code, message

            terminal = "terminal_{}".format(str(time.time()))
            dummy_token = jwt_encode(user_id, terminal)

            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE \"user\" SET token = %s, terminal = %s WHERE user_id = %s",
                (dummy_token, terminal, user_id)
            )
            self.conn.commit()
            cursor.close()
            if cursor.rowcount == 0:
                return error.error_authorization_fail()
        except Exception as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def unregister(self, user_id: str, password: str) -> (int, str): # type: ignore
        try:
            code, message = self.check_password(user_id, password)
            if code != 200:
                return code, message

            cursor = self.conn.cursor()
            cursor.execute(
                "DELETE FROM \"user\" WHERE user_id = %s",
                (user_id,)
            )
            self.conn.commit()
            cursor.close()
            if cursor.rowcount == 0:
                return error.error_authorization_fail()
        except Exception as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def change_password(
        self, user_id: str, old_password: str, new_password: str
    ) -> (int, str): # type: ignore
        try:
            code, message = self.check_password(user_id, old_password)
            if code != 200:
                return code, message

            terminal = "terminal_{}".format(str(time.time()))
            token = jwt_encode(user_id, terminal)
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE \"user\" SET password = %s, token = %s, terminal = %s WHERE user_id = %s",
                (new_password, token, terminal, user_id)
            )
            self.conn.commit()
            cursor.close()
            if cursor.rowcount == 0:
                return error.error_authorization_fail()
        except Exception as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def search_books(self, keyword, search_scope="all", search_in_store=False, store_id=None):
        try:
            if search_in_store:
                return self._search_in_store(keyword, search_scope, store_id)
            else:
                return self._search_global(keyword, search_scope)
        except Exception as e:
            logging.error(f"Search error: {e}")
            return 530, "搜索失败"

    def _search_global(self, keyword, search_scope):
        try:
            cursor = self.conn.cursor()
            if search_scope == "all":
                # 在所有相关字段中搜索
                cursor.execute(
                    """
                    SELECT * FROM books 
                    WHERE title ILIKE %s 
                       OR author ILIKE %s
                       OR publisher ILIKE %s
                       OR original_title ILIKE %s
                       OR translator ILIKE %s
                       OR author_intro ILIKE %s
                       OR book_intro ILIKE %s
                       OR content ILIKE %s
                       OR tags ILIKE %s
                    """,
                    tuple(['%' + keyword + '%'] * 9)
                )
            elif search_scope == "title":
                # 只在标题中搜索
                cursor.execute(
                    "SELECT * FROM books WHERE title ILIKE %s",
                    ('%' + keyword + '%',)
                )
            elif search_scope == "author":
                # 只在作者中搜索
                cursor.execute(
                    "SELECT * FROM books WHERE author ILIKE %s",
                    ('%' + keyword + '%',)
                )
            elif search_scope == "tags":
                # 只在标签中搜索
                cursor.execute(
                    "SELECT * FROM books WHERE tags ILIKE %s",
                    ('%' + keyword + '%',)
                )
            elif search_scope == "content":
                # 在内容介绍中搜索
                cursor.execute(
                    """
                    SELECT * FROM books 
                    WHERE book_intro ILIKE %s 
                       OR content ILIKE %s
                    """,
                    ('%' + keyword + '%', '%' + keyword + '%')
                )
            
            results = cursor.fetchall()
            cursor.close()
            
            if not results:
                return error.error_book_not_found(keyword)
            
            return 200, results

        except Exception as e:
            logging.error(f"Global search error: {e}")
            return 530, "全局搜索失败"

    def _search_in_store(self, keyword, search_scope, store_id):
        try:
            if not self.store_id_exist(store_id):
                return error.error_store_not_found(store_id)

            cursor = self.conn.cursor()
            if search_scope == "all":
                cursor.execute(
                    """
                    SELECT b.* 
                    FROM books b
                    JOIN store s ON b.id = s.book_id
                    WHERE s.store_id = %s 
                    AND (
                        b.title ILIKE %s 
                        OR b.author ILIKE %s
                        OR b.publisher ILIKE %s
                        OR b.original_title ILIKE %s
                        OR b.translator ILIKE %s
                        OR b.author_intro ILIKE %s
                        OR b.book_intro ILIKE %s
                        OR b.content ILIKE %s
                        OR b.tags ILIKE %s
                    )
                    """,
                    (store_id,) + tuple(['%' + keyword + '%'] * 9)
                )
            else:
                # 根据特定scope在店铺内搜索
                search_field = search_scope.lower()
                if search_field in ['title', 'author', 'tags', 'content']:
                    cursor.execute(
                        f"""
                        SELECT b.* 
                        FROM books b
                        JOIN store s ON b.id = s.book_id
                        WHERE s.store_id = %s 
                        AND b.{search_field} ILIKE %s
                        """,
                        (store_id, '%' + keyword + '%')
                    )

            results = cursor.fetchall()
            cursor.close()

            if not results:
                return error.error_book_not_found_in_the_store(keyword, store_id)

            return 200, results

        except Exception as e:
            logging.error(f"Store search error: {e}")
            return 530, "店铺内搜索失败"