import mysql.connector
import datetime
import multiprocessing as mp
from queue import Empty


class TambahKaryawan:
    def __init__(self):
        try:
            connection = mysql.connector.connect(
                host='localhost',
                database='absen',
                user='root',
                password='root'
            )

        except mysql.connector.Error as error:
            print("Error while connecting to MySQL: ", error)

        finally:
            if connection.is_connected():
                db_Info = connection.get_server_info()
                print("Connected to MySQL Server version ", db_Info)
                connection.close()

    def insert_data(self, nik, nama, jabatan):
        mysql_insert_query = ("INSERT INTO karyawan (nik, nama, jabatan) VALUES (%s, %s, %s)")
        data = (nik, nama, jabatan)

        try:
            connection = mysql.connector.connect(
                host='localhost',
                database='absen',
                user='root',
                password='root'
            )
            cursor = connection.cursor()
            cursor.execute(mysql_insert_query, data)
            connection.commit()

        except mysql.connector.Error as error:
            print("Error while inserting to MySQL: ", error)

        finally:
            print(cursor.rowcount, "Data berhasil diinput")
            print(f"Data NIK: {nik} \nNama: {nama}")
            cursor.close()
            connection.close()

    def get_all_data(self):
        mysql_get_query = ("SELECT * FROM karyawan")

        try:
            connection = mysql.connector.connect(
                host='localhost',
                database='absen',
                user='root',
                password='root'
            )
            cursor = connection.cursor()
            cursor.execute(mysql_get_query)
            records = cursor.fetchall()

        except mysql.connector.Error as error:
            print("Error while searching data: ", error)
        finally:
            cursor.close()
            connection.close()
            return records

    def select_data(self, nik, queue):
        mysql_select_query = ("SELECT * FROM karyawan WHERE nik = %s")
        data = (nik, )

        try:
            connection = mysql.connector.connect(
                host='localhost',
                database='absen',
                user='root',
                password='root'
            )
            cursor = connection.cursor()
            cursor.execute(mysql_select_query, data)
            records = cursor.fetchall()
            for row in records:
                queue.put(row)
        except mysql.connector.Error as error:
            print("Error while searching data: ", error)
        finally:
            print(f"NIK: {row[0]}\nNama: {row[1]}")
            cursor.close()
            connection.close()

    def insert_absen(self, id, nama):
        mysql_insert_absen = ("INSERT INTO absensi (nik, hari, jam) VALUES (%s, %s, %s)")
        tanggal = datetime.date.today()
        tanggal_print = tanggal.strftime("%d-%B-%Y")
        jam = datetime.datetime.now()
        jam = jam.strftime("%H:%M:%S")
        data = (id, tanggal, jam)

        try:
            connection = mysql.connector.connect(
                host='localhost',
                database='absen',
                user='root',
                password='root'
            )
            cursor = connection.cursor()
            cursor.execute(mysql_insert_absen, data)
            connection.commit()

        except mysql.connector.Error as error:
            print("Error while insert absen data: ", error)
        finally:
            print(cursor.rowcount, "Data berhasil diinput")
            print(f"Selamat datang {nama} \nAbsen {tanggal_print}, {jam}")
            cursor.close()
            connection.close()
