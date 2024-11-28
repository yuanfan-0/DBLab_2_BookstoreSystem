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
            user_doc = {
                "user_id": user_id,
                "password": password,
                "balance": 0,
                "token": token,
                "terminal": terminal
            }
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
        user_doc = self.db.user.find_one({"user_id": user_id})
        if user_doc is None:
            return error.error_authorization_fail()
        db_token = user_doc.get("token")
        if not self.__check_token(user_id, db_token, token):
            return error.error_authorization_fail()
        return 200, "ok"

    def check_password(self, user_id: str, password: str) -> (int, str): # type: ignore
        user_doc = self.db.user.find_one({"user_id": user_id})
        if user_doc is None:
            return error.error_authorization_fail()
        
        if password != user_doc.get("password"):
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
            return 528, "{}".format(str(e)), ""
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
            return 528, "{}".format(str(e))
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
            return 528, "{}".format(str(e))
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
            return 528, "{}".format(str(e))
        return 200, "ok"