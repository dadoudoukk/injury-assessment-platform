"""
增量角色菜单脚本：仅为 patient / jigou / insurance 补基础授权。

注意：
- 本脚本不是完整权限基线，不会处理审核中心（auditCenter）相关菜单。
- 审核中心仅 admin 可见，由 phase2_menu_audit.sql / init_db.ensure_phase2_* 维护。
- 重复执行只会追加缺失的 sys_role_menu，不会收回误授权；修正审核误授权请跑 phase2 迁移。
"""
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
# They might need home as well.
assign_menus(patient_role_id, ['home', 'caseCenter', 'caseManage', 'case:add'])

# Assign menus for Jigou (Appraisal Agency)
assign_menus(jigou_role_id, ['home', 'caseCenter', 'caseManage', 'case:edit', 'case:appraisal'])

# Assign menus for Insurance
assign_menus(insurance_role_id, ['home', 'caseCenter', 'caseManage'])

conn.commit()
print("Permissions configured successfully!")

conn.close()
