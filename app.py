import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'rideshare-secret-key-2024')
    
    MYSQL_USER     = os.environ.get('MYSQLUSER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQLPASSWORD', '')
    MYSQL_HOST     = os.environ.get('MYSQLHOST', 'localhost')
    MYSQL_PORT     = os.environ.get('MYSQLPORT', '3306')
    MYSQL_DB       = os.environ.get('MYSQLDATABASE', 'ridesharing')

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False