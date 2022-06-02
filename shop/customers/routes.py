from flask import render_template, session, request, redirect, url_for, flash, current_app, make_response
from flask_login import login_required, current_user, logout_user, login_user
from shop import app, db, photos, search, bcrypt, login_manager
from .forms import CustomerRegisterForm, CustomerLoginForm, CustomerUpdateForm
from .model import Register, CustomerOrder
import secrets
import os
import pdfkit
import stripe

from ..products.routes import categories, brands

buplishable_key = 'pk_test_51L2dsPGGVqgwPrgwJO0OgQLQImHo8ovqtn0xj91OnSISjkIKnWaDB6KRddENtxmxPLUdrr6S162q3riNrgqa9vXz00jnwWAhG9'
stripe.api_key = 'sk_test_51L2dsPGGVqgwPrgwy84LTBkLLqYcJ4BClCifFNEBDdmsvOyOYfzgvyuHUsPoRoN4sdpNoyqlH42G4vWAKIngLqwB00dOljkwMX'


@app.route('/payment', methods=['POST'])
@login_required
def payment():
    invoice = request.form.get('invoice')
    amount = request.form.get('amount')
    customer = stripe.Customer.create(
        email=request.form['stripeEmail'],
        source=request.form['stripeToken'],
    )
    charge = stripe.Charge.create(
        customer=customer.id,
        description='Online Market',
        amount=amount,
        currency='usd',
    )
    orders = CustomerOrder.query.filter_by(customer_id=current_user.id, invoice=invoice).order_by(
        CustomerOrder.id.desc()).first()
    orders.status = 'Paid'
    db.session.commit()
    return redirect(url_for('thanks'))


@app.route('/thanks')
def thanks():
    return render_template('customer/thanks.html')


@app.route('/customer/register', methods=['GET', 'POST'])
def customer_register():
    form = CustomerRegisterForm()
    if form.validate_on_submit():
        hash_password = bcrypt.generate_password_hash(form.password.data)
        register = Register(first_name=form.first_name.data, last_name=form.last_name.data, username=form.username.data,
                            email=form.email.data,
                            password=hash_password, country=form.country.data, city=form.city.data,
                            contact=form.contact.data,
                            address=form.address.data)
        db.session.add(register)
        flash(f'Welcome {form.first_name.data} {form.last_name.data} Thank you for register', 'success')
        db.session.commit()
        return redirect(url_for('customerLogin'))
    return render_template('customer/register.html', form=form)


@login_required
@app.route('/customerupdate/', methods=["POST", "GET"])
def customer_update():
    if current_user.is_authenticated:
        customer_id = current_user.id
    customer = Register.query.get_or_404(customer_id)
    form = CustomerUpdateForm()
    print(customer.password)
    if request.method == "POST":
        if form.password.data == "":
            customer.password = customer.password
        else:
            hash_password = bcrypt.generate_password_hash(form.password.data)
            customer.password = hash_password
        customer.first_name = form.first_name.data
        customer.last_name = form.last_name.data
        customer.username = form.username.data
        customer.email = form.email.data
        customer.country = form.country.data
        customer.city = form.city.data
        customer.contact = form.contact.data
        customer.address = form.address.data
        if request.files.get('profile'):
            try:
                os.unlink(os.path.join(current_app.root_path, "static/images/" + customer.profile))
                customer.profile = photos.save(request.files.get('profile'), name=secrets.token_hex(10) + ".")
            except:
                customer.profile = photos.save(request.files.get('profile'), name=secrets.token_hex(10) + ".")
        db.session.commit()
        return redirect(url_for('profile_info'))
    form.first_name.data = customer.first_name
    form.last_name.data = customer.last_name
    form.username.data = customer.username
    form.email.data = customer.email
    form.country.data = customer.country
    form.city.data = customer.city
    form.contact.data = customer.contact
    form.address.data = customer.address
    return render_template('customer/updateprofile.html', form=form, customer=customer, categories=categories(),
                           brands=brands())


@login_required
@app.route('/profileinfo')
def profile_info():
    if current_user.is_authenticated:
        customer_id = current_user.id
    customer = Register.query.get_or_404(customer_id)
    return render_template('customer/profileinfo.html', customer=customer, categories=categories(),
                           brands=brands())


@app.route('/customer/login', methods=['GET', 'POST'])
def customerLogin():
    form = CustomerLoginForm()
    if form.email.data == "admin" and form.password.data == "admin":
        return redirect(url_for('login'))
    if form.validate_on_submit():
        user = Register.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('You are login now!', 'success')
            next = request.args.get('next')
            return redirect(next or url_for('home'))
        flash('Incorrect email and password', 'danger')
        return redirect(url_for('customerLogin'))
    return render_template('customer/login.html', form=form)


@app.route('/customer/logout')
def customer_logout():
    logout_user()
    return redirect(url_for('home'))


def updateshoppingcart():
    for key, shopping in session['Shoppingcart'].items():
        session.modified = True
        del shopping['image']
        del shopping['colors']
    return updateshoppingcart


@app.route('/getorder')
@login_required
def get_order():
    if current_user.is_authenticated:
        customer_id = current_user.id
        invoice = secrets.token_hex(5)
        updateshoppingcart()
        try:
            order = CustomerOrder(invoice=invoice, customer_id=customer_id, orders=session['Shoppingcart'])
            db.session.add(order)
            db.session.commit()
            session.pop('Shoppingcart')
            flash('You order has been sent success', 'success')
            return redirect(url_for('orders', invoice=invoice))
        except Exception as e:
            print(e)
            flash('Some thing went wrong while get order', 'danger')
            return redirect(url_for('getCat'))


@app.route('/orders/<invoice>')
@login_required
def orders(invoice):
    if current_user.is_authenticated:
        grandTotal = 0
        subTotal = 0
        customer_id = current_user.id
        customer = Register.query.filter_by(id=customer_id).first()
        orders = CustomerOrder.query.filter_by(customer_id=customer_id, invoice=invoice).order_by(
            CustomerOrder.id.desc()).first()
        for _key, product in orders.orders.items():
            discount = (product['discount'] / 100) * float(product['price'])
            subTotal += float(product['price']) * int(product['quantity'])
            subTotal -= discount
            tax = ("%.2f" % (.06 * float(subTotal)))
            grandTotal = ("%.2f" % (1.06 * float(subTotal)))

    else:
        return redirect(url_for('customerLogin'))
    return render_template('customer/order.html', invoice=invoice, tax=tax, subTotal=subTotal, grandTotal=grandTotal,
                           customer=customer, orders=orders)


@app.route('/get_pdf/<invoice>', methods=['POST', 'GET'])
@login_required
def get_pdf(invoice):
    if current_user.is_authenticated:
        grandTotal = 0
        subTotal = 0
        customer_id = current_user.id
        if request.method == "POST":
            customer = Register.query.filter_by(id=customer_id).first()
            orders = CustomerOrder.query.filter_by(customer_id=customer_id, invoice=invoice).order_by(
                CustomerOrder.id.desc()).first()
            for _key, product in orders.orders.items():
                discount = (product['discount'] / 100) * float(product['price'])
                subTotal += float(product['price']) * int(product['quantity'])
                subTotal -= discount
                tax = ("%.2f" % (.06 * float(subTotal)))
                grandTotal = float("%.2f" % (1.06 * subTotal))

            rendered = render_template('customer/pdf.html', invoice=invoice, tax=tax, grandTotal=grandTotal,
                                       customer=customer, orders=orders)
            config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
            rendered = render_template('customer/pdf.html', invoice=invoice, tax=tax, grandTotal=grandTotal,
                                       customer=customer, orders=orders)
            pdf = pdfkit.from_string(rendered, False, configuration=config)
            response = make_response(pdf)
            response.headers['content-Type'] = 'application/pdf'
            response.headers['content-Disposition'] = 'inline; filename=' + invoice + '.pdf'
            # response.headers['content-Disposition'] = 'atteched; filename=' + invoice + '.pdf'
            return response
    return request(url_for('orders'))


@app.route('/customerorder')
@login_required
def customer_order():
    if current_user.is_authenticated:
        customer_id = current_user.id
    orders = CustomerOrder.query.filter_by(customer_id=customer_id)
    return render_template('customer/customer_order.html', categories=categories(),
                           brands=brands(), orders=orders)


@app.route('/orderss/<invoice>')
@login_required
def orderss(invoice):
    if current_user.is_authenticated:
        grandTotal = 0
        subTotal = 0
        customer_id = current_user.id
        customer = Register.query.filter_by(id=customer_id).first()
        orders = CustomerOrder.query.filter_by(customer_id=customer_id, invoice=invoice).order_by(
            CustomerOrder.id.desc()).first()
        for _key, product in orders.orders.items():
            discount = (product['discount'] / 100) * float(product['price'])
            subTotal += float(product['price']) * int(product['quantity'])
            subTotal -= discount
            tax = ("%.2f" % (.06 * float(subTotal)))
            grandTotal = ("%.2f" % (1.06 * float(subTotal)))

    else:
        return redirect(url_for('customerLogin'))
    return render_template('customer/orderss.html', invoice=invoice, tax=tax, subTotal=subTotal, grandTotal=grandTotal,
                           customer=customer, orders=orders, categories=categories(),
                           brands=brands())
