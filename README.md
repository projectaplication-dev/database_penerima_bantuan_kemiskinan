# Database Penerima Bantuan Kemiskinan Ekstrem

Web application sederhana untuk:
- Login petugas
- Pencarian penerima berdasarkan NIK 16 digit
- Menampilkan nama lengkap, alamat, desa, kecamatan, kabupaten, desil, status
- Import data penerima dari CSV
- API JSON untuk integrasi/AppSheet
- SQLite sebagai database awal

## Menjalankan

1. Install Python 3.10+.
2. Masuk ke folder `backend`.
3. Jalankan:
   `pip install -r requirements.txt`
4. Jalankan:
   `python app.py`
5. Buka:
   `http://localhost:5000`

## Akun demo
- Username: `admin`
- Password: `admin123`

Segera ganti password untuk penggunaan nyata.

## Catatan keamanan
NIK adalah data pribadi. Untuk produksi gunakan HTTPS, password yang kuat, backup terenkripsi, pembatasan hak akses, audit log, dan jangan membuka database ke publik tanpa autentikasi.

## Integrasi AppSheet
API pencarian:
`GET /api/penerima/<NIK>`

Contoh:
`http://localhost:5000/api/penerima/7300000000000001`

API tersebut mengembalikan JSON.
