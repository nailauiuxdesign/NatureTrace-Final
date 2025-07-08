import snowflake.connector
import logging

# 启用详细日志
logging.basicConfig(level=logging.DEBUG)

def test_role_access():
    try:
        conn = snowflake.connector.connect(
            user="FLORA0122",
            password="NatureTrace.123",
            account="MP23362.canadacentral",
            role="NATURETRACE_ROLE",  # 明确指定角色
            warehouse="COMPUTE_WH"
        )
        cursor = conn.cursor()
        
        # 测试角色权限
        cursor.execute("""
            SELECT 
                CURRENT_ROLE(),
                CURRENT_WAREHOUSE(),
                EXISTS(
                    SELECT 1 
                    FROM ANIMAL_DB.INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_NAME = 'ANIMAL_INSIGHT_DATA'
                ) AS table_exists
        """)
        role, wh, exists = cursor.fetchone()
        print(f"角色: {role}, 仓库: {wh}, 表存在: {exists}")
        
    except Exception as e:
        print(f"错误: {str(e)}")
        if "does not exist" in str(e):
            print("→ 请确认角色已创建并授权给用户")
    finally:
        cursor.close()
        conn.close()

test_role_access()
