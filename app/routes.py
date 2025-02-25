import os
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, Product, Review,Message,Order
from app.forms import RegistrationForm, LoginForm, ProductForm, ReviewForm,MessageForm
from werkzeug.utils import secure_filename

main = Blueprint('main', __name__)


@main.route('/')
def index():
    products = Product.query.all()
    return render_template('index.html', products=products)

@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            flash('Email already registered. Please log in.', 'danger')
            return redirect(url_for('main.login'))

    
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', form=form)

@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('main.index'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html', form=form)


@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


UPLOAD_FOLDER = 'app/static/images' 
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@main.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        if form.image.data:
            file = form.image.data
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(UPLOAD_FOLDER, filename))  # Save the file
                product = Product(name=form.name.data, description=form.description.data,
                                  price=form.price.data, category=form.category.data,
                                  image=filename, seller_id=current_user.id)
                db.session.add(product)
                db.session.commit()
                flash('Product added successfully!', 'success')
                return redirect(url_for('main.index'))
            else:
                flash('Invalid file type. Please upload a PNG or JPG image.', 'danger')
    return render_template('add_product.html', form=form)

@main.route('/product/<int:product_id>', methods=['GET', 'POST'])
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    form = ReviewForm()
    if form.validate_on_submit():
        review = Review(content=form.content.data, rating=form.rating.data,
                        user=current_user, product=product)
        db.session.add(review)
        db.session.commit()
        flash('Your review has been added!', 'success')
        return redirect(url_for('main.product_detail', product_id=product.id))
    return render_template('product_detail.html', product=product, form=form)

@main.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('main.index'))
    products = Product.query.all()
    users = User.query.all()
    return render_template('admin_dashboard.html', products=products, users=users)

@main.route('/wishlist')
@login_required
def wishlist():
    return render_template('wishlist.html')

@main.route('/mark_purchased/<int:product_id>')
@login_required
def mark_purchased(product_id):
    product = Product.query.get_or_404(product_id)
    if product.seller_id != current_user.id:
        flash('You do not have permission to mark this item as purchased.', 'danger')
        return redirect(url_for('main.index'))
    product.status = 'purchased'
    db.session.commit()
    flash('The item has been marked as purchased.', 'success')
    return redirect(url_for('main.index'))

@main.route('/delete_product/<int:product_id>')
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    if product.seller_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to delete this product.', 'danger')
        return redirect(url_for('main.index'))
    db.session.delete(product)
    db.session.commit()
    flash('The product has been deleted.', 'success')
    return redirect(url_for('main.index'))

from datetime import datetime
@main.route ('/messages' ,methods=["GET"])
@login_required
def messages():
     received_messages = Message.query.filter_by(receiver_id=current_user.id).all()
     sent_messages = Message.query.filter_by(sender_id=current_user.id).all()
     return render_template('messages.html', received_messages=received_messages, sent_messages=sent_messages)

@main.route('/send_message/<int:receiver_id>', methods=['GET', 'POST'])
@login_required
def send_message(receiver_id):
    form = MessageForm()
    receiver = User.query.get_or_404(receiver_id)
    if form.validate_on_submit():
        message = Message(sender_id=current_user.id, receiver_id=receiver.id, content=form.content.data)
        db.session.add(message)
        db.session.commit()
        flash('Message sent!', 'success')
        return redirect(url_for('main.messages'))
    return render_template('send_messages.html', form=form, receiver=receiver)

@main.route('/users', methods=['GET'])
@login_required
def users():
    all_users = User.query.all()  # Get all users
    return render_template('users.html', users=all_users)

#@main.route('/sent_messages')
#@login_required
#def sent_messages():
    received_messages = current_user.received_messages.order_by(Message.timestamp.desc()).all()
    sent_messages = current_user.sent_messages.order_by(Message.timestamp.desc()).all()
    return render_template('messages.html', received_messages=received_messages, sent_messages=sent_messages)


@main.route('/add_to_wishlist/<int:product_id>')
@login_required
def add_to_wishlist(product_id):
    product = Product.query.get_or_404(product_id)
    if product not in current_user.wishlist_products:
        current_user.wishlist_products.append(product)
        db.session.commit()
        flash('Product added to wishlist!', 'success')
    else:
        flash('Product is already in your wishlist.', 'info')
    return redirect(url_for('main.product_detail', product_id=product.id))

@main.route('/remove_from_wishlist/<int:product_id>')
@login_required
def remove_from_wishlist(product_id):
    product = Product.query.get_or_404(product_id)
    if product in current_user.wishlist_products:
        current_user.wishlist_products.remove(product)
        db.session.commit()
        flash('Product removed from wishlist!', 'success')
    else:
        flash('Product is not in your wishlist.', 'info')
    return redirect(url_for('main.wishlist'))
#route acces to buy product.
@main.route('/buy_product/<int:product_id>')
@login_required
def buy_product(product_id):
    product = Product.query.get_or_404(product_id)
    if product.seller_id == current_user.id:
        flash('You cannot buy your own product.', 'danger')
        return redirect(url_for('main.product_detail', product_id=product.id))
    order = Order(buyer_id=current_user.id, product_id=product.id)
    db.session.add(order)
    db.session.commit()
    flash('Order placed successfully!', 'success')
    return redirect(url_for('main.product_detail', product_id=product.id))

@main.route('/update_order_status/<int:order_id>/<status>')
@login_required
def update_order_status(order_id, status):
    order = Order.query.get_or_404(order_id)
    if order.product.seller_id != current_user.id:
        flash('You do not have permission to update this order.', 'danger')
        return redirect(url_for('main.index'))
    order.status = status
    db.session.commit()
    flash('Order status updated!', 'success')
    return redirect(url_for('main.orders'))

@main.route('/delete_user/<int:user_id>')
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash('You do not have permission to delete users.', 'danger')
        return redirect(url_for('main.index'))
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash('You cannot delete an admin user.', 'danger')
        return redirect(url_for('main.admin_dashboard'))
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!', 'success')
    return redirect(url_for('main.admin_dashboard'))