import logging

from flask import Flask, jsonify
import os
from flask_migrate import Migrate
from extensions import db
from model import UserInfo
from model import Book
from model import User
import requests
import time
import random
import string
from datetime import datetime
from flask import request
from model import BorrowRecord
from model import Friend

WECHAT_APPID = "wx03b00acfbdbd09e6"
WECHAT_SECRET = "90432fd94ff93d26d2fa9c8a882923ee"
#---------------------------------------------------------------------------------------------------------------------#
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
migrate = Migrate(app, db)

@app.route('/mock', methods=['POST'])
def mock():
    user_id = request.json.get('user_id')
    username = request.json.get('username')
    password = request.json.get('password')
    user = User(user_id=user_id, username=username, password=password)
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'User created successfully'})

#---------------------------------------------------------------------------------------------------#
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/upload_userinfo', methods=['POST'])
def upload_userinfo():
    file = request.files.get('file')
    nickname = request.form.get('nickname')
    code = request.form.get('code')
    if not code:
        return jsonify({'error': '缺少code'}), 400
    if not (file and nickname):
        return jsonify({'error': '缺少文件或昵称'}), 400

    # 微信code换openid
    wx_url = f"https://api.weixin.qq.com/sns/jscode2session?appid={WECHAT_APPID}&secret={WECHAT_SECRET}&js_code={code}&grant_type=authorization_code"
    resp = requests.get(wx_url)
    wx_data = resp.json()
    if 'openid' not in wx_data:
        return jsonify({'error': '微信登录失败', 'detail': wx_data}), 400
    openid = wx_data['openid']
    token = openid + '_' + str(int(time.time())) + '_' + ''.join(random.choices(string.ascii_letters + string.digits, k=8))

    # 保存图片
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    folder = os.path.dirname(save_path)
    if not os.path.exists(folder):
        os.makedirs(folder)
    file.save(save_path)
    file_url = f"/static/uploads/{file.filename}"

    # 检查openid是否已存在
    user_info = UserInfo.query.filter_by(openid=openid).first()
    if user_info:
        # 已存在则更新
        user_info.nickname = nickname
        user_info.image_path = save_path
        user_info.token = token
        user_info.create_time = datetime.now()
    else:
        # 不存在则新建
        user_info = UserInfo(
            nickname=nickname,
            image_path=save_path,
            openid=openid,
            token=token,
            create_time=datetime.now()
        )
        db.session.add(user_info)
    db.session.commit()
    return jsonify({'nickname': nickname, 'file_url': file_url, 'token': token, 'openid': openid})
#---------------------------------------------------------------------------------------------------------------------#
@app.route('/uploads')
def list_uploads():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    file_urls = [f"/static/uploads/{filename}" for filename in files]
    return jsonify(file_urls)
#---------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------#

@app.route('/get_userinfo', methods=['GET', 'POST'])
def get_userinfo():
    # 优先从请求头获取 openid
    auth_header = request.headers.get('Authorization')
    openid = None
    if auth_header and auth_header.startswith('Bearer '):
        openid = auth_header.split(' ')[1]
    # 如果请求头没有，再从参数或 body 获取
    if not openid:
        openid = request.args.get('openid') or request.json.get('openid') if request.is_json else None
    if not openid:
        return jsonify({'error': '缺少或无效的openid'}), 401

    # 查询数据库，判断 openid 是否存在
    user_info = UserInfo.query.filter_by(openid=openid).first()
    if not user_info:
        return jsonify({'error': '用户不存在或openid无效'}), 401

    # 返回用户信息
    return jsonify({
        'userinfo': {
            'nickname': user_info.nickname,
            'image_path': user_info.image_path,
            'openid': user_info.openid,
            'token': user_info.token,
            'create_time': user_info.create_time.strftime('%Y-%m-%d %H:%M:%S')
        }
    })
#---------------------------------------------------------------------------------------------------------------------#
#添加书籍
@app.route('/books', methods=['POST'])
def create_book():
    # 优先从请求头获取 openid
    auth_header = request.headers.get('Authorization')
    openid = None
    if auth_header and auth_header.startswith('Bearer '):
        openid = auth_header.split(' ')[1]
    # 如果请求头没有，再从参数或 body 获取
    if not openid:
        openid = request.args.get('openid') or request.json.get('openid') if request.is_json else None
    if not openid:
        return jsonify({'error': '缺少或无效的openid'}), 401

    title=request.form.get('title')
    author= request.form.get('author')
    book_image= request.files.get('book_image')
    save_path = os.path.join('static/uploads/book', book_image.filename).replace('\\','/')
    print(save_path)
    folder = os.path.dirname(save_path)
    if not os.path.exists(folder):
        os.makedirs(folder)
    book_image.save(save_path)
    book_url = f"/static/uploads/book/{book_image.filename}"
    book_info= Book.query.filter_by(book_id=book_id).first()
    if not title and author:
        return jsonify({'error': '缺少书名和作者'}), 400
    if not book_image:
        return jsonify({'error':'你图呢'})
    if book_info:
        # 已存在则更新
        book_info.book_id = book_id
    else:
        # 不存在则新建
        book_info = Book(
            book_id=book_id,
            title=title,
            author=author,
            book_image=save_path,  # 注意这里使用 book_url 保存路径
            create_time=datetime.now()
        )
        db.session.add(book_info)
    db.session.commit()
    return jsonify({
        "code": 200,
        "msg": "添加成功",
        'book_id':book_id,
        'book_url':book_url
    })
#---------------------------------------------------------------------------------------------------------------------#
#获取书籍
@app.route('/books', methods=['GET'])
def get_books():
    book_title = request.json.get('title')
    book = Book.query.filter_by(title=book_title).first()
    if book:
        return jsonify({
            "code": 200,
            "msg": "查询成功",
            "data": {
                "book_id": book.book_id,
                "title": book.title,
                "author": book.author,
                "book_image": book.book_image,
                "create_time": book.create_time.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    else:
        return jsonify({
            "code": 404,
            "msg": "未找到该书籍"
        })
#---------------------------------------------------------------------------------------------------------------------#
@app.route('/books/<book_id>', methods=['PUT'])
def update_book(book_id):
    # 获取请求中的数据
    title = request.form.get('title')
    author = request.form.get('author')
    book_image = request.files.get('book_image')

    # 根据 book_id 查询数据库中的书籍
    book = Book.query.filter_by(book_id=book_id).first()
    print(book_id)
    # 如果未找到该书籍，则返回错误信息
    if not book:
        return jsonify({
            "code": 404,
            "msg": "未找到书籍，无法更新"
        }), 404

    # 更新书籍的信息
    if title:
        book.title = title
    if author:
        book.author = author

    # 如果有上传新的图片，则保存并更新图片路径
    if book_image:
        # 构造文件保存路径
        save_path = os.path.join('static/uploads/book', book_image.filename).replace('\\', '/')
        folder = os.path.dirname(save_path)
        if not os.path.exists(folder):
            os.makedirs(folder)
        book_image.save(save_path)
        book.book_image = save_path  # 更新数据库中书籍图片路径

    # 更新修改时间
    book.create_time = datetime.now()

    # 提交更改到数据库
    db.session.commit()

    return jsonify({
        "code": 200,
        "msg": "书籍信息更新成功",
        "data": {
            "book_id": book.book_id,
            "title": book.title,
            "author": book.author,
            "book_image": book.book_image,
            "create_time": book.create_time.strftime('%Y-%m-%d %H:%M:%S')
        }
    })


#---------------------------------------------------------------------------------------------------------------------#
@app.route('/books/<book_id>', methods=['DELETE'])
def delete_book(book_id):
    # 根据 book_id 查询书籍信息
    book = Book.query.filter_by(book_id=book_id).first()

    # 如果未找到书籍，返回错误信息
    if not book:
        return jsonify({
            "code": 404,
            "msg": "未找到书籍，无法删除"
        }), 404

    # 删除书籍记录
    db.session.delete(book)
    db.session.commit()

    return jsonify({
        "code": 200,
        "msg": "书籍删除成功",
        "data": {
            "book_id": book.book_id,
            "title": book.title,
            "author": book.author,
            "book_image": book.book_image,
            "create_time": book.create_time.strftime('%Y-%m-%d %H:%M:%S')
        }
    })
#---------------------------------------------------------------------------------------------------------------------#

@app.route('/borrow', methods=['POST'])
def borrow_book():
    user_id = request.json.get('user_id')
    book_id = request.json.get('book_id')
    # 检查书是否已被借出
    record = BorrowRecord.query.filter_by(book_id=book_id, status='borrowed').first()
    if record:
        return jsonify({'code': 400, 'msg': '该书已被借出'})
    # 创建借阅记录
    borrow_record = BorrowRecord(
        user_id=user_id,
        book_id=book_id,
        borrow_time=datetime.now(),
        status='borrowed'
    )
    db.session.add(borrow_record)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '借书成功'})

#---------------------------------------------------------------------------------------------------------------------#

@app.route('/return', methods=['POST'])
def return_book():
    user_id = request.json.get('user_id')
    book_id = request.json.get('book_id')
    # 查找未归还的借阅记录
    record = BorrowRecord.query.filter_by(user_id=user_id, book_id=book_id, status='borrowed').first()
    if not record:
        return jsonify({'code': 404, 'msg': '未找到借阅记录'})
    record.return_time = datetime.now()
    record.status = 'returned'
    db.session.commit()
    return jsonify({'code': 200, 'msg': '还书成功'})

#---------------------------------------------------------------------------------------------------------------------#

@app.route('/friend', methods=['POST'])
def add_friend():
    friend_nickname = request.json.get('friend_nickname')
    # 查找未归还的借阅记录
    friend = Friend.query.filter_by(friend_nickname=friend_nickname, status='borrowed').first()
    if not friend:
        return jsonify({'code': 404, 'msg': '未找到借阅记录'})
    return jsonify({
        'friend':(
            'friend_nickname': friend.friend_nickname,
        )
    })

if __name__ == '__main__':
    app.run(debug=True)
