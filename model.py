# _*_ coding: utf-8 _*_
"""
Time:     2025/5/20 9:37
Author:   shiver_man
Version:  V 0.1
File:     model.py

"""


from extensions import db
#mock数据
class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(60), nullable=False)
    password = db.Column(db.String(30), nullable=False)
#userinfo
class UserInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nickname = db.Column(db.String(60), nullable=True)  # 允许为空
    image_path = db.Column(db.String(200), nullable=False)
    openid = db.Column(db.String(64), nullable=False, unique=True)
    token = db.Column(db.String(128), nullable=False, unique=True)
    create_time = db.Column(db.DateTime, nullable=False)
#book
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # 假设主键
    book_id = db.Column(db.String(100), nullable=False, unique=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200), nullable=False)
    book_image = db.Column(db.String(200))  # 确保添加了这个字段
    create_time = db.Column(db.DateTime, nullable=False)

class BorrowRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    book_id = db.Column(db.String(100), nullable=False)
    borrow_time = db.Column(db.DateTime, nullable=False)
    return_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(10), nullable=False, default='borrowed')

class Friend(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    friend_id = db.Column(db.Integer, nullable=False)
    friend_nickname = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(10), nullable=False, default='borrowed')