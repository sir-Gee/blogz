import datetime

from flask import Flask, request, render_template, redirect, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
import hashlib

app = Flask(__name__)

app.config['DEBUG'] = True      # displays runtime errors in the browser, too
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:qwerty@localhost:3306/blogz'
app.config['SQLALCHEMY_ECHO'] = True


db = SQLAlchemy(app)


class Blog(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    text = db.Column(db.String(255))
    created_at = db.Column(db.String(120))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __init__(self, title, text, created_at, owner):
        self.title = title
        self.text = text
        self.created_at = created_at
        self.owner = owner


class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.password = password


@app.route('/addpost', methods=['POST', 'GET'])
def add_post():

    if request.method == 'POST':
        post_title = request.form['title']
        post_text = request.form['text']

        if post_title == "" or post_text == "":
            return render_template('addpost.html', errorPost="Title or Body cannot be blank")


        # if post_title == Blog.query.filter_by(title=post_title).first():
        #     return redirect("/addpost?error=You have this post already")

        user = User.query.filter_by(username=session['username']).first()
        blog = Blog(post_title, post_text, datetime.datetime.now().strftime("%c"), user)
        db.session.add(blog)
        db.session.commit()

        blog = Blog.query.filter_by(title=post_title, text=post_text).first()

        return redirect("/index?user_id="+str(user.id)+"&post_id="+str(blog.id))

    return render_template('addpost.html', errorTask=request.args.get("error"))


@app.route("/blogs", methods=['POST', 'GET'])
def blogs():
    blog = Blog.query.all()
    user = User.query.all()
    return render_template('allUserPosts.html', posts=blog, user=user)


@app.route('/', methods=['POST', 'GET'])
def index():
    return redirect('index')


@app.route('/index', methods=['POST', 'GET'])
def main_page():

    post_id = request.args.get('post_id')
    user_id = request.args.get('user_id')
    sort_desc = request.args.get('sort_desc')
    sort_asc = request.args.get('sort_asc')
    delete_post = request.args.get('delete_post')

    if delete_post:
        blog = Blog.query.filter_by(id=post_id).first()
        db.session.delete(blog)
        db.session.commit()
        user = User.query.filter_by(id=user_id).first()
        blog = Blog.query.filter_by(owner_id=user_id).order_by(desc(Blog.created_at)).all()
        return render_template('posts.html', posts=blog, user=user)

    if sort_desc:
        user = User.query.filter_by(id=user_id).first()
        blog = Blog.query.filter_by(owner_id=user_id).order_by(desc(Blog.created_at)).all()
        return render_template('posts.html', posts=blog, user_id=user_id, user=user)

    if sort_asc:
        user = User.query.filter_by(id=user_id).first()
        blog = Blog.query.filter_by(owner_id=user_id).all()
        return render_template('posts.html', posts=blog, user=user)

    if post_id:
        blog = Blog.query.filter_by(id=post_id).first()
        user = Blog.query.filter_by(owner_id=user_id).all()
        return render_template('post.html', post=blog, user=user)

    if user_id:
        blog = Blog.query.filter_by(owner_id=user_id).order_by(desc(Blog.created_at)).all()
        user = User.query.filter_by(id=user_id).first()
        # blog1 = blog.order_by(desc(Blog.id)).all()
        # blog = Blog.query.filter_by(owner_id=user_id).all()
        return render_template('posts.html', posts=blog, user=user)


    # all_posts = Blog.query.order_by(Blog.created_at.desc()).all()

    all_users = User.query.all()

    return render_template('users.html', title="BlogZ!", users=all_users)


@app.route("/login", methods=['GET', 'POST'])
def login():
    error_mail = ""

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == "" or password == "":
            flash('zoiks! Username and Password cant be blank')
            return redirect('/login')

        user = User.query.filter_by(username=username).first()

        if user is None:
            error_mail = 'zoiks! User with ' + username + ' doesnt exist. Please register one'
            return render_template("register.html", error_mail=error_mail)

        if hashlib.md5(password.encode()).hexdigest() != user.password:
            flash('zoiks! Password is not correct')
            # return redirect('/login')
            return render_template("login.html", username=username)

        session['username'] = username
        return redirect("/addpost")
    else:
        return render_template("login.html")


@app.route("/register", methods=['GET', 'POST'])
def register():
    error_register = ''

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']
        if username == '' or password == '' or verify == '':
            error_register = 'one or more fields are invalid'
            return render_template('register.html', error_register=error_register)

        user = User.query.filter_by(username=username).first()

        if user is not None:
            error_register = 'User with ' + username + ' already exists'
            return render_template('register.html', error_register=error_register, username=username)

        if request.form['password'] != request.form['verify']:
            error_register = "Passwords dont match"
            return render_template('register.html', error_register=error_register, username=username)

        if len(username) < 3 or len(username) > 20 or len(password) < 3 or len(password) > 20:
            error_register = "invalid username or invalid password"
            return render_template('register.html', error_register=error_register, username=username)

        user = User(username=username, password=hashlib.md5(password.encode()).hexdigest())
        db.session.add(user)
        db.session.commit()
        session['username'] = username
        return redirect("/")
    else:
        return render_template('register.html')


# def is_email(string):
#     atsign_index = string.find('@')
#     atsign_present = atsign_index >= 0
#     if not atsign_present:
#         return False
#     else:
#         domain_dot_index = string.find('.', atsign_index)
#         domain_dot_present = domain_dot_index >= 0
#         return domain_dot_present


@app.route("/logout")
def logout():
    del session['username']
    return redirect("/")


@app.before_request
def require_login():

    endpoints_without_login = ['main_page', 'login', 'register']

    if request.endpoint not in endpoints_without_login and 'username' not in session:
        return redirect("/register")

    # if request.endpoint == 'addpost' and session not in User.query.filter_by(username=session['username']).all():
    #     return redirect("/register")


def sort():
    print("hello")

app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RU'

if __name__ == '__main__':
    app.run()
