import os, secrets, sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort, g
from models.database import Database, DEFAULT_DB
from models.services import RestaurantService, ROLES

def create_app(db_path=DEFAULT_DB):
    app=Flask(__name__)
    app.secret_key=os.environ.get('RESTAURANT_SECRET') or secrets.token_hex(32)
    app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax')
    def service():
        if 'db' not in g: g.db=Database(db_path)
        return RestaurantService(g.db)
    @app.teardown_appcontext
    def close(exc):
        db=g.pop('db',None)
        if db: db.close()
    @app.before_request
    def guard():
        if 'csrf' not in session: session['csrf']=secrets.token_hex(24)
        if request.method=='POST' and not secrets.compare_digest(session['csrf'],request.form.get('csrf','')): abort(400)
        if request.endpoint not in ('login','static') and not session.get('role'): return redirect(url_for('login'))
    @app.route('/login',methods=['GET','POST'])
    def login():
        s=service(); setup=not s.db.one('SELECT 1 FROM users LIMIT 1')
        if request.method=='POST':
            try:
                if setup: s.bootstrap_admin(request.form['password']); flash('Account created. Sign in as admin.'); return redirect(url_for('login'))
                u=s.login(request.form['username'],request.form['password'])
                if u:
                    session.clear(); session.update(username=u['username'],role=u['role']); return redirect(url_for('page',name='dashboard'))
                flash('Invalid username or password')
            except ValueError as e: flash(str(e))
        return render_template('login.html',setup=setup)
    @app.post('/logout')
    def logout():
        session.clear(); return redirect(url_for('login'))
    permissions={'dashboard':ROLES,'tables':('Manager','Waiter'),'menu':('Manager',),'orders':('Manager','Waiter','Cashier'),'kitchen':('Manager','Kitchen'),'payment':('Manager','Cashier'),'staff':('Manager',),'reports':('Manager',)}
    def allow(name):
        if name not in permissions: abort(404)
        if session['role'] not in permissions[name]: abort(403)
    @app.get('/')
    def home(): return redirect(url_for('page',name='dashboard'))
    @app.get('/<name>')
    def page(name):
        allow(name); s=service(); data={}
        if name=='dashboard': data=dict(tables=s.tables(),orders=s.active_orders(),report=s.report() if session['role']=='Manager' else None)
        elif name=='tables': data=dict(tables=s.tables(),orders=s.active_orders())
        elif name=='menu': data=dict(items=s.menu(True))
        elif name in ('orders','payment'):
            orders=s.active_orders(); oid=request.args.get('id',type=int); oid=oid or (orders[0]['id'] if orders else None)
            if oid and not any(o['id']==oid for o in orders): abort(404)
            data=dict(orders=orders,oid=oid,items=s.menu(),details=s.details(oid) if oid else [],total=s.total(oid) if oid else 0)
        elif name=='kitchen': data=dict(items=s.kitchen_items())
        elif name=='staff': data=dict(users=s.db.all('SELECT username,role FROM users'),roles=ROLES)
        elif name=='reports': data=dict(report=s.report(),paid=s.db.all("SELECT * FROM orders WHERE status='Paid' ORDER BY id DESC"))
        return render_template('page.html',name=name,nav=[n for n in permissions if session['role'] in permissions[n]],**data)
    @app.post('/action/<name>/<op>')
    def action(name,op):
        allow(name); s=service(); f=request.form; oid=f.get('oid',type=int); target=name
        allowed={'tables':{'create'},'menu':{'add','edit'},'orders':{'add','quantity','remove'},'kitchen':{'status'},'payment':{'pay'},'staff':{'add'}}
        if op not in allowed.get(name,set()): abort(404)
        if name=='orders' and session['role']=='Cashier': abort(403)
        try:
            if name=='tables': oid=s.create_order(int(f['table'])); target='orders'
            elif name=='menu':
                args=(f['name'],f['category'],f['price'])
                if op=='add': s.add_menu_item(*args)
                else: s.update_menu_item(int(f['item']),*args,f.get('available')=='1')
            elif name=='orders':
                if op=='add': s.add_item(oid,int(f['item']),f['qty'],f.get('note',''))
                elif op=='quantity': s.update_quantity(int(f['detail']),f['qty'])
                else: s.remove_item(int(f['detail']))
            elif name=='kitchen': s.set_kitchen_status(int(f['detail']),f['status'])
            elif name=='payment': flash(f"Payment recorded: {s.checkout(oid,f['method'],f['discount']):,} VND"); oid=None
            elif name=='staff': s.create_user(f['username'],f['password'],f['role'])
            if name!='payment': flash('Saved successfully')
        except (ValueError,sqlite3.IntegrityError,TypeError) as e: flash(str(e))
        return redirect(url_for('page',name=target,**({'id':oid} if oid and target in ('orders','payment') else {})))
    return app

if __name__=='__main__': create_app().run(host='127.0.0.1',port=5000)
