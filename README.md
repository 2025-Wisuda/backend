# TUTORIAL

## Panduan Menjalankan Proyek Secara Lokal

Dokumen ini menjelaskan langkah-langkah untuk menginstal, mengkonfigurasi, dan menjalankan backend proyek ini di komputer lokal (localhost).

### 1. Prasyarat (Yang Harus Sudah Ada)

Pastikan perangkat lunak berikut sudah terinstal dan berjalan:

* **Python:** Versi **`3.8.12`** (Versi harus sama persis).
* **MySQL Server:** Database server MySQL harus sudah terinstal dan layanannya (service) sedang berjalan.

### 2. Instalasi Awal

1.  **Ambil Kode Proyek (Clone):**
    Buka Terminal (Mac/Linux) atau Command Prompt (Windows), lalu jalankan perintah ini:
    ```bash
    git clone https://github.com/2025-Wisuda/backend
    cd backend
    ```
2.  **Buat dan Aktifkan Lingkungan Virtual (Virtual Environment):**
    Ini penting agar library Python proyek ini tidak bentrok dengan proyek lain.
    ```bash
    # Perintah untuk membuat environment bernama 'venv'
    python -m venv env

    # Perintah untuk mengaktifkan environment
    # --> Jika Anda menggunakan MacOS atau Linux:
    source env/bin/activate
    # --> Jika Anda menggunakan Windows:
    env\Scripts\activate
    ```
    *(Jika berhasil, Anda akan melihat tulisan `(venv)` di awal baris perintah terminal Anda)*

3.  **Instal Semua Library yang Dibutuhkan:**
    Pastikan environment `(venv)` masih aktif, lalu jalankan:
    ```bash
    pip install -r requirements.txt
    ```
    *(Tunggu proses instalasi semua library dari file `requirements.txt` selesai)*

### 3. Konfigurasi Database

Proyek ini memerlukan koneksi ke database MySQL.

1.  **Siapkan Database di MySQL:**
    * Buka aplikasi manajemen MySQL Anda (misalnya phpMyAdmin, MySQL Workbench, atau command line).
    * Buat sebuah **database baru**. Contoh nama database: `backend`. Catat nama yang Anda gunakan.
    * Pastikan Anda memiliki **username** dan **password** untuk mengakses database MySQL tersebut.

2.  **Update Pengaturan Koneksi di Kode Proyek (settings.py):**
    * Buka file `settings.py` dalam folder proyek Anda (lokasinya di `backend/api/settings.py`).
    * Cari bagian konfigurasi `DATABASES`.
    * **Ubah** nilai untuk `NAME`, `USER`, dan `PASSWORD` sesuai dengan nama database, username, dan password MySQL yang Anda siapkan di langkah sebelumnya.

    ```python
    # Konfigurasi settings.py saat ini
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'backend',     # <-- GANTI DENGAN NAMA DATABASE ANDA
            'USER': 'root',        # <-- GANTI DENGAN USERNAME MYSQL ANDA
            'PASSWORD': '',        # <-- GANTI DENGAN PASSWORD MYSQL ANDA
            'HOST': '127.0.0.1',   # Biasanya '127.0.0.1' atau 'localhost'
            'PORT': '3306',        # Port default MySQL
        }
    }
    ```
    * Simpan perubahan pada file `settings.py`.

### 4. Setup Database & Menjalankan Server

Kembali ke terminal (pastikan `(venv)` masih aktif).

1.  **Buat Tabel-Tabel di Database (Migrate):**
    Perintah ini akan membuat struktur tabel yang dibutuhkan oleh aplikasi di database MySQL Anda.
    ```bash
    python manage.py migrate
    ```

2.  **Isi Data Awal (Seed Users & Groups):**
    Perintah ini mengisi data awal seperti akun admin default.
    ```bash
    python manage.py seed_groups
    python manage.py seed_users
    ```

3.  **Jalankan Server Pengembangan Lokal:**
    ```bash
    python manage.py runserver
    ```
    Jika tidak ada error, server akan berjalan. Anda akan melihat output seperti:
    `Starting development server at http://127.0.0.1:8000/`
    Biarkan terminal ini tetap terbuka agar server terus berjalan.

### 5. Akses Aplikasi & Uji Coba API

1.  **Masuk ke Halaman Admin:**
    * Buka browser.
    * Kunjungi alamat: `http://127.0.0.1:8000/admin`
    * Gunakan akun berikut untuk login:
        * **Username:** `admin`
        * **Password:** `admin`

2.  **Buat Kunci API (API Key):**
    * Setelah berhasil login ke halaman admin, cari menu atau bagian untuk **API Keys**.
    * Buat sebuah API Key baru. **Simpan (copy) nilai key** yang dihasilkan.

3.  **Akses Dokumentasi Interaktif API (Swagger):**
    * Buka tab baru di browser Anda.
    * Kunjungi alamat: `http://127.0.0.1:8000/api/v1/docs/swagger`
    * Halaman ini menampilkan semua endpoint API yang tersedia.

4.  **Otorisasi di Swagger:**
    * Di halaman Swagger, cari dan klik tombol **`Authorize`** (biasanya di kanan atas).
    * Akan muncul jendela popup. Masukkan **API Key** yang Anda buat di langkah 2 ke dalam field yang tersedia (misalnya `X-Api-Key` atau sesuai petunjuk di popup).
    * Klik `Authorize` atau `Save` di popup tersebut.
    * Sekarang Anda sudah bisa mencoba request ke endpoint-endpoint API yang memerlukan otentikasi melalui halaman Swagger.

---

 Jika terjadi error, periksa kembali langkah-langkah di atas, terutama konfigurasi database (`settings.py`) dan pastikan semua perintah dijalankan saat virtual environment `(venv)` aktif.