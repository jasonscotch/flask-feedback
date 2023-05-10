from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Feedback
from forms import UserForm, UserLoginForm, UserFeedbackForm
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config.from_pyfile('config.py')

app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///feedback"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True

app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False


connect_db(app)
db.create_all()

toolbar = DebugToolbarExtension(app)


@app.route('/')
def home_page():
    return redirect('/register')

@app.route('/register', methods=["GET", "POST"])
def register_user():
    """Registration page for a new user to sign up."""
    if "username" in session:
        return redirect(f"/users/{session['username']}")
    
    form = UserForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        
        new_user = User.register(
            username,
            password,
            email,
            first_name,
            last_name)
        
        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            form.username.errors.append('Username/email taken. Please pick another.')
            return render_template('register.html', form=form)
        session['username'] = new_user.username
        
        flash('Welcome! Successfully Created Your Account! ', 'success')
        return redirect(f'/users/{username}')
        
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login_user():
    """Logs in a user"""
    if "username" in session:
        return redirect(f"/users/{session['username']}")
    
    form = UserLoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        user = User.authenticate(username, password)
        if user:
            flash(f"Welcome Back, {user.username}!", 'success')
            session['username'] = user.username
            return redirect(f'/users/{user.username}')
        else:
            form.username.errors = ['Invalid username/password']
            
    return render_template('login.html', form=form)

@app.route('/users/<username>')
def secret(username):
    """Display's info on a user and their feedback"""
    if 'username' not in session:
        flash('Please login first!', 'danger')
        return redirect('/login')
    info = User.query.get_or_404(username)
    return render_template('info.html', info=info)

@app.route('/users/<username>/delete')
def delete_user(username):
    """Delete a user"""
    if 'username' not in session:
        flash('Please login first!', 'danger')
        return redirect('/login')
    
    user = User.query.get_or_404(username)
    if user.username == session['username']:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted', 'success')
        return redirect('/')
    flash("You don't have permission to do that")
    return redirect(f'/users/{username}')

@app.route('/users/<username>/feedback/add', methods=["GET", "POST"])
def create_feedback(username):
    """Creates a new feedback for a specific user"""
    if 'username' not in session:
        flash('Please login first!', 'danger')
        return redirect('/login')
    
    form = UserFeedbackForm()
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
    
        new_feedback = Feedback(title=title, content=content, username=session['username'])
        db.session.add(new_feedback)
        db.session.commit()
        flash('Feedback Created!', 'success')
        return redirect(f"/users/{username}")

    return render_template('new_feedback.html', form=form)

@app.route('/feedback/<int:id>/update', methods=["GET", "POST"])
def update_feedeback(id):
    """Submits updates to a user's feedback to the db and redirects back to the users main page"""
    if 'username' not in session:
        flash('Please login first!', 'danger')
        return redirect('/login')
    
    feedback = Feedback.query.get_or_404(id)
    form = UserFeedbackForm()
    
    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data
        db.session.commit()
        flash('Feedback Updated!', 'success')
        return redirect(f"/users/{feedback.username}")
    
    form.title.data = feedback.title
    form.content.data = feedback.content

    return render_template('edit_feedback.html', form=form)
        
        

@app.route('/feedback/<int:id>/delete', methods=["POST"])
def delete_feedback(id):
    """Deletes a users feedback"""
    if 'username' not in session:
        flash('Please login first!', 'danger')
        return redirect('/login')
    
    feedback = Feedback.query.get_or_404(id)
    if feedback.username == session['username']:
        db.session.delete(feedback)
        db.session.commit()
        flash('Feedback deleted', 'success')
        return redirect(f'/users/{feedback.username}')
    flash("You don't have permission to do that")
    return redirect(f'/users/{feedback.username}')



@app.route('/logout')
def logout_user():
    """Logs a user out"""
    session.pop('username')
    flash('Goodbye!', 'primary')
    return redirect('/login')