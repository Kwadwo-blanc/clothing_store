from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_required, current_user
from flask_uploads import UploadSet, IMAGES, configure_uploads
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from models import db, User, Product
from auth import auth
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)
app.secret_key = 'supersecret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['UPLOADED_PHOTOS_DEST'] = 'static/images'
photos = UploadSet('photos', IMAGES)
configure_uploads(app, photos)

# Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

db.init_app(app)
app.register_blueprint(auth)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def is_admin():
    return current_user.is_authenticated and current_user.username == 'admin'

@app.route('/')
def index():
    products = Product.query.all()
    return render_template('index.html', products=products)

@app.route('/product/<int:product_id>')
def product(product_id):
    item = Product.query.get_or_404(product_id)
    return render_template('product.html', product=item)

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        name = request.form['name']
        method = request.form['payment_method']
        file = request.files.get('proof')

        filename = None
        if file:
            filename = secure_filename(file.filename)
            photos.save(file, name=filename)

        # Send order to Google Sheets
        log_order_to_sheets(name, method, filename)
        return render_template('thank_you.html', name=name, method=method, filename=filename)
    return render_template('checkout.html')

@app.route('/admin')
@login_required
def admin_dashboard():
    if not is_admin():
        return redirect('/')
    products = Product.query.all()
    return render_template('admin.html', products=products)

@app.route('/admin/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if not is_admin():
        return redirect('/')
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        product = Product(name=name, description=description, price=price)
        db.session.add(product)
        db.session.commit()
        return redirect('/admin')
    return render_template('add_product.html')

@app.route('/admin/delete/<int:id>')
@login_required
def delete_product(id):
    if not is_admin():
        return redirect('/')
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return redirect('/admin')

products = [
    {
        "id": 1,
        "name": "Hoodie",
        "price": 190,
        "image": "images/hoodie_1.jpg"
    }
]

@app.route('/')
def home():
    return render_template('index.html', products=products)


# Google Sheets Logging
def log_order_to_sheets(name, method, filename):
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open('Orders').sheet1
    sheet.append_row([name, method, filename or 'None'])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

