import logging
import os
import threading
import psycopg2
from pymongo import MongoClient

import threading

class Store:
    def __init__(self, postgredb_url="postgresql://postgres:123456@localhost:5432/bookstore", mongodb_url="mongodb://localhost:27017/", db_name="bookstore"):
        # 初始化线程本地存储
        self.thread_local = threading.local()

        # 连接 PostgreSQL 数据库
        self.postgredb_url = postgredb_url
        self.pg_conn = psycopg2.connect(postgredb_url)
        self.pg_cursor = self.pg_conn.cursor()

        # 初始化 PostgreSQL 表
        self.init_tables()
        # 初始化 PostgreSQL 索引
        self.init_indexes()

        # 连接 MongoDB 数据库
        self.client = MongoClient(mongodb_url)
        self.mongodb = self.client[db_name]

    def get_thread_local_conn(self):
        """为当前线程创建独立的数据库连接"""
        if not hasattr(self.thread_local, "pg_conn"):
            self.thread_local.pg_conn = psycopg2.connect(self.postgredb_url)
            self.thread_local.pg_conn.autocommit = False  # 关闭自动提交
            self.thread_local.pg_cursor = self.thread_local.pg_conn.cursor()
        return self.thread_local.pg_conn, self.thread_local.pg_cursor

    def get_db_conn(self):
        """获取当前线程的数据库连接"""
        pg_conn, pg_cursor = self.get_thread_local_conn()
        return pg_conn, self.mongodb
    def init_tables(self):
        try:
            # 创建 user 表
            self.pg_cursor.execute("""
                CREATE TABLE IF NOT EXISTS "user" (
                    user_id TEXT PRIMARY KEY,
                    password TEXT NOT NULL,
                    balance INTEGER NOT NULL,
                    token TEXT,
                    terminal TEXT
                )
            """)

            # 创建 user_store 表
            self.pg_cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_store (
                    user_id TEXT,
                    store_id TEXT,
                    PRIMARY KEY(user_id, store_id)
                )
            """)

            # 创建 store 表
            self.pg_cursor.execute("""
                CREATE TABLE IF NOT EXISTS store (
                    store_id TEXT,
                    book_id TEXT,
                    book_info TEXT,
                    stock_level INTEGER,
                    PRIMARY KEY(store_id, book_id)
                )
            """)

            # 创建 new_order 表
            self.pg_cursor.execute("""
                CREATE TABLE IF NOT EXISTS new_order (
                    order_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    store_id TEXT,
                    is_paid BOOLEAN NOT NULL,
                    is_shipped BOOLEAN NOT NULL,
                    is_received BOOLEAN NOT NULL,
                    order_completed BOOLEAN NOT NULL,
                    status TEXT NOT NULL,
                    created_time TIMESTAMP NOT NULL
                )
            """)

            # 创建 new_order_detail 表
            self.pg_cursor.execute("""
                CREATE TABLE IF NOT EXISTS new_order_detail (
                    order_id TEXT,
                    book_id TEXT,
                    count INTEGER,
                    price INTEGER,
                    PRIMARY KEY(order_id, book_id)
                )
            """)

            self.pg_conn.commit()
        except psycopg2.Error as e:  # pragma: no cover
            logging.error(e)
            self.pg_conn.rollback()

    def init_indexes(self):
        try:
            # 删除已有的索引（如果存在）
            self.pg_cursor.execute("""
                DROP INDEX IF EXISTS idx_store_book_id;
                DROP INDEX IF EXISTS idx_store_store_book;
                DROP INDEX IF EXISTS idx_store_book_info_gin;
            """)

            # 重新创建索引
            self.pg_cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_store_book_id 
                ON store(book_id);
                
                CREATE INDEX IF NOT EXISTS idx_store_store_book 
                ON store(store_id, book_id);
                
                CREATE INDEX IF NOT EXISTS idx_store_book_info_gin 
                ON store USING gin(to_tsvector('chinese', book_info));
            """)
            
            self.pg_conn.commit()
        except psycopg2.Error as e:   # pragma: no cover
            logging.error(f"Error creating PostgreSQL indexes: {e}")
            self.pg_conn.rollback()

    # def get_db_conn_init(self):
    #     return self.pg_conn, self.mongodb

# 全局变量用于数据库同步
database_instance: Store = None
init_completed_event = threading.Event()

def init_database(db_path):
    global database_instance
    database_instance = Store()
    init_completed_event.set()

def get_store():
    global database_instance
    return database_instance