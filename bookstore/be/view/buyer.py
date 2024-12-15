from flask import Blueprint
from flask import request
from flask import jsonify
from be.model.buyer import Buyer
from be.model import user

bp_buyer = Blueprint("buyer", __name__, url_prefix="/buyer")


@bp_buyer.route("/new_order", methods=["POST"])
def new_order():
    user_id: str = request.json.get("user_id")
    store_id: str = request.json.get("store_id")
    books = request.json.get("books") 
    id_and_count = []
    for book in books:
        book_id = book.get("id")
        count = book.get("count")
        id_and_count.append((book_id, count))

    b = Buyer()
    code, message, order_id = b.new_order(user_id, store_id, id_and_count)
    return jsonify({"message": message, "order_id": order_id}), code


@bp_buyer.route("/pay_to_platform", methods=["POST"])
def pay_to_platform():
    user_id = request.json.get("user_id")
    password = request.json.get("password")  # 后端需要添加判断密码的相关操作
    order_id = request.json.get("order_id")
    b = Buyer()
    code, message = b.pay_to_platform(user_id, password, order_id)
    return jsonify({"message": message}), code

@bp_buyer.route("/confirm_receipt_and_pay_toseller", methods=["POST"])
def confirm_receipt_and_pay_toseller():
    user_id = request.json.get("user_id")
    password = request.json.get("password") # 后端需要添加判断密码的相关操作
    order_id = request.json.get("order_id")
    b = Buyer()
    code, message = b.confirm_receipt_and_pay_to_seller(user_id, password, order_id)
    return jsonify({"message": message}), code

@bp_buyer.route("/add_funds", methods=["POST"])
def add_funds():
    user_id = request.json.get("user_id")
    password = request.json.get("password")
    add_value = request.json.get("add_value")
    b = Buyer()
    code, message = b.add_funds(user_id, password, add_value)
    return jsonify({"message": message}), code

# 查询订单状态
@bp_buyer.route('/query_order_status', methods=["POST"])
def query_order_status():
    user_id = request.json.get("user_id")
    order_id = request.json.get("order_id")
    password = request.json.get("password")
    b = Buyer()
    code, message, order_status = b.query_order_status(user_id, order_id, password)
    return jsonify({"message": message, "order_status": order_status, "code": code})

# 查询所有订单
@bp_buyer.route('/query_buyer_all_orders', methods=["POST"])
def query_buyer_all_orders():
    user_id = request.json.get("user_id")
    password = request.json.get("password")
    b = Buyer()
    code, message, orders = b.query_buyer_all_orders(user_id, password)
    return jsonify({"message": message, "orders": orders, "code": code})

# 取消订单
@bp_buyer.route('/cancel_order', methods=["POST"])
def cancel_order():
    user_id = request.json.get("user_id")
    order_id = request.json.get("order_id")
    password = request.json.get("password")
    b = Buyer()
    code, message = b.cancel_order(user_id, order_id, password)
    return jsonify({"message": message, "code": code})


# 自动取消超时订单
@bp_buyer.route('/auto_cancel_expired_orders', methods=['POST'])
def auto_cancel_expired_orders():
    b = Buyer()
    code, message = b.auto_cancel_expired_orders()
    return jsonify({"message": message, "code": code})


@bp_buyer.route("/search", methods=["POST"])
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

