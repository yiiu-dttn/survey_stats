import psycopg2
from urllib.parse import urlparse
import json

DATABASE_URL = "postgresql://postgres:11111111@localhost:5432/MIS_NHI"

def get_db_connection():
    parsed_url = urlparse(DATABASE_URL)
    return psycopg2.connect(
        dbname=parsed_url.path[1:],
        user=parsed_url.username,
        password=parsed_url.password,
        host=parsed_url.hostname,
        port=parsed_url.port
    )

def get_surveys():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT "ID", "TITLE" FROM public."SSS_SURVEY"')
            return cur.fetchall()
    except Exception as e:
        print(f"Error fetching surveys: {e}")
        return []
    finally:
        conn.close()

def get_survey_details(survey_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT s."ID", s."CO_SO_DAO_TAO_ID", c."MA_DON_VI", s."ELEMENTS", s."TITLE"
                FROM public."SSS_SURVEY" s
                LEFT JOIN "CSDT_CO_SO_DAO_TAO" c ON s."CO_SO_DAO_TAO_ID" = c."ID"
                WHERE s."ID" = %s
            """, (survey_id,))
            survey_info = cur.fetchone()

            if not survey_info:
                return {}

            cur.execute("""
                SELECT COUNT(*) as total, 
                       SUM(CASE WHEN "ANSWERS" IS NOT NULL THEN 1 ELSE 0 END) as valid
                FROM public."SSS_SURVEY_ANSWER"
                WHERE "SURVEY_ID" = %s
            """, (survey_id,))
            counts = cur.fetchone()

            elements_raw = survey_info[3]
            elements = []
            if isinstance(elements_raw, str):
                try:
                    elements = json.loads(elements_raw)
                except json.JSONDecodeError as e:
                    print(f"Error decoding ELEMENTS JSON: {e}")
            elif isinstance(elements_raw, list):
                elements = elements_raw

            return {
                'facility_id': survey_info[1],
                'facility_name': survey_info[2] or "Không xác định",
                'elements': elements,
                'title': survey_info[4],
                'total_answers': counts[0] if counts else 0,
                'valid_answers': counts[1] if counts else 0
            }
    except Exception as e:
        print(f"Error fetching survey details: {e}")
        return {}
    finally:
        conn.close()

def get_survey_answers(survey_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT "ANSWERS"
                FROM public."SSS_SURVEY_ANSWER"
                WHERE "SURVEY_ID" = %s AND "ANSWERS" IS NOT NULL
            """, (survey_id,))
            results = []
            for row in cur.fetchall():
                answer_raw = row[0]
                answer = {}
                if isinstance(answer_raw, str):
                    try:
                        answer = json.loads(answer_raw)
                    except json.JSONDecodeError as e:
                        print(f"Error decoding ANSWERS JSON: {e}")
                elif isinstance(answer_raw, dict):
                    answer = answer_raw
                if answer:
                    results.append(answer)
            return results
    except Exception as e:
        print(f"Error fetching survey answers: {e}")
        return []
    finally:
        conn.close()
