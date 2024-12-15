import requests
from urllib.parse import urljoin
from fe.access import book
from fe.access.auth import Auth


class Seller:
    def __init__(self, url_prefix, seller_id: str, password: str):
        self.url_prefix = urljoin(url_prefix, "seller/")

        self.seller_id = seller_id
        self.password = password
        self.terminal = "my terminal"
        self.auth = Auth(url_prefix)
        code, self.token = self.auth.login(self.seller_id, self.password, self.terminal)
        assert code == 200

    def create_store(self, store_id):
        json = {
            "user_id": self.seller_id,
            "store_id": store_id,
        }
        # print(simplejson.dumps(json))
        url = urljoin(self.url_prefix, "create_store")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        return r.status_code

    def add_book(self, store_id: str, stock_level: int, book_info: book.Book) -> int:
        json = {
            "user_id": self.seller_id,
            "store_id": store_id,
            "book_info": book_info.__dict__,
            "stock_level": stock_level,
        }
        # print(simplejson.dumps(json))
        url = urljoin(self.url_prefix, "add_book")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        return r.status_code

    def add_stock_level(
        self, seller_id: str, store_id: str, book_id: str, add_stock_num: int
    ) -> int:
        json = {
            "user_id": seller_id,
            "store_id": store_id,
            "book_id": book_id,
            "add_stock_level": add_stock_num,
        }
        # print(simplejson.dumps(json))
        url = urljoin(self.url_prefix, "add_stock_level")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        return r.status_code

    def query_one_store_orders(self, seller_id: str, store_id: str, password):
        json = {
            "user_id": seller_id,
            "store_id": store_id,
            "password": password
        }

        url = urljoin(self.url_prefix, "query_one_store_orders")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        response_json = r.json()
        return response_json.get("code"), response_json.get("message"), response_json.get("orders")
    

    def query_all_store_orders(self, seller_id: str, password):
        json = {
            "user_id": seller_id,
            "password": password
        }

        url = urljoin(self.url_prefix, "query_all_store_orders")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        response_json = r.json()
        return response_json.get("code"), response_json.get("message"), response_json.get("orders")

    def ship(self, seller_id: str, store_id: str, order_id: str) -> (int, str):  # type: ignore
        json = {
            "user_id": seller_id,
            "store_id": store_id, 
            "order_id": order_id,
        }
        url = urljoin(self.url_prefix, "ship")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        response_json = r.json()
        code=response_json.get("code")
        return code
    
    def search_books(self, keyword: str, search_scope: str = "all", 
                    search_in_store: bool = False, store_id: str = None) -> (int, list): # type: ignore
        json = {
            "keyword": keyword,
            "search_scope": search_scope,
            "search_in_store": search_in_store,
            "store_id": store_id
        }
        url = urljoin(self.url_prefix, "search")
        r = requests.post(url, json=json)
        return r.status_code, r.json().get("books", [])
    
    def get_stock_level(self, store_id: str, book_id: str) -> (int, int): # type: ignore
        json = {
            "store_id": store_id,
            "book_id": book_id
        }
        url = urljoin(self.url_prefix, "get_stock_level")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        response_json = r.json()
        return response_json.get("code"), response_json.get("stock_level", -1)

    def add_stock_level_except(self, user_id: str, store_id: str, book_id: str, add_stock_level: int) -> int:
        # 模拟异常情况的方法
        json = {
            "user_id": user_id,
            "store_id": store_id,
            "book_id": book_id,
            "add_stock_level": add_stock_level
        }
        # 发送请求到会抛出异常的端点
        url = urljoin(self.url_prefix, "add_stock_level_except")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        return r.status_code

    def add_stock_level_delay(self, user_id: str, store_id: str, book_id: str, add_stock_level: int) -> int:
        # 模拟延迟提交的方法
        json = {
            "user_id": user_id,
            "store_id": store_id,
            "book_id": book_id,
            "add_stock_level": add_stock_level
        }
        # 发送请求到会延迟处理的端点
        url = urljoin(self.url_prefix, "add_stock_level_delay")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        return r.status_code