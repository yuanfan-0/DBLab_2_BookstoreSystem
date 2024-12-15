import pytest
from fe.access.new_buyer import register_new_buyer
from fe.access.book import Book
from fe.test.gen_book_data import GenBook
from fe.access.new_seller import register_new_seller
import uuid


class TestSearch:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        self.seller_id = "test_search_seller_id_{}".format(str(uuid.uuid1()))
        self.store_id = "test_search_store_id_{}".format(str(uuid.uuid1()))
        self.buyer_id = "test_search_buyer_id_{}".format(str(uuid.uuid1()))
        self.password = self.seller_id
        
        self.buyer = register_new_buyer(self.buyer_id, self.password)
        
        # 生成测试用书籍数据
        self.gen_book = GenBook(self.seller_id, self.store_id)
        self.seller = self.gen_book.seller

        self.books = self.gen_book.gen(
            non_exist_book_id=False, 
            low_stock_level=False,
            max_book_count=5  # 生成5本测试书
        )

        yield

        
    # 获取商店书籍信息
    def get_store_books_info(self):
        books_info = []
        for book_info, _ in self.gen_book.buy_book_info_list:
            book_detail = {
                'title': book_info.title,
                'author': book_info.author,
                'publisher': book_info.publisher,
                'book_id': book_info.id,
                'tags': book_info.tags
            }
            books_info.append(book_detail)
        return books_info

    # 买家搜索测试
    def test_buyer_global_search(self):
        code, books = self.buyer.search_books(
            keyword="美丽心灵",
            search_scope="all"
        )
        assert code == 200
        assert len(books) > 0

    def test_buyer_store_search(self):
        search_books = self.get_store_books_info()
        for book in search_books:
            code, books = self.buyer.search_books(
                keyword=book['title'],
                search_scope="all",
                search_in_store=True,
                store_id=self.store_id
            )
            assert code == 200
            assert len(books) > 0

    # 卖家搜索测试
    def test_seller_global_search(self):
        code, books = self.seller.search_books(
            keyword="美丽心灵",
            search_scope="all"
        )
        assert code == 200
        assert len(books) > 0

    def test_seller_store_search(self):
        search_books = self.get_store_books_info()
        for book in search_books:
            code, books = self.seller.search_books(
                keyword=book['title'],
                search_scope="all",
                search_in_store=True,
                store_id=self.store_id
            )
            assert code == 200
            assert len(books) > 0

    # 不同搜索范围测试
    def test_search_by_title(self):
        # 买家搜索
        code, books = self.buyer.search_books(
            keyword="美丽心灵",
            search_scope="title"
        )
        assert code == 200
        assert len(books) > 0
        
        # 卖家搜索
        code, books = self.seller.search_books(
            keyword="美丽心灵",
            search_scope="title"
        )
        assert code == 200
        assert len(books) > 0

    def test_search_by_tags(self):
        # 买家搜索
        code, books = self.buyer.search_books(
            keyword="传记",
            search_scope="tags"
        )
        assert code == 200
        assert len(books) > 0
        
        # 卖家搜索
        code, books = self.seller.search_books(
            keyword="传记",
            search_scope="tags"
        )
        assert code == 200
        assert len(books) > 0

    # 错误情况测试
    def test_search_non_exist(self):
        # 买家搜索不存在的内容
        code, _ = self.buyer.search_books(
            keyword="non_exist_keyword_xxxxx",
            search_scope="all"
        )
        assert code != 200
        
        # 卖家搜索不存在的内容
        code, _ = self.seller.search_books(
            keyword="non_exist_keyword_xxxxx",
            search_scope="all"
        )
        assert code != 200

    def test_search_invalid_store(self):
        # 买家搜索不存在的商店
        code, _ = self.buyer.search_books(
            keyword="test",
            search_scope="all",
            search_in_store=True,
            store_id="non_exist_store_id"
        )
        assert code != 200
        
        # 卖家搜索不存在的商店
        code, _ = self.seller.search_books(
            keyword="test",
            search_scope="all",
            search_in_store=True,
            store_id="non_exist_store_id"
        )
        assert code != 200

