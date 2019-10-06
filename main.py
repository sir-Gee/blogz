import datetime

from flask import Flask, request, render_template, redirect, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc

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
    email = db.Column(db.String(120), unique=True)
    username = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, email, username, password):
        self.email = email
        self.username = username
        self.password = password


@app.route('/addpost', methods=['POST', 'GET'])
def add_post():

    if request.method == 'POST':
        post_title = request.form['title']
        post_text = request.form['text']

        if post_title == Blog.query.filter_by(title=post_title).first():
            return redirect("/addpost?error=You have this post already")

        user = User.query.filter_by(email=session['email']).first()
        blog = Blog(post_title, post_text, datetime.datetime.now().strftime("%c"), user)
        db.session.add(blog)
        db.session.commit()

        return redirect("/")

    return render_template('addpost.html', errorTask=request.args.get("error"))


@app.route('/', methods=['POST', 'GET'])
def index():
    post_id = request.args.get('post_id')
    user_id = request.args.get('user_id')

    if post_id:
        blog = Blog.query.filter_by(id=post_id).first()
        user = Blog.query.filter_by(owner_id=user_id).all()
        return render_template('post.html', post=blog, user=user)

    if user_id:
        blog = Blog.query.filter_by(owner_id=user_id).all()
        # blog1 = blog.order_by(desc(Blog.id)).all()
        # blog = Blog.query.filter_by(owner_id=user_id).all()
        return render_template('posts.html', posts=blog)

    # all_posts = Blog.query.order_by(Blog.created_at.desc()).all()

    all_users = User.query.all()

    return render_template('users.html', title="BlogZ!", users=all_users)


@app.route("/login", methods=['GET', 'POST'])
def login():
    error_mail = ""

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if email == "" or password == "":
            flash('zoiks! Email and Password cant be blank')
            return redirect('/login')

        user = User.query.filter_by(email=email).first()

        if user is None:
            error_mail = 'zoiks! User with ' + email + ' doesnt exist. Please register one'
            return render_template("register.html", error_mail=error_mail)

        if password != user.password:
            flash('zoiks! Password is not correct')
            # return redirect('/login')
            return render_template("login.html")

        session['email'] = email
        return redirect("/addpost")
    else:
        return render_template("login.html")


@app.route("/register", methods=['GET', 'POST'])
def register():
    error_register = ''

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        verify = request.form['verify']
        if email == '' or password == '' or verify == '':
            error_register = 'one or more fields are invalid'
            return render_template('register.html', error_register=error_register)
        else:
            if not is_email(email):
                flash('zoiks! "' + email + '" does not seem like an email address')
                return redirect('/register')

        user = User.query.filter_by(email=email).first()

        if user is not None:
            error_register = 'User with ' + email + ' already exists'
            return render_template('register.html', error_register=error_register)

        if request.form['password'] != request.form['verify']:
            error_register = "Passwords dont match"
            return render_template('register.html', error_register=error_register)

        if len(email) < 3 or len(email) > 20 or len(password) < 3 or len(password) > 20:
            error_register = "an invalid username or an invalid password message"
            return render_template('register.html', error_register=error_register)

        user = User(email=email, password=password)
        db.session.add(user)
        db.session.commit()
        session['email'] = email
        return redirect("/")
    else:
        return render_template('register.html')


def is_email(string):
    atsign_index = string.find('@')
    atsign_present = atsign_index >= 0
    if not atsign_present:
        return False
    else:
        domain_dot_index = string.find('.', atsign_index)
        domain_dot_present = domain_dot_index >= 0
        return domain_dot_present


@app.route("/logout")
def logout():
    del session['email']
    return redirect("/")


@app.before_request
def require_login():

    endpoints_without_login = ['/', 'login', 'register']

    if not (session or request.endpoint in endpoints_without_login):
        return redirect("/register")


app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RU'

if __name__ == '__main__':
    app.run()
