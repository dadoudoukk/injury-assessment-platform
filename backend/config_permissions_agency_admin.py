import pymysql

conn = pymysql.connect(
    host='localhost',
    user='root',
    password='root',
    database='injury_assessment_platform',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

cursor = conn.cursor()

def get_role_id(code):
    cursor.execute("SELECT id FROM sys_role WHERE code = %s AND is_delete = 0", (code,))
    role = cursor.fetchone()
    return role['id'] if role else None

def get_menu_id(name):
    cursor.execute("SELECT id FROM sys_menu WHERE name = %s AND is_delete = 0", (name,))
    menu = cursor.fetchone()
    return menu['id'] if menu else None

def assign_menus(role_id, menu_names):
    for name in menu_names:
        menu_id = get_menu_id(name)
        if not menu_id:
            continue
        cursor.execute("SELECT id FROM sys_role_menu WHERE role_id = %s AND menu_id = %s", (role_id, menu_id))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO sys_role_menu (role_id, menu_id, created_at) VALUES (%s, %s, NOW())", (role_id, menu_id))

agency_admin_role_id = get_role_id('agency_admin')

if agency_admin_role_id:
    assign_menus(agency_admin_role_id, ['home_index', 'business', 'caseManage', 'case:edit', 'case:appraisal'])

conn.commit()
print("Permissions configured successfully for agency_admin!")

conn.close()
