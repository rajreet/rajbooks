import os
import requests
from flask import *
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from fuzzywuzzy import fuzz,process
from datetime import datetime

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = True
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

#Goodreads API key
KEY="BF8VAzf81fD4vsbBujwSqA"

#Book structure class with match ratio(levenshtein distance)
class Book:
    def __init__(self,title,author,isbn,year,ratio):
        self.title=title
        self.author=author
        self.isbn=isbn
        self.year=int(year)
        self.ratio=ratio

    


@app.route("/",methods=["POST","GET"])
def index():
    #if username exists in session(user logged in)
    if "name" in session:
        return redirect(url_for('books',page=1))
    
    if request.method=="GET":
        #resgistration successfull
        if 'display' in request.args:
            return render_template("index.html",disp="block",message="You have been registered succesfully.")
        else:
            return render_template("index.html",disp="none")
    else:
        email=request.form.get("email")
        password=request.form.get("password")
        try:
            passwords=db.execute(f"SELECT password FROM users WHERE email='{email}'").fetchone()
            pwd=passwords[0]
            # print(pwd)

            #login
            if(pwd==password):
                name=db.execute(f"SELECT username FROM users WHERE email='{email}'").fetchone()
                session["name"]=name[0]
                return redirect(url_for('books',page=1))
            else:
                #invalid password
                return render_template("index.html",disp="none",p_error="Invalid Password.")    
        except:
            # username not available
            return render_template("index.html",disp="none",email_error="Email does not exists.")

@app.route("/signup",methods=["POST","GET"])
def signup():
    if(request.method=="GET"):
        return render_template("signup.html",disp="none")
    else:
        name=request.form.get("name")
        username=request.form.get("username")
        email=request.form.get("email")
        password=request.form.get("password")

        #Check empty fields 
        if(name=="" or username=="" or email=="" or password==""):
            return render_template("signup.html",disp="block",error="Fields cannot be empty.")

        try:
            #register user into database
            db.execute("INSERT INTO users VALUES(:username,:name,:email,:password)",{"username":username,"name":name,"email":email,"password":password})
            db.commit()
            return redirect(url_for('index',display=True))
        except:
            return render_template("signup.html",disp="block",error="Username or Email already exists.")

@app.route("/books")
def books():
    #if username exists in session
    if session.get("name") is None:
        return render_template("error.html",message="User not logged in.")

    #store list of books in session
    if session.get("books") is None:
        session["books"]=db.execute("SELECT * FROM books").fetchall()

    if "page" in request.args:
        page=int(request.args['page'])

        #display books per page
        size=50

        #maximum page number
        page_length=int(len(session["books"])/size)
        if(page>page_length):
            return render_template("error.html",message="Page not Found")

        
        #for pagination
        start=size*(page-1)
        end=size*page

        lpage=page
        rpage=page+10

        #for pagination limits
        if page<=5:
            lpage=1
            rpage=10
        elif page>page_length-5:
            lpage=page_length-10
            rpage=page_length
        else:
            lpage-=5
            rpage-=5

        pagelist=range(lpage,rpage+1)
        
        return render_template("books.html",books=session["books"][start:end],pagelist=pagelist,currpage=page,pagelen=page_length,uname=session["name"],disp="block")

    else:
        #search parameters
        search=request.args['search']
        option=request.args['searchby']

        booklist=[]

        #search by name
        if option=="name":
            for book in session["books"]:
                ratio=fuzz.partial_ratio(search.upper(),book.title.upper())
                if ratio > 70:
                    obj=Book(book.title,book.author,book.isbn,book.year,ratio)
                    booklist.append(obj)
        
        #search by author
        if option=="author":
            for book in session["books"]:
                ratio=fuzz.partial_ratio(search.upper(),book.author.upper())
                if ratio > 70:
                    obj=Book(book.title,book.author,book.isbn,book.year,ratio)
                    booklist.append(obj)
        
        #search by isbn
        if option=="isbn":
            for book in session["books"]:
                ratio=fuzz.partial_ratio(search.upper(),book.isbn.upper())
                if ratio > 70:
                    obj=Book(book.title,book.author,book.isbn,book.year,ratio)
                    booklist.append(obj)
            
        #search by year    
        if option=="year":
            for book in session["books"]:
                year=str(book.year)
                ratio=fuzz.partial_ratio(search.upper(),year.upper())
                if ratio > 70:
                    obj=Book(book.title,book.author,book.isbn,book.year,ratio)
                    booklist.append(obj)


        #sort according to match ratio by fuzzy logic(levenshtein distance)
        booklist.sort(key=lambda x: x.ratio,reverse=True)

        return render_template("books.html",books=booklist[:50],pagelist={1},currpage=1,pagelen=1,uname=session["name"],disp="none")

@app.route("/book/<string:isbn>",methods=["POST","GET"])
def book(isbn):
    
    #search for the book
    book=db.execute(f"SELECT * FROM books WHERE isbn='{isbn}'").fetchone()

    print(book.rating_count)

    #get data from goodreads API if database does not have data
    if(book.rating_count is None):
        data = requests.get("https://www.goodreads.com/book/review_counts.json",params={"key":KEY,"isbns":book.isbn})
        bookapi=data.json()
        bookapi=bookapi['books'][0]
        rating_count=float(bookapi['work_ratings_count'])
        rating_score=int(round(rating_count*float(bookapi['average_rating'])))
        db.execute(f"UPDATE books SET rating_count={rating_count}, rating_score={rating_score} WHERE isbn='{book.isbn}'")

    else:
        rating_score=book.rating_score
        rating_count=book.rating_count
    
    db.commit()


    rating=round(rating_score/rating_count,2)

    # print(bookapi)

    #submit review
    if(request.method=='POST'):
        if(request.form.get('reviewsubmit') is not None):
            review=request.form.get('reviewsubmit')
            if(review!=""):
                date=datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                db.execute(f"INSERT INTO reviews(username,bookisbn,text,reviewdate) VALUES('{session['name']}','{book.isbn}','{review}','{date}');")
            db.commit()

            return redirect(url_for('book',isbn=book.isbn))
        
        if(request.form.get('userrating') is not None):
            print(request.form.get('userrating'))
            return redirect(url_for('book',isbn=book.isbn))

    #select reviews from data base
    reviews=db.execute(f"SELECT * FROM reviews WHERE bookisbn='{book.isbn}'").fetchall()


    return render_template("book.html",book=book,uname=session["name"],rating=rating,reviews=reviews)


@app.route("/logout")
def logout():
    del session["name"]
    session.clear()
    return redirect(url_for('index'))

    
    

        
        
