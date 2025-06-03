# _*_ coding: utf-8 _*_
"""
Time:     2025/5/20 9:37
Author:   shiver_man
Version:  V 0.1
File:     manager.py

"""
from flask import Flask
from flask_migrate import Migrate
from app import app, db

migrate = Migrate(app, db)

if __name__ == "__main__":
    app.run()

