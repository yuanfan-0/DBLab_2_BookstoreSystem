from flask import Blueprint
from flask import request
from flask import jsonify
from be.model import seller
from be.model import user
import json


bp_seller = Blueprint("seller", __name__, url_prefix="/seller")


@bp_seller.route("/create_store", methods=["POST"])
def seller_create_store():
    user_id: str = request.json.get("user_id")
    store_id: str = request.json.get("store_id")
    s = seller.Seller()
    code, message = s.create_store(user_id, store_id)
    return jsonify({"message": message}), code


@bp_seller.route("/add_book", methods=["POST"])
def seller_add_book():
    user_id: str = request.json.get("user_id")
    store_id: str = request.json.get("store_id")
    book_info: str = request.json.get("book_info")
    stock_level: str = request.json.get("stock_level", 0)

    s = seller.Seller()
    code, message = s.add_book(
        user_id, store_id, book_info.get("id"), json.dumps(book_info), stock_level
    )

    return jsonify({"message": message}), code

@bp_seller.route("/ship", methods=["POST"])
def ship():
    user_id: str = request.json.get("user_id")
    store_id: str = request.json.get("store_id")
    order_id: str = request.json.get("order_id")
    s = seller.Seller()
    code, message = s.ship(user_id, store_id,order_id)
    return jsonify({"message": message, "code": code})

@bp_seller.route("/add_stock_level", methods=["POST"])
def add_stock_level():
    user_id: str = request.json.get("user_id")
    store_id: str = request.json.get("store_id")
    book_id: str = request.json.get("book_id")
    add_num: str = request.json.get("add_stock_level", 0)

    s = seller.Seller()
    code, message = s.add_stock_level(user_id, store_id, book_id, add_num)

    return jsonify({"message": message}), code

@bp_seller.route("/query_one_store_orders", methods=["POST"])
def query_store_orders():
    user_id: str = request.json.get("user_id")
    store_id: str = request.json.get("store_id")
    password = request.json.get("password")

    s = seller.Seller()
    code, message, orders = s.query_one_store_orders(user_id, store_id, password)

    return jsonify({"message": message, "code": code, "orders": orders})


@bp_seller.route("/query_all_store_orders", methods=["POST"])
def query_all_store_orders():
    user_id: str = request.json.get("user_id")
    password = request.json.get("password")

    s = seller.Seller()
    code, message, orders = s.query_all_store_orders(user_id, password)

    return jsonify({"message": message, "code": code, "orders": orders})


@bp_seller.route("/search", methods=["POST"])
def search_books():
    json_obj = request.get_json()
    
    keyword = json_obj.get("keyword", "")
    search_scope = json_obj.get("search_scope", "all")
    search_in_store = json_obj.get("search_in_store", False)
    store_id = json_obj.get("store_id", None)

    u = user.User()
    code, books = u.search_books(
        keyword=keyword,
        search_scope=search_scope,
        search_in_store=search_in_store,
        store_id=store_id
    )

    # 将查询结果转换为可序列化的格式
    if code == 200:
        books_list = []
        for book in books:
            book_dict = {
                'id': book[0],
                'title': book[1],
                'author': book[2],
                'publisher': book[3],
                'original_title': book[4],
                'translator': book[5],
                'pub_year': book[6],
                'pages': book[7],
                'price': book[8],
                'currency_unit': book[9],
                'binding': book[10],
                'isbn': book[11],
                'author_intro': book[12],
                'book_intro': book[13],
                'content': book[14],
                'tags': book[15]
            }
            books_list.append(book_dict)
        return jsonify({"code": code, "books": books_list}), 200
    else:
        return jsonify({"code": code, "message": books}), code

@bp_seller.route("/get_stock_level", methods=["POST"])
def get_stock_level():
    store_id: str = request.json.get("store_id")
    book_id: str = request.json.get("book_id")
    s = seller.Seller()
    code, stock_level = s.get_stock_level(store_id, book_id)
    return jsonify({"code": code, "stock_level": stock_level})

@bp_seller.route("/add_stock_level_except", methods=["POST"])
def add_stock_level_except():
    user_id: str = request.json.get("user_id")
    store_id: str = request.json.get("store_id")
    book_id: str = request.json.get("book_id")
    add_stock_level: int = request.json.get("add_stock_level")
    s = seller.Seller()
    code, message = s.add_stock_level_except(user_id, store_id, book_id, add_stock_level)
    return jsonify({"message": message, "status_code": code})

@bp_seller.route("/add_stock_level_delay", methods=["POST"])
def add_stock_level_delay():
    user_id: str = request.json.get("user_id")
    store_id: str = request.json.get("store_id")
    book_id: str = request.json.get("book_id")
    add_stock_level: int = request.json.get("add_stock_level")
    s = seller.Seller()
    code, message = s.add_stock_level_delay(user_id, store_id, book_id, add_stock_level)
    return jsonify({"message": message, "status_code": code})




