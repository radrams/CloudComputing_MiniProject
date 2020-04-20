import random
import urllib
import json
import urllib.request as urllib2
import urllib.parse
import os
import logging

from OpenSSL import SSL
from cassandra.cluster import Cluster
from flask_httpauth import HTTPBasicAuth
from werkzeug.utils import secure_filename, redirect
from flask import flash, Flask, render_template, request, jsonify, url_for, g
from passlib.apps import custom_app_context as pwd_context

# setting up the logging configuration
logger = logging.getLogger('spam_application')
logger.setLevel(logging.DEBUG)

# flask configuration
app = Flask(__name__)
app.secret_key = 'random string'

# useful variables initialization
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = set(['jpeg', 'jpg', 'png', 'gif'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# keys for external APIs
openWeatherMapApiKey = '22aa4e3ea521bac386358325c77e43fa'
openExchangeRateApiKey = '24e91f44fb2d4e9f9f0b8554f5bbdb1d'
DEFAULTS = {'city': 'London,UK',
            'currency_from': 'GBP',
            'currency_to_usd': 'USD',
            'currency_to_eur': 'EUR'
            }
current_location_url = 'http://ipinfo.io/json'
weather_url_template = 'http://api.openweathermap.org/data/2.5/weather?q={}&units=metric&appid={}'
exchange_url_template = 'https://openexchangerates.org//api/latest.json?app_id={}'

# cassandra keyspace custom name
KEYSPACE = "ks"

# cassandra cluster configurations
cluster = Cluster(contact_points=['172.17.0.2'], port=9042)
session = cluster.connect()

# HTTP authentication for Flask routes
auth = HTTPBasicAuth()

# self-signed ssl certificate context initialization
context = SSL.Context(SSL.SSLv23_METHOD)

# class to store the current user details
class User:
    username = ""
    password_hash = ""
    role = ""

    def __init__(self, username, password_hash, role):
        self.username = username
        self.password_hash = password_hash
        self.role = role

    def update_password_hash(self, password_hash):
        self.password_hash = password_hash

    def update_role(self, role):
        self.role = role

# function to be run before the first request to this instance of the application
# used for cassandra db initialization
@app.before_first_request
def init_database():
    # creating cassandra keyspace if it is not already created
    session.execute("""
           CREATE KEYSPACE IF NOT EXISTS %s
           WITH replication = { 'class': 'SimpleStrategy', 'replication_factor': '2' }
           """ % KEYSPACE)
    session.set_keyspace(KEYSPACE)

    # creating tables 'users', 'categories' and 'products' if they are not already created
    session.execute("""
        CREATE TABLE IF NOT EXISTS users(      
        username TEXT PRIMARY KEY, 
        firstName TEXT,
        lastName TEXT,
        password_hash TEXT,
        email TEXT,
        role TEXT
        )
    """)

    session.execute("""
        CREATE TABLE IF NOT EXISTS categories(      
        categoryId INT PRIMARY KEY,
        name TEXT
        )
    """)

    session.execute("""
        CREATE TABLE IF NOT EXISTS products(
        productId INT PRIMARY KEY,
        name TEXT,
        price FLOAT,
        description TEXT,
        image TEXT,
        stock INT,
        categoryId INT
        )
        """)

    # populating 'users' table
    keys_users = ["username", "firstName", "lastName", "password_hash", "email", "role"]
    user1 = ['annaheckel', 'Annabel', 'Heckel', pwd_context.hash('mypassword'), 'Annabel.Heckel@gmail.com', 'admin']
    user2 = ['jamespilot', 'James', 'Pilot', pwd_context.hash('mypassword'), 'James.Pillot@gmail.com', 'user']
    dictList = [dict(zip(keys_users, user1)), dict(zip(keys_users, user2))]
    prepared = session.prepare("""
      INSERT INTO users (username, firstName, lastName, password_hash, email, role)
        VALUES (?, ?, ?, ?, ?, ?)
        """)
    for item in dictList:
        session.execute(prepared, ([item[key] for key in keys_users]))

    # populating 'categories' table
    keys_category = ["categoryId", "name"]
    category1 = [1, 'Personal Growth']
    category2 = [2, 'Autobiographies']
    category3 = [3, 'Political Science']
    category4 = [4, 'Fiction']
    category5 = [5, 'Computer Programming']
    dictList = [dict(zip(keys_category, category1)), dict(zip(keys_category, category2)),
                dict(zip(keys_category, category3)), dict(zip(keys_category, category4)),
                dict(zip(keys_category, category5))]
    prepared = session.prepare("""
        INSERT INTO categories (categoryId, name)
        VALUES (?, ?)
        """)
    for item in dictList:
        session.execute(prepared, ([item[key] for key in keys_category]))

    # populating 'products' table
    keys_products = ["productId", "name", "price", "description", "image", "stock", "categoryId"]
    product1 = [1, 'How to win friends & influence people', 95.0,
                'If you are about to enter the corperate world , you have to read this !', 'HowToWinFriends.jpg', 29, 1]
    product2 = [2, 'Seeing like a state', 300.0,
                'James Scott analyses how certain schemes to improve the human condition ahve failed',
                'SeeingLikeAState.jpg', 3, 3]
    product3 = [3, 'Big Data Processing Using Spark in Cloud', 100.0, 'Big Data Processing Using Spark in Cloud',
                'BigDataProcessingUsingSparkInCloud.jpg', 10, 1]
    product4 = [4, 'MasteringCloudComputing', 70.0, 'MasteringCloudComputing', 'MasteringCloudComputing.jpg', 20, 5]
    dictList = [dict(zip(keys_products, product1)), dict(zip(keys_products, product2)),
                dict(zip(keys_products, product3)), dict(zip(keys_products, product4))]
    prepared = session.prepare("""
        INSERT INTO products (productId, name, price, description, image, stock, categoryId)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """)
    for item in dictList:
        session.execute(prepared, ([item[key] for key in keys_products]))

# get the details of currently logged in user
def getLoginDetails():
    loggedIn = True
    rows = session.execute('SELECT firstname FROM users').current_rows
    firstName = rows[1].firstname
    noOfItems = '0'
    return (loggedIn, firstName, noOfItems)

# Function to return the home page of the 'online book shop' application
# @path: /
# @method: GET
# returns: Home page
# no authentication required
@app.route("/", methods=["GET"])
def root():
    loggedIn, firstName, noOfItems = getLoginDetails()

    # get the list of 'products' and categories already available in the database
    itemData = session.execute('SELECT productId, name, price, description, image, stock FROM products')
    categoryData = session.execute('SELECT categoryId, name FROM categories')

    # Makes use of external api to get the current location based on ip address
    city = get_current_location()
    if not city:
        city = DEFAULTS['city']

    # External api GET request call to get the weather for current location
    weather = get_weather(city)

    # External api GET request to get the exchange rates for GBP to USD and EUR
    rate_gbp_usd = round(get_rate(DEFAULTS['currency_from'], DEFAULTS['currency_to_usd']), 2)
    rate_gbp_eur = round(get_rate(DEFAULTS['currency_from'], DEFAULTS['currency_to_eur']), 2)
    # Store response as dictionary
    dict_response = {'categories': categoryData.current_rows, 'products': itemData.current_rows, 'weather': weather,
                     'GBP-USD': rate_gbp_usd, 'GBP-EUR': rate_gbp_eur}

    #  Response based on content type
    #  if json type is requested return json response otherwise return list elements to use dynamically in html web page
    if request.headers.get('Content-Type') == 'application/json':
        return jsonify(dict_response)
    else:
        return render_template('home.html', itemData=itemData.current_rows, loggedIn=loggedIn, firstName=firstName,
                               noOfItems=noOfItems, categoryData=categoryData, weather=weather,
                               currency_from=DEFAULTS['currency_from'], currency_to_usd=DEFAULTS['currency_to_usd'],
                               currency_to_eur=DEFAULTS['currency_to_eur'], rate_usd=rate_gbp_usd,
                               rate_eur=rate_gbp_eur)

# Function to open the 'Add Items' web form to send request to 'addItem' api endpoint
@app.route("/add")
def add():
    categories = session.execute("SELECT categoryId, name FROM categories")
    return render_template('add.html', categories=categories)

# Function to create a new Product in the database. Requires authentication and only 'admin' role can add the product
# @path: /addItem
# @method: POST
# @param: name, price, description, stock, category, image
# @returns: Code 201 if success, 400 or 401 and error message if failure
@app.route("/addItem", methods=["POST"])
@auth.login_required
def addItem():
    # get the request header to differentiate between web request and curl request
    condition_header = ('application/json' in request.headers.get(
        'Content-Type') or 'multipart/form-data' in request.headers.get('Content-Type')) and not (
                'WebKit' in request.headers.get('Content-Type'))

    # only 'admin' users can add the product
    if g.user.role != 'admin':
        if condition_header:
            return jsonify({'error': 'only authorized user can add items'}), 401
        else:
            return redirect(url_for('error', errorCode=401, errorDetails='only authorized user can add items'))

    # if the request does not have required parameters return 400 response, handles curl and web requests
    if condition_header:
        dict_user_data = json.loads(request.form['user_data'])
        values_json = [dict_user_data['name'], dict_user_data['price'], dict_user_data['description'],
                       dict_user_data['stock'],
                       dict_user_data['category']]
        if any((v is None or v == '') for v in values_json):
            return jsonify({'error': 'missing arguments!'}), 400
    else:
        values_web = [request.form['name'], request.form['price'], request.form['description'], request.form['stock'],
                      request.form['category']]
        if any((v is None or v == '') for v in values_web):
            msg = "Error occurred, missing details"
            logger.error(msg)
            print(msg)
            return redirect(url_for('error', errorCode=400, errorDetails=msg))

    # if the price and stock value are in string format return 400 response, handles curl and web requests
    if condition_header:
        dict_user_data = json.loads(request.form['user_data'])
        try:
            name = dict_user_data['name']
            price = float(dict_user_data['price'])
            description = dict_user_data['description']
            stock = int(dict_user_data['stock'])
            categoryId = int(dict_user_data['category'])
        except Exception as e:
            return jsonify({'error': 'Error occurred, Price and Stock should be in Numbers'}), 400
    else:
        try:
            name = request.form['name']
            price = float(request.form['price'])
            description = request.form['description']
            stock = int(request.form['stock'])
            categoryId = int(request.form['category'])
        except Exception as e:
            msg = "Error occurred, Price and Stock should be in Numbers"
            logger.error(msg)
            print(msg)
            return redirect(url_for('error', errorCode=400, errorDetails=msg))

    # Uploading product image procedure
    image = request.files['image']
    if image and allowed_file(image.filename):
        filename = secure_filename(image.filename)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    # if there is not file uploaded parameters return 400 response
    else:
        msg = "Error occurred, missing file"
        logger.error(msg)
        print(msg)
        if condition_header:
            return jsonify({'error': msg}), 400
        else:
            return redirect(url_for('error', errorCode=400, errorDetails=msg))
    imagename = filename

    # insert the new product into db
    try:
        prepared = session.prepare("""
               INSERT INTO products (productid, name, price, description, image, stock, categoryid) VALUES (?, ?, ?, ?, ?, ?, ?)
               """)
        # unique product id
        product_id = random.randint(0, 1000000)
        session.execute(prepared, (product_id, name, price, description, imagename, stock, categoryId))
        flash("Product added successfully!")

        # retrun response for curl and web requests
        if condition_header:
            dict_user_data['image'] = imagename
            dict_user_data['product_id'] = product_id
            return jsonify(dict_user_data), 201
        else:
            return redirect(url_for('root'))
    except Exception as e:
        logger.error('Error adding the product: ' + str(e))
        msg = "error occurred"
        flash("Error occurred while adding the product")
        print(msg)
        if condition_header:
            return jsonify({'error': msg}), 400
        else:
            return redirect(url_for('error', errorCode=400, errorDetails=msg))

# Function to open the 'Remove Items' web page to send request to 'removeItem' api endpoint
@app.route("/remove")
def remove():
    data = session.execute("SELECT productid, name, price, image, stock FROM products")
    return render_template('remove.html', data=data.current_rows)

# Function to delete a Product in the database. Requires authentication and only 'admin' role can add the product
# @path: /removeItem/<productid>
# @method: DELETE
# @returns: 200 if success, 400 or 401 or 404 and error message if failure
@app.route("/removeItem/<product_ID>", methods=['GET', 'DELETE'])
@auth.login_required
def removeItem(product_ID):
    # get the request header to differentiate between web request and curl request
    condition_header = request.headers.get('Content-Type')

    # only 'admin' users can remove the product
    if g.user.role != 'admin':
        if condition_header == 'application/json':
            return jsonify({'error': 'only authorized user can remove items'}), 401
        else:
            return redirect(url_for('error', errorCode=401, errorDetails='only authorized user can remove items'))

    # if the request does not have required parameters return 400 response, handles curl and web requests
    if product_ID is None or product_ID == '':
        if condition_header:
                return jsonify({'error': 'missing arguments, productid!'}), 400
        else:
            msg = "Error, missing arguments, productid"
            logger.error(msg)
            print(msg)
            return redirect(url_for('error', errorCode=400, errorDetails=msg))

    # if the requested product does not exist in the db return 404
    prepared_statement = session.prepare(
        'SELECT productid, name, price, description, image, stock, categoryid FROM products WHERE productid=?')
    rows = session.execute(prepared_statement, (int(product_ID),))
    if (rows is None) or (not rows):
        if condition_header == 'application/json':
            return jsonify({'error': 'productId not found'}), 404
        else:
            return redirect(url_for('error', errorCode=404, errorDetails='productId not found'))

    # delete the product, return 200 code if success else 400 error code
    try:
        session.execute('DELETE FROM products WHERE productid = ' + product_ID)
        msg = "Deleted successfully"
        print(msg)
        if condition_header == 'application/json':
            return jsonify({'success': 'Product deleted'}), 200
        else:
            return redirect(url_for('root'))
    except Exception as e:
        logger.error('Error deleting product: ' + str(e))
        msg = "error occurred"
        flash("Error occurred while deleting product")
        if condition_header == 'application/json':
            return jsonify({'error': 'Error occurred while deleting product'}), 400
        else:
            return redirect(url_for('error', errorCode=400, errorDetails=msg))

# Function to update the stock details of the product. Requires authentication and only 'admin' role can add the product
# @path: /updateStockCount/<product_ID>/<stockCount>
# @method: PUT
# @param: product_ID, stockCount
# @returns: 200 if success, 400 or 401 or 404 and error message if failure
@app.route('/updateStockCount/<product_ID>/<stockCount>', methods=['PUT'])
@auth.login_required
def update_stock_count(product_ID, stockCount):
    # get the request header to differentiate between web request and curl request
    condition_header = 'application/json' in request.headers.get('Content-Type')

    # only 'admin' users can remove the product
    if g.user.role != 'admin':
        if condition_header:
            return jsonify({'error': 'only authorized user can update the stock count'}), 401

    # if the request does not have required parameters return 400 response, handles curl and web requests
    if product_ID is None or product_ID == '' or stockCount is None or stockCount == '':
        if condition_header:
                return jsonify({'error': 'missing arguments, productid or stockcount!'}), 400
        else:
            msg = "Error, missing arguments, productid or stockcount"
            logger.error(msg)
            print(msg)
            return redirect(url_for('error', errorCode=400, errorDetails=msg))

    # if the requested product does not exist in the db return 404
    if condition_header:
        prepared_statement = session.prepare(
            'SELECT productid, name, price, description, image, stock, categoryid FROM products WHERE productid=?')
        rows = session.execute(prepared_statement, (int(product_ID),))
        if (rows is None) or (not rows):
            return jsonify({'error': 'productId not found'}), 404

    # update the stockcount for the given producid, 200 if success, 400 if failure
    try:
        prepared_statement = session.prepare('UPDATE products SET stock = ? WHERE productid = ?')
        rows = session.execute(prepared_statement, (int(stockCount), int(product_ID)))
        msg = "Updated successfully"
        print(msg)
        return jsonify({'productid': product_ID, 'stock': stockCount}), 200
    except Exception as e:
        logger.error('Error updating the stock count: ' + str(e))
        msg = "error occurred"
        flash("Error occurred while updating the stock count")
        return jsonify({'error': 'Error occurred while updating the stock count'}), 400

# error page to display error code along with detailed message
@app.route("/error")
def error():
    return render_template('error.html', errorCode=request.args.get('errorCode'),
                           errorDetails=request.args.get('errorDetails'))

# Makes use of external api to get the current location based on ip address
def get_current_location():
    # Automatically geolocate the connecting IP
    response = urllib2.urlopen(current_location_url)
    json_string = response.read()
    response.close()
    location = json.loads(json_string)
    print(location)
    return location['city']

# External api GET request call to get the weather for current location
def get_weather(query):
    query = urllib.parse.quote(query)
    url = weather_url_template.format(query, openWeatherMapApiKey)
    data = urllib2.urlopen(url).read()
    parsed = json.loads(data)
    weather = None
    if parsed.get("weather"):
        weather = {"description": parsed["weather"][0]["description"], "temperature": parsed["main"]["temp"],
                   "city": parsed["name"]
                   }
    return weather

# External api GET request to get the exchange rates
def get_rate(frm, to):
    CURRENCY_URL = exchange_url_template.format(openExchangeRateApiKey)
    all_currency = urllib2.urlopen(CURRENCY_URL).read()
    parsed = json.loads(all_currency).get('rates')
    frm_rate = parsed.get(frm.upper())
    to_rate = parsed.get(to.upper())
    return to_rate / frm_rate

# utility function to check the allowed file names while adding a new product
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

# Flask-HTTPAuth implementation
# Function to verify the user, using the username and password
@auth.verify_password
def verify_password(username, password):
    # username or password is not given
    if username is None or password is None or username == '' or password == '':
        return False
    prepared_statement = session.prepare("SELECT username, password_hash, role FROM users WHERE username = ?")
    rows = session.execute(prepared_statement, (username,))

    # user does not exist in the database
    if not rows:
        return False
    else:
        user = User(rows.one().username, "", "")
        # verify the password
        if not pwd_context.verify(password, rows.one().password_hash):
            return False
        # store the current user details in the Class
        user.update_password_hash(rows.one().password_hash)
        user.update_role(rows.one().role)
        g.user = user
        return True

if __name__ == '__main__':
    # application over https using self-signed certificates
    context = ('cert.pem', 'key.pem')
    app.run(debug=True, host='0.0.0.0', port=443, ssl_context=context)