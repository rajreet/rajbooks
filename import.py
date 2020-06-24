import os 
import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

try:
    db.execute("CREATE TABLE books( isbn VARCHAR PRIMARY KEY, title VARCHAR  NOT NULL,author VARCHAR  NOT NULL, year INTEGER NOT NULL );")
    print("Database created")
except:
    print("Database Exists")

with open('books.csv') as bookscsv:
    books=csv.reader(bookscsv)

    #skip headers
    next(books)

    count=0
    for row in books:
        isbn=row[0]
        title=row[1]
        author=row[2]
        year=row[3]

        #replace apostrophes
        title=title.replace("'","''")
        author=author.replace("'","''")

        db.execute(f"INSERT INTO books VALUES ('{isbn}','{title}','{author}',{year});")
        count+=1
        print(f"Inserted {count}.")

db.commit()