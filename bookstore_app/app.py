from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bookstore.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 🔑 required for session-based login
app.secret_key = 'replace_with_a_random_secret_string'
db = SQLAlchemy(app)

@app.before_request
def require_login():
    # allow login page and static files without authentication
    if request.endpoint in ('login', 'static'):
        return

    # if not logged in, redirect to login page
    if not session.get('logged_in'):
        return redirect(url_for('login'))


# ------------------- MODELS -------------------
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    author_name = db.Column(db.String(100))
    category_name = db.Column(db.String(100))
    price = db.Column(db.Float)
    quantity = db.Column(db.Integer)


class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    book_title = db.Column(db.String(100))
    order_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    quantity = db.Column(db.Integer)
    total_amount = db.Column(db.Float)


# ------------------- ROUTES -------------------


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # 🧠 super simple hard-coded credentials
        # change these if you like
        if username == 'admin' and password == 'admin123':
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('index'))
        else:
            error = 'Invalid username or password'

    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))



@app.route('/')
def index():
    # Count how many books per category for chart
    category_data = db.session.query(Book.category_name, db.func.count(Book.id)).group_by(Book.category_name).all()
    labels = [row[0] for row in category_data]
    counts = [row[1] for row in category_data]
    return render_template('index.html', labels=labels, counts=counts)


# ---------- BOOK CRUD ----------
@app.route('/books', methods=['GET', 'POST'])
def books():
    if request.method == 'POST':
        title = request.form['title']
        author_name = request.form['author_name']
        category_name = request.form['category_name']
        price = request.form['price']
        quantity = request.form['quantity']

        new_book = Book(title=title, author_name=author_name,
                        category_name=category_name, price=price, quantity=quantity)
        db.session.add(new_book)
        db.session.commit()
        return redirect(url_for('books'))

    books = Book.query.all()
    return render_template('books.html', books=books)


@app.route('/delete_book/<int:id>')
def delete_book(id):
    book = Book.query.get_or_404(id)
    db.session.delete(book)
    db.session.commit()
    return redirect(url_for('books'))


@app.route('/update_book_details/<int:id>', methods=['POST'])
def update_book_details(id):
    book = Book.query.get_or_404(id)
    book.author_name = request.form['author_name']
    book.category_name = request.form['category_name']
    book.price = request.form['price']
    book.quantity = request.form['quantity']
    db.session.commit()
    return redirect(url_for('books'))


# ---------- CUSTOMER CRUD ----------
@app.route('/customers', methods=['GET', 'POST'])
def customers():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']

        new_customer = Customer(name=name, email=email, phone=phone)
        db.session.add(new_customer)
        db.session.commit()
        return redirect(url_for('customers'))

    customers = Customer.query.all()
    return render_template('customers.html', customers=customers)


@app.route('/delete_customer/<int:id>')
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    db.session.delete(customer)
    db.session.commit()
    return redirect(url_for('customers'))


# ---------- ORDER CRUD ----------
@app.route('/orders', methods=['GET', 'POST'])
def orders():
    if request.method == 'POST':
        customer_id = request.form['customer_id']
        book_title = request.form['book_title']
        quantity = int(request.form['quantity'])
        price = float(request.form['price'])
        total = price * quantity

        new_order = Order(customer_id=customer_id, book_title=book_title,
                          quantity=quantity, total_amount=total)
        db.session.add(new_order)
        db.session.commit()
        return redirect(url_for('orders'))

    orders = Order.query.all()
    customers = Customer.query.all()
    books = Book.query.all()
    customer_dict = {c.id: c.name for c in customers}
    return render_template('orders.html', orders=orders, customers=customers, books=books,customer_dict=customer_dict )


@app.route('/delete_order/<int:id>')
def delete_order(id):
    order = Order.query.get_or_404(id)
    db.session.delete(order)
    db.session.commit()
    return redirect(url_for('orders'))


# ---------- VIEW UNIQUE AUTHORS ----------
@app.route('/authors')
def view_authors():
    results = db.session.query(Book.author_name, db.func.count(Book.id)).group_by(Book.author_name).all()
    return render_template('authors.html', authors=results)


# ---------- VIEW UNIQUE CATEGORIES ----------
@app.route('/categories')
def view_categories():
    results = db.session.query(Book.category_name, db.func.count(Book.id)).group_by(Book.category_name).all()
    return render_template('categories.html', categories=results)


# ---------- CUSTOMER ORDER HISTORY ----------
@app.route('/customer_orders/<int:customer_id>')
# def customer_orders(customer_id):
#     # Get the customer or 404
#     customer = Customer.query.get_or_404(customer_id)

#     # All orders made by this customer
#     orders = Order.query.filter_by(customer_id=customer_id).all()

#     return render_template(
#         'customer_orders.html',
#         customer=customer,
#         orders=orders
#     )
# ---------- CUSTOMER ORDER HISTORY ----------
@app.route('/customer/<int:id>')
@app.route('/customer_orders/<int:id>')
def customer_orders(id):
    customer = Customer.query.get_or_404(id)
    orders = Order.query.filter_by(customer_id=id).all()
    return render_template('customer_orders.html',
                           customer=customer,
                           orders=orders)


# ------------------- INITIAL SETUP -------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        # Insert sample data if DB is empty
        if not Book.query.first():
            print("⚙️ Inserting sample data...")

            # Books
            b1 = Book(title="Harry Potter and the Philosopher's Stone",
                      author_name="J.K. Rowling", category_name="Fantasy", price=20.99, quantity=10)
            b2 = Book(title="A Game of Thrones",
                      author_name="George R.R. Martin", category_name="Fantasy", price=25.50, quantity=8)
            b3 = Book(title="Success Full of Life",
                      author_name="Raju", category_name="True Events", price=55.00, quantity=100)
            b4 = Book(title="The Silent Patient", author_name="Alex Michaelides",
              category_name="Thriller", price=18.99, quantity=20)
            b5 = Book(title="Atomic Habits", author_name="James Clear",
              category_name="Self-Help", price=16.50, quantity=50)
            b6 = Book(title="The Martian", author_name="Andy Weir",
              category_name="Sci-Fi", price=22.75, quantity=15)
            b7 = Book(title="Pride and Prejudice", author_name="Jane Austen",
              category_name="Romance", price=14.99, quantity=30)
            b8 = Book(title="The Psychology of Money", author_name="Morgan Housel",
              category_name="Business", price=19.99, quantity=40)
            b9 = Book(title="Gone Girl", author_name="Gillian Flynn",
              category_name="Mystery", price=17.50, quantity=25)
            b10 = Book(title="The Shining", author_name="Stephen King",
               category_name="Horror", price=21.99, quantity=12)

            db.session.add_all([b1,b2,b3,b4,b5,b6,b7,b8,b9,b10])


            # Customers
            cust1 = Customer(name="Alice Johnson", email="alice@yahoo.com", phone="1234567890")
            cust2 = Customer(name="Bob Smith", email="bob@gmail.com", phone="9876543210")
            c3 = Customer(name="Jaykumar", email="jay@gamil.com", phone="9998887777")
            c4 = Customer(name="Kallu", email="kallu@gmail.com", phone="9123456780")
            c5 = Customer(name="Karun", email="karun@gmail.com", phone="9988776655")
            c6 = Customer(name="Manu", email="manu@gmail.com", phone="9090909090")
            c7 = Customer(name="Sneha Rao", email="sneha@gmail.com", phone="8887776666")
            c8 = Customer(name="Vishal Gupta", email="vishal@egmail.com", phone="7788996655")
            c9 = Customer(name="Ananya Sharma", email="ananya@gmail.com", phone="8899776655")
            c10 = Customer(name="Rohit Kumar", email="rohit@gmail.com", phone="7008009001")
            db.session.add_all([cust1, cust2,c3, c4,c5,c6,c7,c8,c9,c10])

            # Orders
            o1 = Order(customer_id=1, book_title=b1.title, quantity=2, total_amount=b1.price * 2)
            o2 = Order(customer_id=2, book_title=b2.title, quantity=1, total_amount=b2.price)
            o3 = Order(customer_id=3, book_title=b5.title, quantity=3, total_amount=b5.price * 3)
            o4 = Order(customer_id=4, book_title=b3.title, quantity=1, total_amount=b3.price)
            o5 = Order(customer_id=5, book_title=b7.title, quantity=2, total_amount=b7.price * 2)
            o6 = Order(customer_id=6, book_title=b10.title, quantity=1, total_amount=b10.price)
            o7 = Order(customer_id=7, book_title=b4.title, quantity=4, total_amount=b4.price * 4)
            o8 = Order(customer_id=8, book_title=b8.title, quantity=1, total_amount=b8.price)
            o9 = Order(customer_id=9, book_title=b6.title, quantity=2, total_amount=b6.price * 2)
            o10 = Order(customer_id=10, book_title=b9.title, quantity=1, total_amount=b9.price)
            db.session.add_all([o1, o2,o3,o4,o5,o6,o7,o8,o9,o10])

            db.session.commit()
            print("✅ Sample data inserted successfully!")

    app.run(debug=True)
