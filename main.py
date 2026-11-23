from controllers.app_controller import AppController
from views.app_view import RestaurantApp
from getpass import getpass


def main():
    controller = AppController()
    if not controller.db.one('SELECT 1 FROM users LIMIT 1'):
        print('First run: set up the Manager account (username: admin).')
        while True:
            password = getpass('Choose admin password (8+ characters): ')
            try:
                controller.service.bootstrap_admin(password)
                break
            except ValueError as exc:
                print(exc)
        print('Admin account created. Open the GUI and log in.')
    app = RestaurantApp(controller)
    app.mainloop()
    controller.db.close()

if __name__ == '__main__':
    main()
