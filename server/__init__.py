import nltk
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
nltk.download('punkt')