import os

from flask import *
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/",methods=["POST","GET"])
def index():
    if request.method=="GET":
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

            if(pwd==password):
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
            db.execute("INSERT INTO users VALUES(:username,:name,:email,:password)",{"username":username,"name":name,"email":email,"password":password})
            db.commit()
            return redirect(url_for('index',display=True))
        except:
            return render_template("signup.html",disp="block",error="Username or Email already exists.")

@app.route("/books")
def books():
    #store list of books in session
    if session.get("books") is None:
        session["books"]=db.execute("SELECT * FROM books").fetchall()

    page=int(request.args['page'])
    #display books per page
    size=50

    #maximum page number
    page_length=int(len(session["books"])/size)
    if(page>page_length):
        return "Page Not Found"

    
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
    
    return render_template("books.html",books=session["books"][start:end],pagelist=pagelist,currpage=page,pagelen=page_length)
    
    

        
        
