import os
import random
import base64
import simplejson as json
from pymongo import MongoClient
from bson.binary import Binary
import psycopg2

class Book:
    id: str
    title: str
    author: str
    publisher: str
    original_title: str
    translator: str
    pub_year: str
    pages: int
    price: int
    currency_unit: str
    binding: str
    isbn: str
    author_intro: str
    book_intro: str
    content: str
    tags: list
    pictures: list

    def __init__(self):
        self.tags = []
        self.pictures = []


class BookDB:
    def __init__(self, large: bool = False):
        # 连接到MongoDB
        self.mongo_client = MongoClient('mongodb://localhost:27017/')
        self.mongo_db = self.mongo_client['bookstore']
        self.mongo_collection = self.mongo_db['books']

        # 连接到PostgreSQL
        self.pg_conn = psycopg2.connect(
            dbname="bookstore",
            user="postgres",
            password="123456",
            host="localhost",
            port="5432"
        )
        self.pg_cursor = self.pg_conn.cursor()

    def get_book_count(self):
        self.pg_cursor.execute("SELECT COUNT(*) FROM books")
        count = self.pg_cursor.fetchone()[0]
        return count

    def get_book_info(self, start, size):
        books = []
        # 从PostgreSQL中获取书籍信息
        self.pg_cursor.execute("""
            SELECT id, title, author, publisher, original_title, translator, pub_year, pages, price, currency_unit, binding, isbn, author_intro, book_intro, content, tags
            FROM books
            ORDER BY id
            OFFSET %s LIMIT %s
        """, (start, size))

        print(f"back_start: {start}, back_size: {size}")
        rows = self.pg_cursor.fetchall()
        print(f"back_rows: {len(rows)}") 

        for row in rows:
            book = Book()
            book.id = row[0]
            book.title = row[1]
            book.author = row[2]
            book.publisher = row[3]
            book.original_title = row[4]
            book.translator = row[5]
            book.pub_year = row[6]
            book.pages = row[7]
            book.price = row[8]
            book.currency_unit = row[9]
            book.binding = row[10]
            book.isbn = row[11]
            book.author_intro = row[12]
            book.book_intro = row[13]
            book.content = row[14]
            book.tags = row[15]

            # 从MongoDB中获取图片数据
            mongo_row = self.mongo_collection.find_one({"id": book.id})
            if mongo_row:
                picture_binary = mongo_row.get('picture')
                picture_base64 = base64.b64encode(picture_binary).decode('utf-8')
                book.pictures.append(picture_base64)

            books.append(book)

        return books

    def close(self):
        self.mongo_client.close()
        self.pg_cursor.close()
        self.pg_conn.close()