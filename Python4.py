
import sqlite3

class Cart:
    def __init__(self):
        """
        Инициализация объекта Cart.
        """
        self.items = {}

    def add_item(self, product_name: str, quantity: int):
        """
        Добавление товара в корзину.
        """
        if product_name in self.items:
            self.items[product_name] += quantity
        else:
            self.items[product_name] = quantity

    def clear_cart(self):
        """
        Очистка корзины.
        """
        self.items = {}

    def get_cart(self) -> dict:
        """
        Получение текущего состояния корзины.
        return: Словарь товаров в корзине {название товара: количество}.
        """
        return self.items
    
class JewelryShop:
    def __init__(self, database_path: str = "jewelry_shop.db"):
        self.conn = sqlite3.connect(database_path)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,  -- Добавлено UNIQUE constraint
                price REAL NOT NULL,
                quantity INTEGER NOT NULL
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                total_price REAL NOT NULL
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                product_id INTEGER,
                quantity INTEGER NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')

        self.conn.commit()


    def add_product(self, name: str, price: float, quantity: int):
        # Проверяем, есть ли товар с таким именем уже в базе данных
        self.cursor.execute("SELECT * FROM products WHERE name=?", (name,))
        existing_product = self.cursor.fetchone()

        if existing_product:
            # Если товар с таким именем уже существует, обновляем количество
            updated_quantity = existing_product[3] + quantity
            self.cursor.execute("UPDATE products SET quantity=? WHERE name=?", (updated_quantity, name))
            self.conn.commit()
            print(f"Количество товара '{name}' успешно обновлено.")
        else:
            # Если товара с таким именем нет, выполняем вставку
            self.cursor.execute("INSERT INTO products (name, price, quantity) VALUES (?, ?, ?)", (name, price, quantity))
            self.conn.commit()
            print(f"Товар '{name}' успешно добавлен.")

    def delete_product(self, product_name: str):
        # Проверяем, существует ли товар с указанным именем
        self.cursor.execute("SELECT * FROM products WHERE name=?", (product_name,))
        existing_product = self.cursor.fetchone()

        if existing_product:
            # Удаляем товар из таблицы products
            self.cursor.execute("DELETE FROM products WHERE name=?", (product_name,))

            # Удаляем связанные записи из таблицы order_items
            self.cursor.execute("DELETE FROM order_items WHERE product_id=?", (existing_product[0],))

            self.conn.commit()
            print(f"Товар '{product_name}' успешно удален.")
        else:
            print(f"Товар с именем '{product_name}' не найден.")
    def update_product(self, product_name: str, new_price: float = None, new_quantity: int = None):
        # Проверяем, существует ли товар с указанным именем
        self.cursor.execute("SELECT * FROM products WHERE name=?", (product_name,))
        existing_product = self.cursor.fetchone()

        if existing_product:
            current_price, current_quantity = existing_product[2], existing_product[3]

            # Подготавливаем новые значения или оставляем текущие, если они не были указаны
            updated_price = new_price if new_price is not None else current_price
            updated_quantity = new_quantity if new_quantity is not None else current_quantity

            # Обновляем запись о товаре
            self.cursor.execute("UPDATE products SET price=?, quantity=? WHERE name=?",
                                (updated_price, updated_quantity, product_name))
            self.conn.commit()

            print(f"Параметры товара '{product_name}' успешно обновлены.")
        else:
            print(f"Товар с именем '{product_name}' не найден.")
    def filter_products(self, min_price=None, max_price=None, min_quantity=None, max_quantity=None):
        # Подготавливаем SQL-запрос с условиями фильтрации
        try:
            query = "SELECT * FROM products "
            params = []

            if min_price is not None:
                query += " AND price >= ?"
                params.append(min_price)

            if max_price is not None:
                query += " AND price <= ?"
                params.append(max_price)

            if min_quantity is not None:
                query += " AND quantity >= ?"
                params.append(min_quantity)

            if max_quantity is not None:
                query += " AND quantity <= ?"
                params.append(max_quantity)

            # Выполняем запрос
            self.cursor.execute(query, tuple(params))
            return self.cursor.fetchall()
        except Exception as e:
            print('e')
    
    def get_available_products(self):
        self.cursor.execute('SELECT * FROM products WHERE quantity > 0')
        return self.cursor.fetchall()
    def get_orders(self):
        self.cursor.execute('SELECT * FROM orders ')
        return self.cursor.fetchall()
    def create_order(self, customer_name: str, products: dict):
        total_price = 0
        for product_name, order_quantity in products.items():
            self.cursor.execute("SELECT name, price, quantity FROM products WHERE name=?", (product_name,))
            product_data = self.cursor.fetchone()

            if product_data and product_data[2] >= order_quantity:
                product_name, product_price, available_quantity = product_data
                total_price += product_price * order_quantity

                # Уменьшение количества товара в таблице products
                updated_quantity = available_quantity - order_quantity
                self.cursor.execute("UPDATE products SET quantity=? WHERE name=?", (updated_quantity, product_name))

        if total_price > 0:
            # Создание записи о заказе в таблице orders
            self.cursor.execute("INSERT INTO orders (customer_name, total_price) VALUES (?, ?)", (customer_name, total_price))
            order_id = self.cursor.lastrowid

            # Добавление товаров в заказ в таблицу order_items
            for product_name, order_quantity in products.items():
                self.cursor.execute("SELECT id FROM products WHERE name=?", (product_name,))
                product_id = self.cursor.fetchone()[0]

                # Добавление записи о товаре в заказ в таблицу order_items
                self.cursor.execute("INSERT INTO order_items (order_id, product_id, quantity) VALUES (?, ?, ?)",
                                    (order_id, product_id, order_quantity))

            self.conn.commit()

    def delete_order(self, order_id: int):
        # Проверяем, существует ли заказ с указанным идентификатором
        self.cursor.execute("SELECT * FROM orders WHERE id=?", (order_id,))
        existing_order = self.cursor.fetchone()

        if existing_order:
            # Удаляем заказ из таблицы orders
            self.cursor.execute("DELETE FROM orders WHERE id=?", (order_id,))

            # Удаляем связанные записи из таблицы order_items
            self.cursor.execute("DELETE FROM order_items WHERE order_id=?", (order_id,))

            self.conn.commit()
            print(f"Заказ с идентификатором {order_id} успешно удален.")
        else:
            print(f"Заказ с идентификатором {order_id} не найден.")


# # Пример использования
#
jewelry_shop = JewelryShop()
# # Добавление товаров в магазин с ограниченным количеством
# jewelry_shop.add_product("Gold Necklace", 500, 10)
# jewelry_shop.add_product("Silver Earrings", 150, 20)
# jewelry_shop.add_product("Diamond Ring", 1000, 5)

# for item in jewelry_shop.get_available_products():
#     print(item)

# # Создание заказа
# order_products = {"Gold Necklace": 2, "Diamond Ring": 1}
# jewelry_shop.create_order("John Doe", order_products)


# cart = Cart()

# # # Добавляем товары в корзину
# cart.add_item("Gold Necklace", 2)


# # Выводим текущее состояние корзины
# print("Текущее состояние корзины:")
# print(cart.get_cart())
# for item in jewelry_shop.get_available_products():
#     print(item)
# print('---Заказ---')
# jewelry_shop.create_order(customer_name='lol',products=cart.get_cart())
# for item in jewelry_shop.get_available_products():
#     print(item)


class UserAuthentication:
    def __init__(self, database_path: str = "users.db") -> None:
        """
        Инициализация объекта UserAuthentication.

        :param database_path: Путь к файлу базы данных SQLite.
        """
        self.conn = sqlite3.connect(database_path)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self) -> None:
        """
        Создание таблицы users в базе данных, если её нет.
        """
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            )
        ''')
        self.conn.commit()

    def register_user(self, username: str, password: str, role: str) -> None:
        """
        Регистрация нового пользователя.
        role: Роль пользователя (client, employee, admin).
        """
        # Проверяем, существует ли пользователь с таким именем
        self.cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        existing_user = self.cursor.fetchone()

        if existing_user:
            print(f"Пользователь с именем '{username}' уже существует. Выберите другое имя.")
        else:
            # Регистрируем нового пользователя
            self.cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
            self.conn.commit()
            print("Registration successful!")

    def authenticate_user(self, username: str, password: str,role:str) -> bool:
        try:
            """
            Проверка аутентификации пользователя.
            return: True, если пользователь прошел аутентификацию, иначе False.
            """
            self.cursor.execute("SELECT * FROM users WHERE username=? AND password=? AND role=?", (username, password,role))
            user = self.cursor.fetchone()
            return user is not None
        except Exception as e:
            print(e)

    def get_all_users(self) -> list:
        """
        Получение списка всех зарегистрированных пользователей.

        :return: Список пользователей в виде кортежей (id, username, password, role).
        """
        self.cursor.execute("SELECT * FROM users")
        return self.cursor.fetchall()

    def delete_user(self, user_id: int) -> None:
        """
        Удаление пользователя по его идентификатору.

        :param user_id: Идентификатор пользователя.
        """
        try:
            self.cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
            self.conn.commit()
        except Exception as e:
            print(e)
    def update_user(self, user_id: int,new_name: str = None, new_password: str = None, new_role: str = None) -> None:
        """
        Изменение данных пользователя.
        """
        # Проверяем, существует ли пользователь с указанным идентификатором
        self.cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
        existing_user = self.cursor.fetchone()

        if existing_user:
            current_name, current_password, current_role = existing_user[1], existing_user[2], existing_user[3]

            # Подготавливаем новые значения или оставляем текущие, если они не были указаны
            updated_name = new_name if new_name is not None else current_name
            updated_password = new_password if new_password is not None else current_password
            updated_role = new_role if new_role is not None else current_role

            # Обновляем запись о пользователе
            self.cursor.execute("UPDATE users SET username=?,password=?, role=? WHERE id=?",
                                (updated_name,updated_password, updated_role, user_id))
            self.conn.commit()

            print(f"Данные пользователя с идентификатором {user_id} успешно обновлены.")
        else:
            print(f"Пользователь с идентификатором {user_id} не найден.")
    def get_id_by_name(self, username: str) -> int:
        """
        Получение идентификатора пользователя по его имени.
        """
        # Проверяем, существует ли пользователь с указанным именем
        self.cursor.execute("SELECT id FROM users WHERE username=?", (username,))
        user_id = self.cursor.fetchone()

        if user_id:
            return user_id[0]
        else:
            print(f"Пользователь с именем '{username}' не найден.")





# # Регистрация пользователей
# authenticator.register_user("client1", "password123", "client")
# authenticator.register_user("employee1", "securepass", "employee")
# authenticator.register_user("admin1", "adminpass", "admin")

# # Получение списка всех пользователей
# all_users = authenticator.get_all_users()
# print("All Users:", all_users)






## Удаление пользователя (по выбору - замените user_id на фактический идентификатор)
# user_id_to_delete = 1
# authenticator.delete_user(user_id_to_delete)

# # Повторное получение списка всех пользователей после удаления
# all_users_after_deletion = authenticator.get_all_users()
# print("All Users After Deletion:", all_users_after_deletion)

def main():
    while True:
        print("\n1. Register\n2. Login\n3. Exit")
        choice = input("Enter your choice: ")

        if choice == "1":
            # Регистрация нового пользователя
            username = input("Enter username: ")
            password = input("Enter password: ")
            role = input("Enter role (client, employee, admin): ")
            user_auth.register_user(username, password, role)


        elif choice == "2":
            # Аутентификация пользователя
            username = input("Enter username: ")
            password = input("Enter password: ")
            role = input("Enter role (client, employee, admin): ")
            if user_auth.authenticate_user(username, password,role):
                print("Authentication successful!")
                if role == 'client':
                    # Создание объекта Cart для корзины пользователя
                    cart = Cart()

                    while True:
                        print("\n1. View Available Products\n2. Add Product to Cart\n3. View Cart\n4. Checkout\n5. Logout")
                        user_choice = input("Enter your choice: ")

                        if user_choice == "1":
                            # Просмотр доступных продуктов
                            available_products = jewelry_shop.get_available_products()
                            print("\nAvailable Products:")
                            for product in available_products:
                                print(product)

                        elif user_choice == "2":
                            # Добавление товара в корзину
                            product_name = input("Enter product name: ")
                            quantity = int(input("Enter quantity: "))
                            cart.add_item(product_name, quantity)
                            print(f"{quantity} {product_name}(s) added to cart.")

                        elif user_choice == "3":
                            # Просмотр корзины
                            current_cart = cart.get_cart()
                            print("\nCurrent Cart:")
                            for item, quantity in current_cart.items():
                                print(f"{item}: {quantity}")

                        elif user_choice == "4":
                            # Оформление заказа
                            jewelry_shop.create_order(username, cart.get_cart())
                            print("Order placed successfully!")

                            # Очистка корзины после оформления заказа
                            cart.clear_cart()

                        elif user_choice == "5":
                            # Выход из учетной записи
                            break
                        else:
                            print("Invalid choice. Please try again.")
                elif role == "employee":
                    while True:
                        # Дополнительные действия для сотрудника
                        print("\nEmployee Actions:")
                        print("1. Add Product\n2. Delete Product\n3. Update Product\n4. View Available Products\n5. Configure own user's data\n6. Logout")

                        employee_choice = input("Enter your choice: ")

                        if employee_choice == "1":
                            # Добавление нового товара
                            new_product_name = input("Enter product name: ")
                            new_product_price = float(input("Enter product price: "))
                            new_product_quantity = int(input("Enter product quantity: "))
                            jewelry_shop.add_product(new_product_name, new_product_price, new_product_quantity)

                        elif employee_choice == "2":
                            # Удаление товара
                            product_to_delete = input("Enter product name to delete: ")
                            jewelry_shop.delete_product(product_to_delete)

                        elif employee_choice == "3":
                            # Изменение параметров товара
                            product_to_update = input("Enter product name to update: ")
                            new_price = float(input("Enter new price (press Enter to keep current price): "))
                            new_quantity = int(input("Enter new quantity (press Enter to keep current quantity): "))
                            jewelry_shop.update_product(product_to_update, new_price, new_quantity)

                        elif employee_choice == "4":
                            # Просмотр доступных продуктов
                            available_products = jewelry_shop.get_available_products()
                            print("\nAvailable Products:")
                            for product in available_products:
                                print(product)
                        elif employee_choice == "5":
                            # Изменение данных пользователя
                            username_from_login = username
                            user_id_to_update = user_auth.get_id_by_name(username=username_from_login)
                            new_name = input("Enter username  to update: ")
                            new_password = input("Enter new password (press Enter to keep current password): ")
                            new_role = input("Enter new role (press Enter to keep current role): ")
                            user_auth.update_user(user_id_to_update,new_name, new_password, new_role)
                            print(f"User with ID {user_id_to_update} updated successfully.")
                        elif employee_choice == "6":
                            # Выход из учетной записи
                            break

                        else:
                            print("Invalid choice. Please try again.")            
                elif role == "admin":
                    while True:
                        # Дополнительные действия для администратора
                        print("\nAdmin Actions:")
                        print("1. View All Users\n2. Delete User\n3. Update User\n4. Configure user's data\n5. Exit Admin Panel")

                        admin_choice = input("Enter your choice: ")

                        if admin_choice == "1":
                            # Просмотр всех пользователей
                            all_users = user_auth.get_all_users()
                            print("\nAll Users:")
                            for user in all_users:
                                print(user)

                        elif admin_choice == "2":
                            # Удаление пользователя
                            user_id_to_delete = int(input("Enter user ID to delete: "))
                            user_auth.delete_user(user_id_to_delete)
                            print(f"User with ID {user_id_to_delete} deleted successfully.")

                        elif admin_choice == "3":
                            # Изменение данных пользователя
                            user_id_to_update = input("Enter user ID to update: ")
                            new_name = input("Enter username  to update: ")
                            new_password = input("Enter new password (press Enter to keep current password): ")
                            new_role = input("Enter new role (press Enter to keep current role): ")
                            user_auth.update_user(user_id_to_update,new_name, new_password, new_role)
                            print(f"User with ID {user_id_to_update} updated successfully.")

                        elif admin_choice == "4":
                            # Добавление нового пользователя
                            new_username = input("Enter username: ")
                            new_password = input("Enter password: ")
                            new_role = input("Enter role (client, employee, admin): ")
                            user_auth.register_user( new_username, new_password, new_role)
                            
                            print(f"User '{new_username}' is added successfully.")

                        elif admin_choice == "5":
                            # Выход из админ-панели
                            print("Exiting Admin Panel.")
                            break

                        else:
                            print("Invalid choice. Please try again.")

            else:
                print("Authentication failed. Please try again.")

        elif choice == "3":
            # Выход из программы
            break

        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    jewelry_shop = JewelryShop()
    user_auth = UserAuthentication()
    main()







