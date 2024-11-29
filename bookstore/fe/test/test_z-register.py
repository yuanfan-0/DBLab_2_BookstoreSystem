import time
import pytest
from fe.access import auth
from fe import conf
from be.model.store import Store

class TestRegister:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        # 每次测试运行前生成唯一的 user_id 和 password
        self.user_id = "test_register_user_{}".format(time.time())
        self.password = "test_register_password_{}".format(time.time())
        self.auth = auth.Auth(conf.URL)
        
        # 清空数据库中的用户数据
        self.store = Store()
        self.clear_database()
        
        yield

        # 测试结束后再次清空数据库
        self.clear_database()

    def clear_database(self):
        # 清空 PostgreSQL 测试数据
        self.store.pg_cursor.execute("DELETE FROM \"user\"")
        self.store.pg_cursor.execute("DELETE FROM store")
        self.store.pg_cursor.execute("DELETE FROM new_order")
        self.store.pg_cursor.execute("DELETE FROM new_order_detail")
        self.store.pg_conn.commit()

        # 清空 MongoDB 中的用户数据
        self.store.mongodb['user'].delete_many({})

    def test_register_ok(self):
        code = self.auth.register(self.user_id, self.password)
        assert code == 200

    def test_unregister_ok(self):
        code = self.auth.register(self.user_id, self.password)
        assert code == 200

        code = self.auth.unregister(self.user_id, self.password)
        assert code == 200

    def test_unregister_error_authorization(self):
        code = self.auth.register(self.user_id, self.password)
        assert code == 200

        code = self.auth.unregister(self.user_id + "_x", self.password)
        assert code != 200

        code = self.auth.unregister(self.user_id, self.password + "_x")
        assert code != 200

    def test_register_error_exist_user_id(self):
        code = self.auth.register(self.user_id, self.password)
        assert code == 200

        code = self.auth.register(self.user_id, self.password)
        assert code != 200