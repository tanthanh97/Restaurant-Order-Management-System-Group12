import pytest
from web_app import create_app
from models.database import Database
from models.services import RestaurantService

@pytest.fixture
def client(tmp_path):
    path=tmp_path/'web.db'; db=Database(path); s=RestaurantService(db); s.bootstrap_admin('testpass123'); s.create_user('waiter','testpass123','Waiter'); db.close()
    app=create_app(path); app.config['TESTING']=True
    return app.test_client()

def post(client,url,**data):
    with client.session_transaction() as sess: data['csrf']=sess['csrf']
    return client.post(url,data=data,follow_redirects=True)

def login(client,user='admin'):
    client.get('/login'); return post(client,'/login',username=user,password='testpass123')

def test_web_login(client):
    assert client.get('/dashboard').status_code==302
    assert b'Welcome, admin' in login(client).data
    for page in ('tables','menu','orders','kitchen','payment','staff','reports'):
        assert client.get('/'+page).status_code==200

def test_web_permissions(client):
    login(client,'waiter'); assert client.get('/staff').status_code==403
    assert client.get('/payment').status_code==403

def test_web_csrf(client):
    login(client); assert client.post('/action/tables/create',data={'table':1}).status_code==400

def test_web_order_payment(client):
    login(client); assert b'Order #1' in post(client,'/action/tables/create',table=1).data
    assert b'Grilled Beef Steak' in post(client,'/action/orders/add',oid=1,item=1,qty=2).data
    post(client,'/action/kitchen/status',detail=1,status='Cooking')
    post(client,'/action/kitchen/status',detail=1,status='Ready')
    assert b'Payment recorded: 500,000 VND' in post(client,'/action/payment/pay',oid=1,method='Cash',discount=0).data
