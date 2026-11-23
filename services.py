import hashlib
import hmac
import os

ROLES = ('Manager','Waiter','Kitchen','Cashier')

def password_hash(password):
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 200_000)
    return salt.hex() + ':' + digest.hex()

def password_verify(password, stored):
    try:
        salt, digest = stored.split(':', 1)
        actual = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 200_000)
        return hmac.compare_digest(actual, bytes.fromhex(digest))
    except (ValueError, TypeError):
        return False

class RestaurantService:
    def __init__(self, db):
        self.db = db

    def bootstrap_admin(self, password):
        if self.db.one('SELECT 1 FROM users LIMIT 1'):
            return False
        if len(password) < 8:
            raise ValueError('Password must have at least 8 characters')
        with self.db.conn:
            self.db.conn.execute('INSERT INTO users(username,password_hash,role) VALUES(?,?,?)', ('admin',password_hash(password),'Manager'))
        return True

    def login(self, username, password):
        user = self.db.one('SELECT * FROM users WHERE username=?', (username,))
        return dict(user) if user and password_verify(password,user['password_hash']) else None

    def create_user(self, username, password, role):
        if role not in ROLES or not username.strip() or len(password)<8:
            raise ValueError('Invalid username, role or password (minimum 8 characters)')
        with self.db.conn:
            self.db.conn.execute('INSERT INTO users(username,password_hash,role) VALUES(?,?,?)', (username.strip(),password_hash(password),role))

    def tables(self):
        return self.db.all('SELECT * FROM dining_tables ORDER BY id')

    def menu(self, include_unavailable=False):
        return self.db.all('SELECT * FROM menu_items ' + ('' if include_unavailable else 'WHERE available=1 ') + 'ORDER BY category,name')

    def add_menu_item(self, name, category, price):
        if not name.strip() or not category.strip() or int(price)<0:
            raise ValueError('Invalid menu item')
        with self.db.conn:
            self.db.conn.execute('INSERT INTO menu_items(name,category,price) VALUES(?,?,?)',(name.strip(),category.strip(),int(price)))

    def update_menu_item(self, item_id, name, category, price, available):
        if not name.strip() or not category.strip() or int(price)<0:
            raise ValueError('Invalid menu item')
        with self.db.conn:
            cur=self.db.conn.execute('UPDATE menu_items SET name=?,category=?,price=?,available=? WHERE id=?', (name.strip(),category.strip(),int(price),int(bool(available)),item_id))
            if not cur.rowcount: raise ValueError('Item not found')

    def create_order(self, table_id):
        with self.db.conn:
            table=self.db.one('SELECT status FROM dining_tables WHERE id=?',(table_id,))
            if not table or table['status']!='Available': raise ValueError('Table is not available')
            cur=self.db.conn.execute('INSERT INTO orders(table_id) VALUES(?)',(table_id,))
            self.db.conn.execute("UPDATE dining_tables SET status='Occupied' WHERE id=?",(table_id,))
            return cur.lastrowid

    def active_orders(self):
        return self.db.all("SELECT o.id,o.table_id,t.name AS table_name,o.created_at FROM orders o JOIN dining_tables t ON t.id=o.table_id WHERE o.status='Active' ORDER BY o.id DESC")

    def add_item(self, order_id, item_id, qty, note=''):
        qty=int(qty)
        if qty<=0: raise ValueError('Quantity must be positive')
        with self.db.conn:
            if not self.db.one("SELECT 1 FROM orders WHERE id=? AND status='Active'",(order_id,)): raise ValueError('Order is not active')
            item=self.db.one('SELECT * FROM menu_items WHERE id=? AND available=1',(item_id,))
            if not item: raise ValueError('Dish is unavailable')
            self.db.conn.execute('INSERT INTO order_details(order_id,item_id,quantity,unit_price,note) VALUES(?,?,?,?,?)',(order_id,item_id,qty,item['price'],note))

    def details(self, order_id):
        return self.db.all('SELECT d.*,m.name AS item_name FROM order_details d JOIN menu_items m ON m.id=d.item_id WHERE d.order_id=? ORDER BY d.id',(order_id,))

    def remove_item(self, detail_id):
        with self.db.conn:
            row=self.db.one('SELECT o.status,d.status AS item_status FROM order_details d JOIN orders o ON o.id=d.order_id WHERE d.id=?',(detail_id,))
            if not row or row['status']!='Active' or row['item_status']!='Pending': raise ValueError('Only pending items in active orders may be removed')
            self.db.conn.execute('DELETE FROM order_details WHERE id=?',(detail_id,))

    def update_quantity(self, detail_id, qty):
        qty=int(qty)
        if qty<=0: raise ValueError('Quantity must be positive')
        with self.db.conn:
            row=self.db.one('SELECT o.status,d.status AS item_status FROM order_details d JOIN orders o ON o.id=d.order_id WHERE d.id=?',(detail_id,))
            if not row or row['status']!='Active' or row['item_status']!='Pending': raise ValueError('Only pending items can be edited')
            self.db.conn.execute('UPDATE order_details SET quantity=? WHERE id=?',(qty,detail_id))

    def kitchen_items(self):
        return self.db.all("SELECT d.id,d.quantity,d.note,d.status,m.name AS item_name,t.name AS table_name FROM order_details d JOIN orders o ON o.id=d.order_id JOIN dining_tables t ON t.id=o.table_id JOIN menu_items m ON m.id=d.item_id WHERE o.status='Active' ORDER BY d.id DESC")

    def set_kitchen_status(self, detail_id, status):
        transitions={'Pending':'Cooking','Cooking':'Ready'}
        with self.db.conn:
            row=self.db.one('SELECT status FROM order_details WHERE id=?',(detail_id,))
            if not row or transitions.get(row['status'])!=status: raise ValueError('Invalid kitchen status transition')
            self.db.conn.execute('UPDATE order_details SET status=? WHERE id=?',(status,detail_id))

    def total(self, order_id):
        row=self.db.one('SELECT COALESCE(SUM(quantity*unit_price),0) AS total FROM order_details WHERE order_id=?',(order_id,))
        return row['total']

    def checkout(self, order_id, method, discount=0):
        discount=int(discount)
        if method not in ('Cash','Card','QR') or discount<0: raise ValueError('Invalid payment')
        with self.db.conn:
            order=self.db.one("SELECT * FROM orders WHERE id=? AND status='Active'",(order_id,))
            if not order: raise ValueError('Order is not active')
            if not self.details(order_id): raise ValueError('Cannot pay an empty order')
            if any(d['status']!='Ready' for d in self.details(order_id)): raise ValueError('All dishes must be ready before checkout')
            subtotal=self.total(order_id)
            if discount>subtotal: raise ValueError('Discount exceeds subtotal')
            self.db.conn.execute("UPDATE orders SET status='Paid',payment_method=?,discount=?,paid_at=CURRENT_TIMESTAMP WHERE id=?",(method,discount,order_id))
            self.db.conn.execute("UPDATE dining_tables SET status='Available' WHERE id=?",(order['table_id'],))
            self.db.conn.execute('INSERT INTO audit_log(event) VALUES(?)',(f'Order {order_id} paid {subtotal-discount} by {method}',))
            return subtotal-discount

    def report(self):
        return self.db.one("SELECT COUNT(*) AS orders,COALESCE(SUM((SELECT COALESCE(SUM(quantity*unit_price),0) FROM order_details WHERE order_id=o.id)-discount),0) AS revenue FROM orders o WHERE status='Paid'")
