from flask import Flask, render_template, flash, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate 
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from webforms import LoginForm, PostForm, UserForm, SearchForm
from flask_ckeditor import CKEditor
import uuid as uuid
import os 

# Create a Flask Instance
app = Flask(__name__)
ckeditor = CKEditor(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://azaoydqyrtodxb:e6caacb1f2bd4fbfdb17d5b06b326c30c48fb3cc76150f2859985cb1310c6f6f@ec2-52-3-60-53.compute-1.amazonaws.com:5432/d32gvgjkaefqhp'
app.config['SECRET_KEY'] = "secret key"

UPLOAD_TO_STATIC = 'static/images/'
app.config['UPLOAD_FOLDER'] = UPLOAD_TO_STATIC

#Initialize The Database
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Flask Login 
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# Database Models

    # Blog posts
class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    content = db.Column(db.Text)
    date_posted = db.Column(db.DateTime(), default=datetime.utcnow)
    slug = db.Column(db.String(255))
    poster_id = db.Column(db.Integer, db.ForeignKey('users.id'))

# Create User Model
class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    profile_picture = db.Column(db.String(2000), nullable=True)
    password_hash = db.Column(db.String(128)) 
    posts = db.relationship('Posts', backref='poster')


    @property
    def password(self):
        raise AttributeError('password is not a readable attribute!')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Create String
    def __repr__(self):
        return '<Name %r> % self.name'

# Index 
@app.route('/')
def index():
    posts = Posts.query.order_by(Posts.date_posted)
    return render_template('index.html', posts=posts)
    
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

# Navbar

# Pass Stuff to Navbar
@app.context_processor
def base():
    form = SearchForm()
    return dict(form=form)

# Search Function
@app.route('/search', methods=["POST"])
def search():
    form = SearchForm()
    posts = Posts.query
    if form.validate_on_submit():
        # Get Data from submitted form
        post.searched = form.searched.data
        # Query the Database
        posts = posts.filter(Posts.content.like('%' + post.searched + '%'))
        posts = posts.order_by(Posts.title).all()

        return render_template("search.html", form=form, searched=post.searched, posts=posts)

# Admin Section
    
# Admin page
@app.route('/admin')
@login_required
def admin():
    id = current_user.id
    if id == 16:
        return render_template('admin.html')
    else: 
        flash('Sorry, you must be admin to access this area')
        return redirect(url_for('dashboard'))

    return render_template("admin.html")



# Posts 

# Add Post Page 
@app.route('/add_posts', methods=['GET', 'POST'])
@login_required
def add_post():
    form = PostForm()
    if form.validate_on_submit():
        poster = current_user.id
        post = Posts(title=form.title.data, content=form.content.data, poster_id= poster, slug=form.slug.data)
       # Clear the form
        form.title.data = ''
        form.content.data = ''
        # form.author.data = ''
        form.slug.data = ''

        # Add post data to db
        db.session.add(post)
        db.session.commit()

        #Success Toast
        flash("Blog Post Submitted Successfully!!")

     # Return to page    
    return render_template("add_post.html", form=form)

# Update Posts 
@app.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    form = UserForm()
    name_to_update = Users.query.get_or_404(id)
    if request.method == 'POST':
        name_to_update.name = request.form['name']
        name_to_update.email = request.form['email']
        name_to_update.username = request.form['username']
        try:
            db.session.commit()
            flash("User Updated Successfully!")
            return render_template("update.html", form=form, name_to_update=name_to_update, id=id)
        except:
            flash("Error! Looks like there was a problem... Try Again!")
            return render_template("update.html", form=form, name_to_update=name_to_update, id=id)

    else:
        return render_template("update.html", form=form, name_to_update=name_to_update, id=id)

@app.route('/posts')
def posts():
    posts = Posts.query.order_by(Posts.date_posted)
    return render_template('posts.html', posts=posts)

@app.route('/posts/<int:id>')
def post(id):
    post = Posts.query.get_or_404(id)
    return render_template("post.html", post=post)

@app.route('/posts/edit/<int:id>', methods=['GET','POST'])
@login_required
def edit_post(id):
    post = Posts.query.get_or_404(id)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.slug = form.slug.data
        post.content = form.content.data
        # Update Database
        db.session.add(post)
        db.session.commit()
        flash("Post Has Been Updated!!")
        return redirect(url_for('post', id=post.id))

    if current_user.id == post.poster_id:
        form.title.data = post.title
        form.slug.data = post.slug
        form.content.data = post.content
        return render_template('edit_post.html', form = form )
    else:
        flash("Not Authorized to Edit This Post")
        posts = Posts.query.order_by(Posts.date_posted)
        return render_template('posts.html', posts=posts)

# Delete Post
@app.route('/posts/delete/<int:id>')
@login_required
def delete_post(id):
    post_to_delete = Posts.query.get_or_404(id)
    id = current_user.id 
    if id == post_to_delete.poster.id or id == 16:

        try:
            db.session.delete(post_to_delete)
            db.session.commit()
            # Return message
            flash("Blog Post Was Deleted!!")
            # Redirect to posts page
            posts = Posts.query.order_by(Posts.date_posted)
            return render_template('posts.html', posts=posts)
        except: 
            flash("Whoops!!... There was a problem deleting the post!!")
            # Redirect to posts page
            posts = Posts.query.order_by(Posts.date_posted)
            return render_template('posts.html', posts=posts)   
    else:
        flash("You Aren't Authorized to Delete That Post")

        posts = Posts.query.order_by(Posts.date_posted)
        return render_template("posts.html", posts=posts)


# Create Login Page
@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                flash("Login Successful")
                return redirect(url_for('dashboard'))
            else:
                flash("Wrong Password - Try Again!")
        else:
            flash("That User Doesn't Exist! Try again!")

    return render_template('login.html', form=form)

# Create Logout 
@app.route('/logout', methods=['GET','POST'])
@login_required
def logout():
    logout_user()
    flash("You Have Succesfully Logged Out!")
    return redirect(url_for('login'))

# Create Dashboard Page
@app.route('/dashboard', methods=['GET','POST'])
@login_required
def dashboard():
    form = UserForm()
    id = current_user.id
    name_to_update = Users.query.get_or_404(id)
    if request.method == 'POST':
        name_to_update.name = request.form['name']
        name_to_update.email = request.form['email']
        name_to_update.username = request.form['username']

        # Check for Profile Pic
        if request.files['profile_picture']:
            name_to_update.profile_picture = request.files['profile_picture']

            # Grab Image Name
            pic_filename = secure_filename(name_to_update.profile_picture.filename)
            pic_name = str(uuid.uuid1()) + "-" + pic_filename
            # Save Pic
            saver = request.files['profile_picture']
            # change to string
            name_to_update.profile_picture = pic_name

            try:
                db.session.commit()
                saver.save(os.path.join(app.config['UPLOAD_FOLDER'], pic_name))

                flash("User Updated Successfully!")
                return render_template("dashboard.html", form=form, name_to_update=name_to_update)
            except:
                flash("Error! Looks like there was a problem... Try Again!")
                return render_template("dashboard.html", form=form, name_to_update=name_to_update)
        else:
            db.session.commit()
            flash('User Updated Successfully!')
            return render_template("dashboard.html", form=form, name_to_update=name_to_update)

    else:
        return render_template("dashboard.html", form=form, name_to_update=name_to_update, id=id)
    return render_template('dashboard.html')

# User Actions

# Add a User 
@app.route('/user/add', methods=['GET', 'POST'])
def add_user():
    name = None
    form = UserForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user is None:
            # Hash the password!!
            hashed_pw = generate_password_hash(form.password_hash.data, "sha256")
            user = Users(name=form.name.data, username=form.username.data, email=form.email.data, password_hash=hashed_pw)
            db.session.add(user)
            db.session.commit()
        name = form.name.data
        form.username.data = ''
        form.name.data = ''
        form.email.data = ''
        form.password_hash.data = ''
        
        flash("User Added Successfully!!")
    our_users = Users.query.order_by(Users.date_added)
    return render_template("add_user.html", form = form, name = name, our_users = our_users )


# Delete a user
@app.route('/delete/<int:id>')
@login_required
def delete(id):
    if id == current_user.id:

        user_to_delete = Users.query.get_or_404(id)
        name = None
        form = UserForm()

        try:
            db.session.delete(user_to_delete)
            db.session.commit()
            flash("User Deleted Successfully!!")

            our_users = Users.query.order_by(Users.date_added)
            return render_template("add_user.html", form=form, name=name, our_users=our_users)

        except:
            flash("Whooops! There was a problem deleting user.... Try Again!")
            return render_template("add_user.html", form=form, name=name, our_users=our_users)
    else:
        flash('You are not authorized to Delete this user')
        return redirect(url_for('dashboard'))



# Errors 

    # Invalid URL
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

# Internal Server Error 
@app.errorhandler(500)
def page_not_found(e):
    return render_template("500.html"), 500
