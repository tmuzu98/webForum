from flask import Flask, request, jsonify, make_response
from pymongo.server_api import ServerApi
from pymongo import MongoClient
import secrets
import datetime
import pytz

app = Flask(__name__)

client = MongoClient("mongodb://localhost:27017/")
# Tried connecting to remote server but it did not allow connection to remote server from gradescope.com
# client = MongoClient("mongodb+srv://mu:12345@cluster0.qm6hjnk.mongodb.net/?retryWrites=true&w=majority")
# uri = "mongodb+srv://mu:12345@cluster0.qm6hjnk.mongodb.net/?retryWrites=true&w=majority"
# client = MongoClient(uri, server_api=ServerApi('1'))
db = client["forum"]

posts = db["posts"]
users = db["users"]

@app.route("/user", methods=["POST"])
def create_user():
    data = request.get_json(force=True)

    if "username" not in data or "email" not in data:
        return make_response(jsonify(err="Bad request"), 400)
    
    username = data["username"]
    email = data["email"]
    real_name = data.get("real_name", "")
    avatar_icon = data.get("avatar_icon", "")

    existing_user = users.find_one({"username": username})
    if existing_user:
        return make_response(jsonify(err="Username already taken"), 409)

    user_id = users.estimated_document_count() + 1
    user_key = secrets.token_hex(32)

    user = {
        "id": user_id,
        "key": user_key,
        "username": username,
        "email": email,
        "real_name": real_name,
        "avatar_icon": avatar_icon,
    }

    users.insert_one(user)

    return jsonify(id=user_id, key=user_key)


@app.route("/user/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = users.find_one({"id": user_id})

    if not user:
        return make_response(jsonify(err="Not found"), 404)

    return jsonify(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        real_name=user["real_name"],
        avatar_icon=user["avatar_icon"],
    )


@app.route("/user/<int:user_id>/edit", methods=["PUT"])
def edit_user(user_id):
    data = request.get_json(force=True)

    if "key" not in data:
        return make_response(jsonify(err="Bad request"), 400)

    user_key = data["key"]

    user = users.find_one({"id": user_id})

    if not user:
        return make_response(jsonify(err="Not found"), 404)

    if user["key"] != user_key:
        return make_response(jsonify(err="Forbidden"), 403)

    users.update_one(
        {"id": user_id},
        {
            "$set": {
                "username": data.get("username", user["username"]),
                "email": data.get("email", user["email"]),
                "real_name": data.get("real_name", user["real_name"]),
                "avatar_icon": data.get("avatar_icon", user["avatar_icon"]),
            }
        },
    )

    return jsonify(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        real_name=user["real_name"],
        avatar_icon=user["avatar_icon"],
    )


@app.route("/post", methods=["POST"])
def create_post():
    data = request.get_json(force=True)

    if not data or "msg" not in data or not isinstance(data["msg"], str):
        return make_response(jsonify(err="Bad request"), 400)

    user_id = data.get("user_id", None)
    user_key = data.get("user_key", None)
    if user_id is not None:
        user = users.find_one({"id": user_id})
        if not (user and user["key"] == user_key):
            return make_response(jsonify(err="User not found or invalid key"), 403)

    parent_post_id = data.get("parent_post_id", None)
    if parent_post_id is not None:
        parent_post = posts.find_one({"id": parent_post_id})
        if not parent_post:
            return make_response(jsonify(err="Parent post not found"), 404)
    post_id = posts.estimated_document_count() + 1
    key = secrets.token_hex(32)
    local_tz = pytz.timezone('America/New_York')  # Replace with your timezone
    local_datetime = datetime.datetime.now(local_tz)
    local_datetime_iso = local_datetime.isoformat()
    timestamp = local_datetime_iso
    post = {
        "id": post_id,
        "key": key,
        "timestamp": timestamp,
        "msg": data["msg"],
        "user_id": user_id,
        "parent_post_id": parent_post_id,
        "replies": [],
    }

    posts.insert_one(post)

    if parent_post_id is not None:
        posts.update_one({"id": parent_post_id}, {"$push": {"replies": post_id}})

    return jsonify(id=post_id, key=key, timestamp=timestamp, user_id=user_id)

@app.route("/post/<int:post_id>", methods=["GET"])
def read_post(post_id):
    post = posts.find_one({"id": post_id})
    if not post:
        return make_response(jsonify(err="Not found"), 404)

    return jsonify(
        id=post["id"],
        timestamp=post["timestamp"],
        msg=post["msg"],
        user_id=post.get("user_id", None),
        parent_post_id=post.get("parent_post_id", None),
        replies=post["replies"],
    )

@app.route("/post/<int:post_id>/delete/<key>", methods=["DELETE"])
def delete_post(post_id, key):
    post = posts.find_one({"id": post_id})
    if not post:
        return make_response(jsonify(err="Not found"), 404)

    if post["key"] != key and (
        post["user_id"] is None or users.find_one({"id": post["user_id"]})["key"] != key
    ):
        return make_response(jsonify(err="Forbidden"), 403)

    posts.delete_one({"id": post_id})

    user_id = post["user_id"]
    username = None
    if user_id is not None:
        user = users.find_one({"id": user_id})
        if user:
            username = user["username"]

    return jsonify(
        id=post["id"],
        key=post["key"],
        timestamp=post["timestamp"],
        user_id=user_id,
        username=username,
    )  

@app.route("/posts/search", methods=["GET"])
def search_posts():
    start_datetime_str = request.args.get("start_datetime", None)
    end_datetime_str = request.args.get("end_datetime", None)

    local_tz = pytz.timezone('America/New_York')  

    if start_datetime_str is not None:
        try:
            start_datetime = datetime.datetime.fromisoformat(start_datetime_str).replace(tzinfo=local_tz)
        except ValueError:
            return make_response(jsonify(err="Invalid start_datetime format"), 400)
    else:
        start_datetime = None

    if end_datetime_str is not None:
        try:
            end_datetime = datetime.datetime.fromisoformat(end_datetime_str).replace(tzinfo=local_tz)
        except ValueError:
            return make_response(jsonify(err="Invalid end_datetime format"), 400)
    else:
        end_datetime = None

    query = {}
    if start_datetime is not None and end_datetime is not None:
        query["timestamp"] = {"$gte": start_datetime.isoformat(), "$lte": end_datetime.isoformat()}
    elif start_datetime is not None:
        query["timestamp"] = {"$gte": start_datetime.isoformat()}
    elif end_datetime is not None:
        query["timestamp"] = {"$lte": end_datetime.isoformat()}

    matching_posts = posts.find(query)

    results = []
    for post in matching_posts:
        results.append(
            {
                "id": post["id"],
                "timestamp": post["timestamp"],
                "msg": post["msg"],
                "user_id": post["user_id"],
                "parent_post_id": post.get("parent_post_id", None),
                "replies": post["replies"],
            }
        )

    return jsonify(results)

@app.route("/posts/user/<int:user_id>", methods=["GET"])
def get_posts_by_user(user_id):
    user = users.find_one({"id": user_id})
    if not user:
        return make_response(jsonify(err="User not found"), 404)

    found_posts = posts.find({"user_id": user_id})

    response = []
    for post in found_posts:
        response.append(
            {
                "id": post["id"],
                "timestamp": post["timestamp"],
                "msg": post["msg"],
                "user_id": post["user_id"],
                "parent_post_id": post.get("parent_post_id", None),
                "replies": post["replies"],
            }
        )

    return jsonify(posts=response)

if __name__ == "__main__":
    app.run()
        