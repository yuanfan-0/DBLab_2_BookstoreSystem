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
