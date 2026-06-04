from flask import Flask, request, jsonify
from config import Config
from models import db, User
from celery_app import create_celery
app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

with app.app_context():
    db.create_all()

celery = create_celery(app)

import redis

cache = redis.Redis(
    host="localhost",
    port=6379,
    db=1,
    decode_responses=True
)


# CREATE
@app.route("/users", methods=["POST"])
def create_user():
    from tasks import send_welcome_email
    data = request.get_json()

    user = User(
        name=data["name"],
        email=data["email"]
    )

    db.session.add(user)
    db.session.commit()

    send_welcome_email.delay(user.email)
    cache.set(
        f"user:{user.id}",
        user.email,
        ex=300
    )

    return jsonify(user.to_dict()), 201

# READ ALL
@app.route("/users", methods=["GET"])
def get_users():
    users = User.query.all()

    return jsonify([
        user.to_dict()
        for user in users
    ])


# READ ONE
@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    email = cache.get(f"user:{user_id}")
    if email:
        data={
            "id": user_id,
            "email": email
        }
        return data
    user = User.query.get_or_404(user_id)
    cache.set(
        f"user:{user.id}",
        user.email,
        ex=300
    )

    return jsonify(user.to_dict())


# UPDATE
@app.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    user = User.query.get_or_404(user_id)

    data = request.get_json()

    user.name = data.get("name", user.name)
    user.email = data.get("email", user.email)

    db.session.commit()

    return jsonify(user.to_dict())


# DELETE
@app.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": "User deleted"})


if __name__ == "__main__":
    app.run(debug=True)