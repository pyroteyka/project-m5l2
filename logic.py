import sqlite3
from config import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import math


class DB_Map():
    def __init__(self, database):
        self.database = database
    
    def create_user_table(self):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS users_cities (
                                user_id INTEGER,
                                city_id TEXT,
                                FOREIGN KEY(city_id) REFERENCES cities(id)
                            )''')
            conn.commit()

    def add_city(self,user_id, city_name ):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM cities WHERE city=?", (city_name,))
            city_data = cursor.fetchone()
            if city_data:
                city_id = city_data[0]  
                conn.execute('INSERT INTO users_cities VALUES (?, ?)', (user_id, city_id))
                conn.commit()
                return 1
            else:
                return 0

            
    def select_cities(self, user_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT cities.city 
                            FROM users_cities  
                            JOIN cities ON users_cities.city_id = cities.id
                            WHERE users_cities.user_id = ?''', (user_id,))

            cities = [row[0] for row in cursor.fetchall()]
            return cities


    def get_coordinates(self, city_name):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT lat, lng
                            FROM cities  
                            WHERE city = ?''', (city_name,))
            coordinates = cursor.fetchone()
            return coordinates

    def create_graph(self, path, cities):
        ax  = plt.axes(projection=ccrs.PlateCarree())
        ax.stock_img()

        for city in cities:
            coordinates = self.get_coordinates(city)
            if coordinates:
                lat, lng = coordinates
                plt.plot([lng], [lat], color='red', linewidth=1, marker='o', transform=ccrs.Geodetic())
                plt.text(lng + 3, lat + 12, city, horizontalalignment='right', transform=ccrs.Geodetic())

        plt.title('Выбранные города')
        plt.savefig(path, bbox_inches='tight')
        plt.close()

        
    def draw_distance(self, city1, city2):
          # Получаем координаты городов
        coords1 = self.get_coordinates(city1)
        coords2 = self.get_coordinates(city2)

        if not coords1 or not coords2:
            raise ValueError(f"Не удалось получить координаты для {city1} или {city2}")

        lat1, lon1 = coords1
        lat2, lon2 = coords2

        # Вычисляем расстояние по формуле «хаверсин» (в километрах)
        def haversine(lat1, lon1, lat2, lon2):
            R = 6371  # радиус Земли, км
            phi1, phi2 = math.radians(lat1), math.radians(lat2)
            d_phi = math.radians(lat2 - lat1)
            d_lambda = math.radians(lon2 - lon1)
            a = math.sin(d_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda/2)**2
            return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        dist = haversine(lat1, lon1, lat2, lon2)

        # Строим карту и маршрут
        ax = plt.axes(projection=ccrs.PlateCarree())
        ax.stock_img()
        ax.coastlines()

        # Маркеры городов
        plt.plot([lon1, lon2], [lat1, lat2],
                 color='blue', linewidth=2, marker='o',
                 transform=ccrs.Geodetic())

        # Подписи городов
        plt.text(lon1 + 1, lat1 + 1, city1, ha='right', transform=ccrs.Geodetic())
        plt.text(lon2 + 1, lat2 + 1, city2, ha='left', transform=ccrs.Geodetic())

        # Подпись расстояния — посредине маршрута
        mid_lon = (lon1 + lon2) / 2
        mid_lat = (lat1 + lat2) / 2
        plt.text(mid_lon, mid_lat, f"{dist:.1f} км",
                 ha='center', va='center',
                 bbox=dict(facecolor='white', alpha=0.7),
                 transform=ccrs.Geodetic())

        plt.title(f"Расстояние между {city1} и {city2}: {dist:.1f}км")
        plt.savefig(path, bbox_inches='tight')
        plt.close()


if __name__=="__main__":
    
    m = DB_Map(DATABASE)
    m.create_user_table()
