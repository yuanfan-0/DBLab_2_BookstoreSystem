## 搜索功能
### URL：
OST http://[address]/search
### Request
#### Header:
key | 类型 | 描述 | 是否可为空
--|---|---|---
oken | string | 登录产生的会话标识 | N
#### Body:
``json

 "keyword": "search_keyword",
 "search_scope": "all",
 "search_in_store": false,
 "store_id": "store_id"

``
#### 属性说明：
变量名 | 类型 | 描述 | 是否可为空
--|---|---|---
eyword | string | 搜索关键词 | N
earch_scope | string | 搜索范围，可选值为 "all", "title", "author", "tags", "content" | Y
earch_in_store | boolean | 是否在特定商店内搜索 | Y
tore_id | string | 商店ID，仅在 `search_in_store` 为 `true` 时需要 | Y
### Response
Status Code:
码 | 描述
-- | ---
200 | 搜索成功
523 | 未找到相关书籍
524 | 商店ID不存在
530 | 搜索失败
#### Body:
``json

 "code": 200,
 "books": [
   {
     "id": "book_id",
     "title": "book_title",
     "author": "book_author",
     "publisher": "book_publisher",
     "original_title": "original_title",
     "translator": "translator",
     "pub_year": "pub_year",
     "pages": 123,
     "price": 1000,
     "currency_unit": "CNY",
     "binding": "binding",
     "isbn": "isbn",
     "author_intro": "author_intro",
     "book_intro": "book_intro",
     "content": "content",
     "tags": "tags"
   }
 ]

``
#### 属性说明：
变量名 | 类型 | 描述 | 是否可为空
--|---|---|---
d | string | 书籍ID | N
itle | string | 书籍标题 | N
uthor | string | 书籍作者 | N
ublisher | string | 出版社 | N
riginal_title | string | 原始标题 | Y
ranslator | string | 译者 | Y
ub_year | string | 出版年份 | Y
ages | integer | 页数 | Y
rice | integer | 价格，以分为单位 | Y
urrency_unit | string | 货币单位 | Y
inding | string | 装订类型 | Y
sbn | string | 国际标准书号 | Y
uthor_intro | string | 作者简介 | Y
ook_intro | string | 书籍简介 | Y
ontent | string | 内容 | Y
ags | string | 标签 | Y
### 对应测试代码
```python
ef test_buyer_global_search(self):
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
``
### 对应后端实现代码
```python
ef search_books(self, keyword, search_scope="all", search_in_store=False, store_id=None):
   try:
       if search_in_store:
           return self._search_in_store(keyword, search_scope, store_id)
       else:
           return self._search_global(keyword, search_scope)
   except Exception as e:
       logging.error(f"Search error: {e}")
       return 530, "搜索失败"
``
