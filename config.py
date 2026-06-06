import os

class Config:
    SECRET_KEY = 'ridesharing-unilorin-2025-secret'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:@localhost/ridesharing'
    SQLALCHEMY_TRACK_MODIFICATIONS = False