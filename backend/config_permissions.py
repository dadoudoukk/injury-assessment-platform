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

def ensure_role(code, name, description):
    cursor.execute("SELECT id FROM sys_role WHERE code = %s AND is_delete = 0", (code,))
    role = cursor.fetchone()
    if not role:
        cursor.execute(
            "INSERT INTO sys_role (code, name, description, is_active, is_delete, data_scope, created_at, updated_at) VALUES (%s, %s, %s, 1, 0, 1, NOW(), NOW())",
            (code, name, description)
        )
        return cursor.lastrowid
    return role['id']

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

# Ensure roles exist
patient_role_id = ensure_role('patient', '普通伤者', 'C端普通用户/伤者角色')
jigou_role_id = ensure_role('jigou', '鉴定机构人员', '鉴定机构操作人员')
insurance_role_id = ensure_role('insurance', '保险公司人员', '保险公司查看人员')

# Assign menus for Patient
# Patients need to view case management and add cases.
# They might need home_index as well.
assign_menus(patient_role_id, ['home_index', 'business', 'caseManage', 'case:add'])

# Assign menus for Jigou (Appraisal Agency)
assign_menus(jigou_role_id, ['home_index', 'business', 'caseManage', 'case:edit', 'case:appraisal'])

# Assign menus for Insurance
assign_menus(insurance_role_id, ['home_index', 'business', 'caseManage'])

conn.commit()
print("Permissions configured successfully!")

conn.close()
