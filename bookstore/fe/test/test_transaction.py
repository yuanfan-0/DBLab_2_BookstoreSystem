import pytest
from fe.test.gen_book_data import GenBook
from fe.access.new_buyer import register_new_buyer
import uuid
import threading
import time
import logging

class TestTransaction:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        self.seller_id = "test_transaction_seller_{}".format(str(uuid.uuid1()))
        self.store_id = "test_transaction_store_{}".format(str(uuid.uuid1()))
        self.buyer_id = "test_transaction_buyer_{}".format(str(uuid.uuid1()))
        self.password = self.seller_id
        self.buyer = register_new_buyer(self.buyer_id, self.password)
        
        # 生成测试用书籍数据
        self.gen_book = GenBook(self.seller_id, self.store_id)
        self.seller = self.gen_book.seller

        self.book_id_stock_level=self.gen_book.book_id_stock_level

        # 生成10-20本测试书
        ok, buy_book_id_list = self.gen_book.gen(
            non_exist_book_id=False, 
            low_stock_level=False,
            max_book_count=20
        )
        assert ok
        assert len(buy_book_id_list) >= 10
        self.buy_book_id_list = buy_book_id_list

        yield
    

    def test_transaction_atomicity(self):
        """测试事务的原子性：一个事务中的所有操作要么全部完成，要么全部不完成"""
        # 使用第一本书
        book_id = self.buy_book_id_list[0][0]
        code, book_stock = self.seller.get_stock_level(self.store_id, book_id)
        assert code == 200
        
        # 添加库存，但在更新过程中模拟异常
        try:
            self.seller.add_stock_level_except(self.seller_id, self.store_id, book_id, 10)
            assert False  # 如果没有抛出异常，测试失败
        except Exception:
            pass
        
        # 验证库存是否保持原值（事务回滚）
        code, stock_level = self.seller.get_stock_level(self.store_id, book_id)
        assert code == 200
        assert stock_level == book_stock  # 库存应该保持原值

    def test_transaction_isolation(self):
        """测试事务隔离性：读已提交级别下，一个事务不能读取另一个未提交事务的数据"""
        book_id = self.buy_book_id_list[1][0]
        assert len(self.book_id_stock_level) > 0
        code, book_stock = self.seller.get_stock_level(self.store_id, book_id)
        assert code == 200
        print(f"book_stock: {book_stock}")

        def update_stock():
            seller = self.seller
            status = seller.get_thread_local_conn(self.store_id)
            assert status
            code, thread_book_stock = seller.get_stock_level(self.store_id, book_id)
            print(f"thread_book_stock: {thread_book_stock}")
            status_code = seller.add_stock_level_delay(self.seller_id, self.store_id, book_id, 10)
            code, new_thread_book_stock = seller.get_stock_level(self.store_id, book_id)
            print(f"new_thread_book_stock: {new_thread_book_stock}")
            assert status_code == 200

        # 启动更新线程
        update_thread = threading.Thread(target=update_stock)
        update_thread.start()
        time.sleep(0.1)  # 等待更新操作开始

        # 在主线程中读取库存
        code, stock_level = self.seller.get_stock_level(self.store_id, book_id)
        assert code == 200
        assert stock_level == book_stock  # 在更新提交前应该读到原始值

        update_thread.join()
        time.sleep(0.1)  # 等待事务完全提交

        # 更新提交后再次读取
        code, stock_level = self.seller.get_stock_level(self.store_id, book_id)
        assert code == 200
        assert stock_level == (book_stock + 10)  # 更新提交后应该能读到新值

    def test_concurrent_operations(self):
        """测试并发操作下的事务行为"""
        # 使用第三本书
        book_id = self.buy_book_id_list[2][0]
        code, book_stock = self.seller.get_stock_level(self.store_id, book_id)
        assert code == 200

        # 重置初始库存为100
        code = self.seller.add_stock_level(self.seller_id, self.store_id, book_id, 100-book_stock)
        assert code == 200

        # 确认初始库存设置成功
        code, initial_stock = self.seller.get_stock_level(self.store_id, book_id)
        assert initial_stock == 100

        # 预先创建买家账户
        buyers = []
        for i in range(5):
            buyer_id = f"concurrent_buyer_{i}_{str(uuid.uuid1())}"
            buyer = register_new_buyer(buyer_id, self.password)
            buyers.append(buyer)

        def concurrent_purchase(buyer):
            try:
                status = buyer.get_thread_local_conn()
                assert status
                code, _ = buyer.new_order(self.store_id, [(book_id, 10)])
                assert code == 200
                return code == 200
            except Exception as e:
                logging.error(f"Error in concurrent purchase: {e}")
                return False

        # 创建并发线程
        threads = []
        results = []
        for buyer in buyers:
            thread = threading.Thread(
                target=lambda b=buyer: results.append(concurrent_purchase(b))
            )
            threads.append(thread)

        # 启动所有线程
        for thread in threads:
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 打印results
        print("并发购买结果:", results)
  

        # 验证最终库存
        code, final_stock = self.seller.get_stock_level(self.store_id, book_id)
        assert code == 200
        assert final_stock == 50

    def test_rollback_on_error(self):
        """测试异常情况下的事务回滚"""
        
        # 使用第四本书
        book_id = self.buy_book_id_list[3][0]

        code, book_stock = self.seller.get_stock_level(self.store_id, book_id)
        assert code == 200

        # 设置初始库存
        code = self.seller.add_stock_level(self.seller_id, self.store_id, book_id, 100-book_stock)
        assert code == 200

        # 尝试购买超出库存的数量
        code, _ = self.buyer.new_order(self.store_id, [(book_id, 150)])
        assert code != 200  # 应该失败

        # 验证库存是否保持不变（回滚）
        code, stock_level = self.seller.get_stock_level(self.store_id, book_id)
        assert code == 200
        assert stock_level == 100  # 库存应该保持不变
  