import pymysql

conn = pymysql.connect(
    host='localhost',
    user='root',
    password='root',
    database='injury_assessment_platform',
    charset='utf8mb4'
)

cursor = conn.cursor()

try:
    cursor.execute("SELECT id, dept_id, created_by, report_number, victim_name, victim_phone, report_date, province, city, district, accident_type, injury_type, insurance_company, status, agency_id, rejected_agency_ids, rework_remark, appraisal_amount, appraisal_conclusion, report_files, appraisal_submitted_at, appraisal_submitted_by, created_at, updated_at, is_delete, delete_time FROM biz_case_record LIMIT 1;")
    print("Success")
except Exception as e:
    print(f"Error: {e}")

conn.close()
