import sqlite3
from pymongo import MongoClient
from bson.binary import Binary
import psycopg2

# 连接到SQLite数据库
sqlite_conn = sqlite3.connect('./fe/data/book.db')
sqlite_cursor = sqlite_conn.cursor()

# 连接到MongoDB数据库
mongo_client = MongoClient('mongodb://localhost:27017/')
mongo_db = mongo_client['bookstore'] 
mongo_collection = mongo_db['books']

# 连接到PostgreSQL数据库
pg_conn = psycopg2.connect(
    dbname="bookstore",
    user="postgres",
    password="123456",
    host="localhost",
    port="5432"
)
pg_cursor = pg_conn.cursor()

# 创建PostgreSQL表（如果表不存在）
pg_cursor.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id TEXT PRIMARY KEY,
        title TEXT,
        author TEXT,
        publisher TEXT,
        original_title TEXT,
        translator TEXT,
        pub_year TEXT,
        pages INTEGER,
        price INTEGER,
        currency_unit TEXT,
        binding TEXT,
        isbn TEXT,
        author_intro TEXT,
        book_intro TEXT,
        content TEXT,
        tags TEXT
    )
""")
pg_conn.commit()

# 从SQLite中查询book表的所有记录
sqlite_cursor.execute("SELECT * FROM book")
rows = sqlite_cursor.fetchall()

# 遍历每一行并插入到MongoDB和PostgreSQL中
for row in rows:
    # 插入到MongoDB中
    mongo_data = {
        'id': row[0],
        'picture': Binary(row[16])  # 将BLOB数据转为Binary
    }
    mongo_collection.insert_one(mongo_data)

    # 插入到PostgreSQL中
    pg_cursor.execute("""
        INSERT INTO books (
            id, title, author, publisher, original_title, translator, pub_year, pages, price, currency_unit, binding, isbn, author_intro, book_intro, content, tags
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
    """, (
        row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], int(row[8]), row[9], row[10], row[11], row[12], row[13], row[14], row[15]
    ))
    pg_conn.commit()

# 关闭数据库连接
sqlite_conn.close()
mongo_client.close()
pg_conn.close()

print("数据迁移完成！")