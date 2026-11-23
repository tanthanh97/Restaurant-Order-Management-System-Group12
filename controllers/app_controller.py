from models.database import Database
from models.services import RestaurantService

class AppController:
    def __init__(self, db_path=None):
        self.db = Database(db_path) if db_path else Database()
        self.service = RestaurantService(self.db)
        self.user = None

    def sign_in(self, username, password):
        self.user = self.service.login(username,password)
        return self.user

    def can(self, *roles):
        return bool(self.user and (self.user['role']=='Manager' or self.user['role'] in roles))
