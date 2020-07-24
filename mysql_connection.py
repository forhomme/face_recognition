import mysql.connector
import datetime


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
                self.connection = connection

    def insert_data(self, nik, nama, jabatan):
        mysql_insert_query = ("INSERT INTO karyawan (nik, nama, jabatan) VALUES (%s, %s, %s)")
        data = (nik, nama, jabatan)

        try:
            cursor = self.connection.cursor()
            cursor.execute(mysql_insert_query, data)
            self.connection.commit()

        except mysql.connector.Error as error:
            print("Error while inserting to MySQL: ", error)

        finally:
            print(cursor.rowcount, "Data berhasil diinput")
            print(f"Data NIK: {nik} \nNama: {nama}")
            cursor.close()

    def select_data(self, nik):
        mysql_select_query = ("SELECT * FROM karyawan WHERE nik is %s")
        data = (nik, )

        try:
            cursor = self.connection.cursor()
            cursor.execute(mysql_select_query, data)
        except mysql.connector.Error as error:
            print("Error while searching data: ", error)
        finally:
            id = cursor[0]
            nama = cursor[1]
            jabatan = cursor[2]
            return id, nama, jabatan

    def insert_absen(self, id, nama, jabatan):
        mysql_insert_absen = ("INSERT INTO absensi (nik, hari, jam) VALUES (%s, %s, %s)")
        tanggal = datetime.date.today()
        tanggal_print = tanggal.strftime("%d-%B-%Y")
        jam = datetime.datetime.now()
        jam = jam.strftime("%H:%M:%S")
        data = (id, tanggal, jam)

        try:
            cursor = self.connection.cursor()
            cursor.execute(mysql_insert_absen, data)
            self.connection.commit()
        except mysql.connector.Error as error:
            print("Error while insert absen data: ", error)
        finally:
            print(f"Selamat datang {nama} \nAbsen {tanggal_print}, {jam}")

    def close_connection(self):
        if self.connection.is_connected():
            self.connection.close()
            print("Koneksi database diputus")


nik = input("Masukan nomor NIK: ")
nama = input("Masukkan Nama Karyawan: ")
jabatan = input("Masukkan Jabatan Karyawan: ")

karyawan = TambahKaryawan()
karyawan.insert_data(nik, nama, jabatan)
karyawan.close_connection()
