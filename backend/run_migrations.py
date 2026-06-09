import pymysql

conn = pymysql.connect(
    host='localhost',
    user='root',
    password='root',
    database='injury_assessment_platform',
    charset='utf8mb4'
)

cursor = conn.cursor()

queries = [
    "ALTER TABLE `biz_case_record` ADD COLUMN `rejected_agency_ids` JSON NULL COMMENT '拒单机构 ID 列表 JSON 数组';",
    "ALTER TABLE `biz_case_record` ADD COLUMN `rework_remark` VARCHAR(255) NULL COMMENT '复议打回原因';",
    "ALTER TABLE `biz_case_record` MODIFY COLUMN `status` int(11) NOT NULL DEFAULT '1' COMMENT '案件状态：1待接单 2鉴定中 3已完成 4已打回';"
]

for q in queries:
    try:
        cursor.execute(q)
        print(f"Success: {q}")
    except Exception as e:
        print(f"Error: {e} - {q}")

conn.commit()
cursor.close()
conn.close()
