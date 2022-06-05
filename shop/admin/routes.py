from flask import render_template, session, request, redirect, url_for, flash

from shop import app, db, bcrypt, Mail, Message, mail
from .forms import RegistrationForm, LoginForm
from .models import User
from shop.products.models import Addproduct, Brand, Category, Feedback
import os


@app.route('/admin')
def admin():
    if 'email' not in session:
        flash(f'Please login first', 'danger')
        return redirect(url_for('login'))
    products = Addproduct.query.all()
    return render_template('admin/index.html', title="Admin page", products=products)


@app.route('/brands')
def brands():
    if 'email' not in session:
        flash(f'Please login first', 'danger')
        return redirect(url_for('login'))
    brands = Brand.query.order_by(Brand.id.desc()).all()
    return render_template('admin/brand.html', title="Brand page", brands=brands)


@app.route('/category')
def category():
    if 'email' not in session:
        flash(f'Please login first', 'danger')
        return redirect(url_for('login'))
    categories = Category.query.order_by(Category.id.desc()).all()
    return render_template('admin/brand.html', title="Brand page", categories=categories)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        hash_password = bcrypt.generate_password_hash(form.password.data)
        user = User(first_name=form.first_name.data, last_name=form.last_name.data, username=form.username.data,
                    email=form.email.data, password=hash_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Welcome {form.first_name.data} {form.last_name.data} Thanks you for registering', 'success')
        return redirect(url_for('login'))
    return render_template('admin/register.html', form=form, title="Registration page")


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if request.method == "POST" and form.validate():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            session['email'] = form.email.data
            flash(f'Welcome {form.email.data} You are login now ', 'success')
            return redirect(request.args.get('next') or url_for('admin'))
        else:
            flash('Wrong Password please try againe', 'danger')
    return render_template('admin/login.html', form=form, title="Login Page")


@app.route('/feedback', methods=['POST', 'GET'])
def feedback():
    if 'email' not in session:
        flash(f'Please login first', 'danger')
        return redirect(url_for('login'))
    feedbacks = Feedback.query.order_by(Feedback.id.desc()).all()

    return render_template('admin/Feedback.html', title="Feedback page", feedbacks=feedbacks)


@app.route('/sent_msg/<int:id>', methods=['POST', 'GET'])
def sent_msg(id):
    feedback = Feedback.query.get_or_404(id)
    if request.method == "POST":
        sent_text = request.form.get('message')
        msg = Message("HEY", sender="noreply@demo.com", recipients=[feedback.email])
        msg.body = f"{sent_text}"
        # mail.send(msg)
        flash("Reset request sent", "success")
        feedback.status = 'Sent'
        db.session.commit()
        return redirect(url_for("feedback"))
    else:
        flash("Email not found", "error")
        return redirect(url_for("feedback"))
