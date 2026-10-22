# ============================================================
#  db.py (ฉบับย่อ)  — ใช้คู่กับ app.py ตัวที่ให้ไปก่อนหน้า
# ============================================================
import re
import datetime as dt
from decimal import Decimal

import mysql.connector
from mysql.connector import errors as E
import config

RENTAL = {"7_days": 7, "30_days": 30, "lifetime": None}      # ชนิดสิทธิ์ -> จำนวนวัน
ENROLL_STATUS = ("studying", "completed")
CONSULT_STATUS = ("requested", "scheduled", "completed", "cancelled")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
DB_ERRORS = {   # แปลง error ของ MySQL เป็นข้อความที่ผู้ใช้อ่านรู้เรื่อง
    1062: "ระบบปฏิเสธการบันทึก: มีข้อมูลซ้ำ (อีเมลซ้ำ หรือผู้เรียนลงทะเบียนคอร์สนี้ไปแล้ว)",
    1451: "ลบไม่ได้: ยังมีข้อมูลอื่นอ้างอิงรายการนี้อยู่ (เช่น การลงทะเบียน/นัดปรึกษา)",
    1452: "ระบบปฏิเสธการบันทึก: อ้างอิงข้อมูลที่ไม่มีอยู่ในระบบ",
}


# ============================================================
#  พื้นฐานฐานข้อมูล
# ============================================================
def _json(v):
    if isinstance(v, dt.datetime):          # ต้องเช็กก่อน date (datetime เป็น subclass ของ date)
        return v.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(v, dt.date):
        return v.strftime("%Y-%m-%d")
    if isinstance(v, Decimal):
        return float(v)
    return v


def _run(sql, params=None, write=False):
    """SELECT -> list ของ dict | INSERT/UPDATE/DELETE -> {new_id, affected}  (ปิด connection เสมอ, rollback เมื่อพลาด)"""
    conn = mysql.connector.connect(
        host=config.DB_HOST, user=config.DB_USER, password=config.DB_PASSWORD,
        database=config.DB_NAME, port=config.DB_PORT)
    try:
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute(sql, params or ())
            if not write:
                return [{k: _json(v) for k, v in r.items()} for r in cur.fetchall()]
            conn.commit()
            return {"new_id": cur.lastrowid, "affected": cur.rowcount}
        except E.IntegrityError as e:
            conn.rollback()
            if e.errno in DB_ERRORS:
                raise ValueError(DB_ERRORS[e.errno]) from e
            raise
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
    finally:
        conn.close()


def run_query(sql, params=None):
    return _run(sql, params)


def run_command(sql, params=None):
    return _run(sql, params, write=True)


def blank_to_none(value):
    """ช่องว่างจากฟอร์ม ("") -> None (= NULL)"""
    if isinstance(value, str):
        value = value.strip()
    return None if value in ("", None) else value


# ============================================================
#  ตัวช่วยตรวจ/แปลงค่า
# ============================================================
def _text(d, key, label):
    v = str(d.get(key) or "").strip()
    if not v:
        raise ValueError(f"กรุณากรอก{label}")
    return v
    
def _num(v, label, required=True, integer=False, minimum=0):
    v = blank_to_none(v)
    if v is None:
        if required:
            raise ValueError(f"กรุณากรอก{label}")
        return None
    try:
        n = Decimal(str(v))
    except Exception:
        raise ValueError(f"{label}ต้องเป็นตัวเลข")
    if not n.is_finite():
        raise ValueError(f"{label}ต้องเป็นตัวเลข")
    if integer and n != n.to_integral_value():
        raise ValueError(f"{label}ต้องเป็นจำนวนเต็ม")
    if n < minimum:
        raise ValueError(f"{label}ต้องไม่น้อยกว่า {minimum}")
    return int(n) if integer else float(round(n, 2))


def _when(v, label, time=False):
    """แปลงข้อความเป็น date (หรือ datetime ถ้า time=True) — ว่าง = None, รูปแบบผิด = ValueError"""
    s = blank_to_none(v)
    if s is None:
        return None
    s = str(s).strip().replace("T", " ")
    for f in (("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M") if time else ("%Y-%m-%d",)):
        try:
            d = dt.datetime.strptime(s if time else s[:10], f)
            return d if time else d.date()
        except ValueError:
            pass
    raise ValueError(f"{label}รูปแบบไม่ถูกต้อง")


def _fmt(d):
    return d.strftime("%Y-%m-%d %H:%M:%S")


def _get(table, key, _id):
    rows = run_query(f"SELECT * FROM {table} WHERE {key} = %s", (_id,))
    return rows[0] if rows else None


def _need(table, key, _id, what):
    row = _get(table, key, _id)
    if not row:
        raise ValueError(f"ไม่พบ{what}นี้ในระบบ")
    return row


def _delete(table, key, _id, what):
    res = run_command(f"DELETE FROM {table} WHERE {key} = %s", (_id,))
    if not res["affected"]:
        raise ValueError(f"ไม่พบ{what}นี้ในระบบ")
    return res


def _search(base_sql, filters, spec, order):
    """spec = [(ชื่อ filter, คอลัมน์, ใช้ LIKE หรือไม่)]"""
    sql, params = base_sql + " WHERE 1=1", []
    for key, col, like in spec:
        if filters.get(key):
            sql += f" AND {col} {'LIKE' if like else '='} %s"
            params.append(f"%{filters[key]}%" if like else filters[key])
    return run_query(f"{sql} ORDER BY {order}", tuple(params))


# ============================================================
#  LEARNER (ผู้เรียน)
# ============================================================
def search_learners(filters):
    return _search("""
        SELECT learner_id AS 'รหัสผู้เรียน', name AS 'ชื่อผู้เรียน',
               email AS 'อีเมล', join_date AS 'วันที่สมัคร'
        FROM learner""", filters,
        [("name", "name", True), ("email", "email", True)], "learner_id DESC")


def get_learner(learner_id):
    return _get("learner", "learner_id", learner_id)


def _learner_values(d):
    email = _text(d, "email", "อีเมล")
    if not EMAIL_RE.match(email):
        raise ValueError("รูปแบบอีเมลไม่ถูกต้อง")
    return (_text(d, "name", "ชื่อผู้เรียน"), email,
            _when(d.get("join_date"), "วันที่สมัคร") or dt.date.today())


def create_learner(data):
    return run_command("INSERT INTO learner (name, email, join_date) VALUES (%s, %s, %s)",
                       _learner_values(data))


def update_learner(learner_id, data):
    _need("learner", "learner_id", learner_id, "ผู้เรียน")
    return run_command("UPDATE learner SET name=%s, email=%s, join_date=%s WHERE learner_id=%s",
                       (*_learner_values(data), learner_id))


def delete_learner(learner_id):
    return _delete("learner", "learner_id", learner_id, "ผู้เรียน")


# ============================================================
#  COURSE (คอร์สเรียน)
# ============================================================
def search_courses(filters):
    return _search("""
        SELECT c.course_id AS คอร์สID, c.title AS ชื่อคอร์ส, c.category AS หมวดหมู่,
               c.price_7days AS 'ราคา 7 วัน', c.price_30days AS 'ราคา 30 วัน',
               c.price_lifetime AS 'ราคาตลอดชีวิต', c.expert_name AS ชื่ออาจารย์,
               c.prerequisite_id AS วิชาที่ต้องเรียนก่อน,
               (SELECT COUNT(*) FROM enrollment e WHERE e.course_id = c.course_id) AS จำนวนผู้เรียน
        FROM course c""", filters,
        [("title", "c.title", True), ("category", "c.category", True)], "c.course_id DESC")


def get_course(course_id):
    return _get("course", "course_id", course_id)


def _course_values(d, course_id=None):
    pre = _num(d.get("prerequisite_id"), "รหัสวิชาที่ต้องเรียนก่อน", required=False, integer=True, minimum=1)
    seen, cur = set(), pre          # เดินตามสายวิชาบังคับก่อน กันวนกลับมาที่ตัวเอง
    while cur and cur not in seen:
        if cur == course_id:
            raise ValueError("วิชาบังคับก่อนวนกลับมาที่วิชานี้ไม่ได้")
        seen.add(cur)
        c = get_course(cur)
        if not c:
            raise ValueError("ไม่พบรหัสวิชาที่ต้องเรียนก่อนนี้ในระบบ")
        cur = c["prerequisite_id"]
    return (_text(d, "title", "ชื่อคอร์ส"), _text(d, "category", "หมวดหมู่"),
            _num(d.get("price_7days"), "ราคาเช่า 7 วัน"),
            _num(d.get("price_30days"), "ราคาเช่า 30 วัน"),
            _num(d.get("price_lifetime"), "ราคาซื้อขาด"),
            pre, _text(d, "expert_name", "ชื่ออาจารย์ประจำวิชา"))


def create_course(data):
    return run_command("""INSERT INTO course (title, category, price_7days, price_30days,
                          price_lifetime, prerequisite_id, expert_name)
                          VALUES (%s, %s, %s, %s, %s, %s, %s)""", _course_values(data))


def update_course(course_id, data):
    _need("course", "course_id", course_id, "คอร์ส")
    return run_command("""UPDATE course SET title=%s, category=%s, price_7days=%s, price_30days=%s,
                          price_lifetime=%s, prerequisite_id=%s, expert_name=%s WHERE course_id=%s""",
                       (*_course_values(data, course_id), course_id))


def delete_course(course_id):
    return _delete("course", "course_id", course_id, "คอร์ส")


# ============================================================
#  ENROLLMENT (ลงทะเบียน: เช่า/ซื้อ)
# ============================================================
def search_enrollments(filters):
    return _search("""
        SELECT e.enroll_id AS 'รหัสลงทะเบียน', e.learner_id AS 'รหัสผู้เรียน', l.name AS 'ชื่อผู้เรียน',
               e.course_id AS 'รหัสคอร์ส', c.title AS 'ชื่อวิชา', e.enroll_date AS 'วันที่ลงทะเบียน',
               e.rental_type AS 'ประเภทสิทธิ์', e.expire_date AS 'วันหมดอายุ',
               e.amount_paid AS 'ยอดชำระ', e.status AS 'สถานะ'
        FROM enrollment e
        JOIN learner l ON e.learner_id = l.learner_id
        JOIN course c ON e.course_id = c.course_id""", filters,
        [("learner_id", "e.learner_id", False), ("course_id", "e.course_id", False),
         ("status", "e.status", False), ("rental_type", "e.rental_type", False)],
        "e.enroll_date DESC, e.enroll_id DESC")


def get_enrollment(enroll_id):
    return _get("enrollment", "enroll_id", enroll_id)


def _enroll_values(d, old=None):
    """ตรวจทุกเงื่อนไขของการลงทะเบียน แล้วคืนค่าที่พร้อม INSERT/UPDATE"""
    lid = _num(d.get("learner_id"), "รหัสผู้เรียน", integer=True, minimum=1)
    cid = _num(d.get("course_id"), "รหัสคอร์ส", integer=True, minimum=1)
    rtype = blank_to_none(d.get("rental_type")) or "30_days"
    status = blank_to_none(d.get("status")) or "studying"
    if rtype not in RENTAL:
        raise ValueError("ประเภทการเช่า/ซื้อไม่ถูกต้อง")
    if status not in ENROLL_STATUS:
        raise ValueError("สถานะการเรียนไม่ถูกต้อง")

    start = _when(d.get("enroll_date"), "วันที่ลงทะเบียน") or dt.date.today()
    expire = _when(d.get("expire_date"), "วันหมดอายุ")
    days = RENTAL[rtype]
    if days is None:
        expire = None                                   # ซื้อขาด ไม่มีวันหมดอายุ
    elif expire is None:
        expire = start + dt.timedelta(days=days)        # เช่า: คำนวณให้เอง
    elif expire < start:
        raise ValueError("วันหมดอายุต้องไม่ก่อนวันที่ลงทะเบียน")

    _need("learner", "learner_id", lid, "ผู้เรียน")
    course = _need("course", "course_id", cid, "คอร์สเรียน")

    changed = old is None or (old["learner_id"], old["course_id"]) != (lid, cid)
    pre = course["prerequisite_id"]
    if changed and pre and not run_query(
            "SELECT 1 FROM enrollment WHERE learner_id=%s AND course_id=%s AND status='completed'", (lid, pre)):
        name = (get_course(pre) or {}).get("title", "วิชาพื้นฐาน")
        raise ValueError(f"ระบบปฏิเสธการบันทึก: ต้องเรียนวิชา '{name}' ให้จบ (completed) ก่อน จึงจะลงทะเบียนได้")

    # ยอดชำระ: ถ้าคอร์ส/ประเภทเดิมไม่เปลี่ยน ให้คงยอดเดิม (ไม่ผันตามราคาปัจจุบัน)
    if old and not changed and old["rental_type"] == rtype:
        amount = old["amount_paid"]
    else:
        amount = course[{"7_days": "price_7days", "30_days": "price_30days", "lifetime": "price_lifetime"}[rtype]]
    return lid, cid, start, rtype, expire, amount, status


def create_enrollment(data):
    return run_command("""INSERT INTO enrollment (learner_id, course_id, enroll_date, rental_type,
                          expire_date, amount_paid, status) VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                       _enroll_values(data))


def update_enrollment(enroll_id, data):
    old = _need("enrollment", "enroll_id", enroll_id, "รายการลงทะเบียน")
    return run_command("""UPDATE enrollment SET learner_id=%s, course_id=%s, enroll_date=%s, rental_type=%s,
                          expire_date=%s, amount_paid=%s, status=%s WHERE enroll_id=%s""",
                       (*_enroll_values(data, old), enroll_id))


def delete_enrollment(enroll_id):
    return _delete("enrollment", "enroll_id", enroll_id, "รายการลงทะเบียน")


# ============================================================
#  CONSULTATION (นัดปรึกษาอาจารย์)
# ============================================================
def search_consultations(filters):
    return _search("""
        SELECT c.consultation_id AS 'รหัสนัดปรึกษา', c.learner_id AS 'รหัสผู้เรียน', l.name AS 'ชื่อผู้เรียน',
               c.course_id AS 'รหัสคอร์ส', cr.title AS 'ชื่อวิชา', c.consultation_date AS 'วัน-เวลานัดหมาย',
               c.duration_min AS 'ระยะเวลา (นาที)', c.fee AS 'ค่าบริการ (บาท)',
               c.status AS 'สถานะ', c.notes AS 'หมายเหตุ'
        FROM consultation c
        JOIN learner l ON c.learner_id = l.learner_id
        JOIN course cr ON c.course_id = cr.course_id""", filters,
        [("learner_id", "c.learner_id", False), ("course_id", "c.course_id", False),
         ("status", "c.status", False)], "c.consultation_date DESC")


def get_consultation(consultation_id):
    row = _get("consultation", "consultation_id", consultation_id)
    if row and row.get("consultation_date"):
        # แตกข้อมูลวันและเวลาออกจากกัน เพื่อส่งกลับไปแสดงใน 2 ช่องของหน้าเว็บตอนกด "แก้ไข"
        dt_str = str(row["consultation_date"])
        row["consult_date"] = dt_str[:10]   # ดึงแค่ YYYY-MM-DD
        row["consult_time"] = dt_str[11:16] # ดึงแค่ HH:MM
    return row


def _consult_values(d, old=None):
    lid = _num(d.get("learner_id"), "รหัสผู้เรียน", integer=True, minimum=1)
    cid = _num(d.get("course_id"), "รหัสคอร์ส", integer=True, minimum=1)
    
    c_date = blank_to_none(d.get("consult_date"))
    c_time = blank_to_none(d.get("consult_time"))
    
    if not c_date or not c_time:
        raise ValueError("กรุณาเลือกวันและเวลาให้ครบ")
        
    start = _when(f"{c_date} {c_time}", "วัน-เวลานัดหมาย", time=True)

    dur = _num(d.get("duration_min"), "ระยะเวลา", required=False, integer=True, minimum=1) or 30
    if dur > 360:
        raise ValueError("ระยะเวลานัดปรึกษาต้องไม่เกิน 360 นาที")
        
    fee = _num(d.get("fee"), "ค่าบริการ", required=False)
    fee = 300.0 if fee is None else fee
    status = blank_to_none(d.get("status")) or "requested"
    
    _need("learner", "learner_id", lid, "ผู้เรียน")
    course = _need("course", "course_id", cid, "คอร์สเรียน")

    # 🟢 ด่านเช็กเวลาซ้อน: ดูว่าอาจารย์คนนี้มีคิว scheduled ทับเวลานี้ไหม
    if status in ("requested", "scheduled"):
        end = start + dt.timedelta(minutes=dur)
        current_id = old["consultation_id"] if old else 0
        
        check_sql = """
            SELECT COUNT(*) AS count 
            FROM consultation x 
            JOIN course cx ON x.course_id = cx.course_id 
            WHERE x.status = 'scheduled' 
              AND x.consultation_id != %s 
              AND cx.expert_name = %s 
              AND x.consultation_date < %s 
              AND DATE_ADD(x.consultation_date, INTERVAL x.duration_min MINUTE) > %s
        """
        conflict = run_query(check_sql, (current_id, course["expert_name"], _fmt(end), _fmt(start)))[0]
        
        if conflict["count"] > 0:

            raise ValueError("คิวนี้ไม่ว่าง อาจารย์มีนัดหมายช่วงเวลานี้แล้ว กรุณาเลือกเวลาอื่น")

    return lid, cid, _fmt(start), dur, fee, status, blank_to_none(d.get("notes"))


def create_consultation(data):
    return run_command("""INSERT INTO consultation (learner_id, course_id, consultation_date, duration_min,
                          fee, status, notes) VALUES (%s, %s, %s, %s, %s, %s, %s)""", _consult_values(data))


def update_consultation(consultation_id, data):
    old = _need("consultation", "consultation_id", consultation_id, "รายการนัดปรึกษา")
    return run_command("""UPDATE consultation SET learner_id=%s, course_id=%s, consultation_date=%s,
                          duration_min=%s, fee=%s, status=%s, notes=%s WHERE consultation_id=%s""",
                       (*_consult_values(data, old), consultation_id))


def delete_consultation(consultation_id):
    return _delete("consultation", "consultation_id", consultation_id, "รายการนัดปรึกษา")


# ============================================================
#  REPORTS
# ============================================================
def report_summary():
    return run_query("""
        SELECT (SELECT COUNT(*) FROM learner)      AS 'ผู้เรียน (คน)',
               (SELECT COUNT(*) FROM course)       AS 'คอร์สทั้งหมด (วิชา)',
               (SELECT COUNT(*) FROM enrollment)   AS 'การลงทะเบียน (ครั้ง)',
               (SELECT COUNT(*) FROM lesson)       AS 'บทเรียน (คลิป)',
               (SELECT COUNT(*) FROM consultation) AS 'นัดปรึกษาอาจารย์ (ครั้ง)',
               (SELECT IFNULL(SUM(amount_paid), 0) FROM enrollment) AS 'รายได้รวมการเช่า/ซื้อ (บาท)'
    """)[0]


def report_popular_courses():
    return run_query("""
        SELECT c.title AS 'ชื่อคอร์ส', c.category AS 'หมวดหมู่', COUNT(e.learner_id) AS 'จำนวนผู้เรียน'
        FROM course c LEFT JOIN enrollment e ON c.course_id = e.course_id
        GROUP BY c.course_id, c.title, c.category
        ORDER BY COUNT(e.learner_id) DESC, c.course_id
        LIMIT 5
    """)


def report_completion_rate():
    # อัตราเป็นตัวเลข (ไม่ใช่ข้อความ) เพื่อให้เรียงลำดับถูกต้อง
    return run_query("""
        SELECT c.title AS 'ชื่อคอร์ส',
               COUNT(e.enroll_id) AS 'คนลงทะเบียนทั้งหมด',
               IFNULL(SUM(e.status = 'completed'), 0) AS 'คนเรียนจบ',
               ROUND(IFNULL(AVG(e.status = 'completed') * 100, 0), 2) AS 'อัตราการเรียนจบ (ร้อยละ)'
        FROM course c LEFT JOIN enrollment e ON c.course_id = e.course_id
        GROUP BY c.course_id, c.title
        ORDER BY IFNULL(AVG(e.status = 'completed'), 0) DESC, c.course_id
    """)


def report_course_prerequisites():
    return run_query("""
        SELECT c.title AS 'ชื่อคอร์ส', c.category AS 'หมวดหมู่', c.expert_name AS 'อาจารย์ประจำวิชา',
               IFNULL(pre.title, '-') AS 'วิชาที่ต้องเรียนก่อน'
        FROM course c LEFT JOIN course pre ON c.prerequisite_id = pre.course_id
        ORDER BY c.course_id
    """)


REPORTS = [
    ("popular-courses", "คอร์สยอดนิยม (Most Enrolled)",              report_popular_courses),
    ("completion-rate", "อัตราการเรียนจบต่อคอร์ส (Completion Rate)", report_completion_rate),
    ("prerequisites",   "คอร์สและวิชาที่ต้องเรียนก่อน (Self-Join)",  report_course_prerequisites),
]