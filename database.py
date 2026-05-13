import pyodbc

conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost\\SQLEXPRESS;"
    "DATABASE=KioscoHospital;"
    "Trusted_Connection=yes;"
)
cursor = conn.cursor()
cursor.execute("SELECT Nombre FROM Pacientes")
print(cursor.fetchall())