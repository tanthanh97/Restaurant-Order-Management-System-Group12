import pytest
from models.database import Database
from models.services import RestaurantService

@pytest.fixture
def service(tmp_path):
    db=Database(tmp_path/'test.db')
    s=RestaurantService(db)
    yield s
    db.close()

def test_bootstrap_login_and_invalid_password(service):
    assert service.bootstrap_admin('securepass123')
    assert service.login('admin','securepass123')['role']=='Manager'
    assert service.login('admin','wrong') is None
    assert service.bootstrap_admin('otherpassword') is False

def test_staff_account(service):
    service.create_user('waiter1','waiterpass123','Waiter')
    assert service.login('waiter1','waiterpass123')['role']=='Waiter'
    with pytest.raises(ValueError): service.create_user('bad','short','Kitchen')

def test_create_order_updates_table(service):
    oid=service.create_order(1)
    assert oid>0
    assert service.tables()[0]['status']=='Occupied'
    with pytest.raises(ValueError): service.create_order(1)

def test_menu_add_and_edit(service):
    service.add_menu_item('Test dish','Dessert',10000)
    item=service.db.one("SELECT * FROM menu_items WHERE name='Test dish'")
    service.update_menu_item(item['id'],'Updated dish','Dessert',12000,False)
    assert service.db.one('SELECT price FROM menu_items WHERE id=?',(item['id'],))['price']==12000
    assert all(x['name']!='Updated dish' for x in service.menu())

def test_add_edit_remove_order_item(service):
    oid=service.create_order(1)
    item=service.menu()[0]
    service.add_item(oid,item['id'],2,'No onions')
    detail=service.details(oid)[0]
    assert service.total(oid)==item['price']*2
    service.update_quantity(detail['id'],3)
    assert service.total(oid)==item['price']*3
    service.remove_item(detail['id'])
    assert service.total(oid)==0

def test_reject_invalid_quantity(service):
    oid=service.create_order(1)
    with pytest.raises(ValueError): service.add_item(oid,service.menu()[0]['id'],0)

def test_kitchen_status_and_payment(service):
    oid=service.create_order(1)
    item=service.menu()[0]
    service.add_item(oid,item['id'],2)
    detail=service.details(oid)[0]['id']
    with pytest.raises(ValueError): service.checkout(oid,'Cash')
    service.set_kitchen_status(detail,'Cooking')
    service.set_kitchen_status(detail,'Ready')
    with pytest.raises(ValueError): service.set_kitchen_status(detail,'Pending')
    total=service.checkout(oid,'Cash',5000)
    assert total==item['price']*2-5000
    assert service.tables()[0]['status']=='Available'
    assert service.report()['revenue']==total

def test_invalid_discount(service):
    oid=service.create_order(1)
    item=service.menu()[0]
    service.add_item(oid,item['id'],1)
    detail=service.details(oid)[0]['id']
    service.set_kitchen_status(detail,'Cooking')
    service.set_kitchen_status(detail,'Ready')
    with pytest.raises(ValueError): service.checkout(oid,'QR',item['price']+1)

def test_payment_cannot_repeat(service):
    oid=service.create_order(1)
    item=service.menu()[0]
    service.add_item(oid,item['id'],1)
    detail=service.details(oid)[0]['id']
    service.set_kitchen_status(detail,'Cooking')
    service.set_kitchen_status(detail,'Ready')
    service.checkout(oid,'Card')
    with pytest.raises(ValueError): service.checkout(oid,'Card')
