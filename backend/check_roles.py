import pymysql
import json

conn = pymysql.connect(
    host='localhost',
    user='root',
    password='root',
    database='injury_assessment_platform',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

cursor = conn.cursor()

cursor.execute("SELECT id, code, name FROM sys_role")
roles = cursor.fetchall()
print("Roles:", json.dumps(roles, ensure_ascii=False))

cursor.execute("SELECT id, name, title, permission, menu_type FROM sys_menu")
menus = cursor.fetchall()
print("Menus:", json.dumps(menus, ensure_ascii=False))

conn.close()
