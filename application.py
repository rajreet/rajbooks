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


        

@app.route("/signup",methods=["POST","GET"])
def signup():
    if(request.method=="GET"):
        return render_template("signup.html",disp="none")
    else:
        name=request.form.get("name")
        username=request.form.get("username")
        email=request.form.get("email")
        password=request.form.get("password")

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
    return render_template("books.html")
    

        
        
