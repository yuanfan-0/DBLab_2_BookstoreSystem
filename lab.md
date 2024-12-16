# 索引构建说明

## PostgreSQL 索引设计

在 `store.py` 的 `init_tables` 方法中，我们构建了三种索引：

1. 基础索引

```sql
CREATE INDEX IF NOT EXISTS idx_store_book_id ON store(book_id);
```
- 为 book_id 创建单列索引
- 用于加速按书籍ID查询的操作

2. 复合索引

```sql
CREATE INDEX IF NOT EXISTS idx_store_store_book ON store(store_id, book_id);
```
- 为 store_id 和 book_id 创建复合索引
- 优化在特定商店中查找特定书籍的操作

3. 全文搜索索引

```sql
CREATE INDEX IF NOT EXISTS idx_store_book_info_gin ON store USING gin(to_tsvector('chinese', book_info));
```
- 使用 GIN (Generalized Inverted Index) 索引类型
- 支持中文全文搜索功能
- 对 book_info 字段建立全文搜索索引
- 可用于模糊搜索和相关性排序

## 全文搜索索引使用示例

1. 基础搜索

```sql
SELECT * FROM store 
WHERE to_tsvector('chinese', book_info) @@ to_tsquery('chinese', '关键词');
```

2. 带相关性排序的搜索

```sql
SELECT *, 
       ts_rank(to_tsvector('chinese', book_info), to_tsquery('chinese', '关键词')) as rank 
FROM store 
WHERE to_tsvector('chinese', book_info) @@ to_tsquery('chinese', '关键词')
ORDER BY rank DESC;
```

## 注意事项

1. 索引优势：
   - 提高查询性能
   - 支持复杂的搜索功能
   - 优化排序操作

2. 索引使用注意：
   - 索引会占用额外存储空间
   - 会轻微影响写入性能
   - 需要定期维护优化

3. 全文搜索索引特点：
   - 支持中文分词
   - 支持模糊匹配
   - 可以按相关性排序
   - 适合处理大量文本数据

# 中文全文搜索配置安装与配置指南

在本指南中，我们将介绍如何在 PostgreSQL 中安装和配置中文全文搜索支持，以便在书店项目中使用。

## 安装 `zhparser` 插件

1. **下载并编译 `zhparser`**：
   - 确保你的系统上安装了 `PostgreSQL` 和 `pg_config` 工具。
   - 使用以下命令下载并编译 `zhparser`：
     ```bash
     git clone https://github.com/amutu/zhparser.git
     cd zhparser
     make && sudo make install     ```

2. **在 PostgreSQL 中创建 `zhparser` 扩展**：
   - 使用 `psql` 连接到你的数据库，并创建 `zhparser` 扩展：
     ```sql
     psql -U postgres -d bookstore
     CREATE EXTENSION zhparser;     ```

## 创建中文文本搜索配置

1. **创建中文配置**：
   - 基于 `simple` 配置创建一个新的 `chinese` 配置：
     ```sql
     CREATE TEXT SEARCH CONFIGURATION chinese ( COPY = simple );     ```

2. **添加解析器和词典**：
   - 如果你有中文分词插件（如 `zhparser`），可以为 `chinese` 配置添加解析器和词典。
   - 如果没有，你可以暂时使用 `simple` 配置的解析器和词典，但这可能无法提供准确的中文分词。

3. **验证配置**：
   - 确保新的 `chinese` 配置已创建：
     ```sql
     \dF     ```

   - 你应该能在列表中看到 `chinese` 配置。

## 修改代码

确保在 `bookstore/be/model/store.py` 中的索引创建部分使用新的 `chinese` 配置：
