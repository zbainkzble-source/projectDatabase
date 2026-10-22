# ============================================================
#  app.py — เว็บแอป Flask (ทำให้เสร็จแล้ว ★ ปกติไม่ต้องแก้)
#  รัน:  python app.py  แล้วเปิด http://127.0.0.1:5000
#  ★ เพิ่มรายงานใหม่ไม่ต้องแก้ไฟล์นี้ — ไปเพิ่มที่ REPORTS ท้าย db.py
# ============================================================
# from datetime import date, datetime
# from flask import Flask, request, jsonify, render_template
# from flask.json.provider import DefaultJSONProvider
# import db


# class JSONProvider(DefaultJSONProvider):
#     """- ส่งวันที่เป็นรูปแบบ YYYY-MM-DD ให้ช่อง <input type="date"> ในฟอร์มอ่านได้
#        - ไม่เรียงชื่อคอลัมน์ใหม่ → หัวตารางเรียงตามลำดับใน SELECT"""
#     sort_keys = False

#     @staticmethod
#     def default(o):
#         if isinstance(o, (date, datetime)):
#             return o.isoformat()
#         return DefaultJSONProvider.default(o)


# app = Flask(__name__)
# app.json = JSONProvider(app)


# def safe(fn, *args, **kwargs):
#     try:
#         return jsonify({"ok": True, "data": fn(*args, **kwargs)})
#     except NotImplementedError as e:
#         return jsonify({"ok": False, "todo": True, "error": str(e)}), 501
#     except ValueError as e:
#         # ข้อผิดพลาดที่ db.py ตั้งใจแจ้งผู้ใช้ เช่น raise ValueError("คลาสนี้เต็มแล้ว")
#         return jsonify({"ok": False, "error": str(e)}), 400
#     except Exception as e:
#         return jsonify({"ok": False, "error": f"{type(e).__name__}: {e}"}), 500


# @app.route("/")
# def page_home():
#     return render_template("index.html")

# @app.route("/report")
# def page_report():
#     return render_template("report.html")


# # ---- ผู้เรียน ----
# @app.route("/api/learners", methods=["GET"])
# def learners_list():
#     filters = {k: v for k, v in request.args.items() if v}
#     return safe(db.search_learners, filters)

# @app.route("/api/learners/<int:_id>", methods=["GET"])
# def learner_get(_id):
#     return safe(db.get_learner, _id)

# @app.route("/api/learners", methods=["POST"])
# def learner_create():
#     return safe(db.create_learner, request.json)

# @app.route("/api/learners/<int:_id>", methods=["PUT"])
# def learner_update(_id):
#     return safe(db.update_learner, _id, request.json)

# @app.route("/api/learners/<int:_id>", methods=["DELETE"])
# def learner_delete(_id):
#     return safe(db.delete_learner, _id)

# # ---- คอร์ส ----
# @app.route("/api/courses", methods=["GET"])
# def courses_list():
#     filters = {k: v for k, v in request.args.items() if v}
#     return safe(db.search_courses, filters)

# @app.route("/api/courses/<int:_id>", methods=["GET"])
# def course_get(_id):
#     return safe(db.get_course, _id)

# @app.route("/api/courses", methods=["POST"])
# def course_create():
#     return safe(db.create_course, request.json)

# @app.route("/api/courses/<int:_id>", methods=["PUT"])
# def course_update(_id):
#     return safe(db.update_course, _id, request.json)

# @app.route("/api/courses/<int:_id>", methods=["DELETE"])
# def course_delete(_id):
#     return safe(db.delete_course, _id)

# # ---- การลงทะเบียน ----
# @app.route("/api/enrollments", methods=["GET"])
# def enrollments_list():
#     filters = {k: v for k, v in request.args.items() if v}
#     return safe(db.search_enrollments, filters)

# @app.route("/api/enrollments/<int:_id>", methods=["GET"])
# def enrollment_get(_id):
#     return safe(db.get_enrollment, _id)

# @app.route("/api/enrollments", methods=["POST"])
# def enrollment_create():
#     return safe(db.create_enrollment, request.json)

# @app.route("/api/enrollments/<int:_id>", methods=["PUT"])
# def enrollment_update(_id):
#     return safe(db.update_enrollment, _id, request.json)

# @app.route("/api/enrollments/<int:_id>", methods=["DELETE"])
# def enrollment_delete(_id):
#     return safe(db.delete_enrollment, _id)


# # ---- รายงาน ----
# @app.route("/api/reports/summary")
# def report_summary():
#     return safe(db.report_summary)

# @app.route("/api/reports")
# def report_list():
#     """รายชื่อรายงานทั้งหมด (อ่านจาก db.REPORTS) ให้หน้าเว็บสร้างกล่องรายงาน"""
#     return jsonify({"ok": True, "data": [{"key": k, "title": t} for k, t, _ in db.REPORTS]})

# @app.route("/api/reports/<key>")
# def report_run(key):
#     """รันรายงานตามชื่อ เช่น /api/reports/overdue"""
#     for k, _, fn in db.REPORTS:
#         if k == key:
#             return safe(fn)
#     return jsonify({"ok": False, "error": f"ไม่พบรายงาน '{key}' ใน db.REPORTS"}), 404


# if __name__ == "__main__":
#     app.run(debug=True, port=5000)


# ============================================================
#  app.py
# ============================================================
from flask import Flask, render_template, request, jsonify
import db

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/report")
def report():
    return render_template("report.html")

# --- API CRUD LEARNERS ---
@app.route("/api/learners", methods=["GET"])
def api_search_learners():
    try:
        data = db.search_learners(request.args)
        return jsonify({"ok": True, "data": data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/learners/<int:learner_id>", methods=["GET"])
def api_get_learner(learner_id):
    try:
        data = db.get_learner(learner_id)
        return jsonify({"ok": True, "data": data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/learners", methods=["POST"])
def api_create_learner():
    try:
        res = db.create_learner(request.json)
        return jsonify({"ok": True, "data": res})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.route("/api/learners/<int:learner_id>", methods=["PUT"])
def api_update_learner(learner_id):
    try:
        res = db.update_learner(learner_id, request.json)
        return jsonify({"ok": True, "data": res})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.route("/api/learners/<int:learner_id>", methods=["DELETE"])
def api_delete_learner(learner_id):
    try:
        res = db.delete_learner(learner_id)
        return jsonify({"ok": True, "data": res})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

# --- API CRUD COURSES ---
@app.route("/api/courses", methods=["GET"])
def api_search_courses():
    try:
        data = db.search_courses(request.args)
        return jsonify({"ok": True, "data": data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/courses/<int:course_id>", methods=["GET"])
def api_get_course(course_id):
    try:
        data = db.get_course(course_id)
        return jsonify({"ok": True, "data": data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/courses", methods=["POST"])
def api_create_course():
    try:
        res = db.create_course(request.json)
        return jsonify({"ok": True, "data": res})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.route("/api/courses/<int:course_id>", methods=["PUT"])
def api_update_course(course_id):
    try:
        res = db.update_course(course_id, request.json)
        return jsonify({"ok": True, "data": res})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.route("/api/courses/<int:course_id>", methods=["DELETE"])
def api_delete_course(course_id):
    try:
        res = db.delete_course(course_id)
        return jsonify({"ok": True, "data": res})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

# --- API CRUD ENROLLMENTS ---
@app.route("/api/enrollments", methods=["GET"])
def api_search_enrollments():
    try:
        data = db.search_enrollments(request.args)
        return jsonify({"ok": True, "data": data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/enrollments/<int:enroll_id>", methods=["GET"])
def api_get_enrollment(enroll_id):
    try:
        data = db.get_enrollment(enroll_id)
        return jsonify({"ok": True, "data": data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/enrollments", methods=["POST"])
def api_create_enrollment():
    try:
        res = db.create_enrollment(request.json)
        return jsonify({"ok": True, "data": res})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.route("/api/enrollments/<int:enroll_id>", methods=["PUT"])
def api_update_enrollment(enroll_id):
    try:
        res = db.update_enrollment(enroll_id, request.json)
        return jsonify({"ok": True, "data": res})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.route("/api/enrollments/<int:enroll_id>", methods=["DELETE"])
def api_delete_enrollment(enroll_id):
    try:
        res = db.delete_enrollment(enroll_id)
        return jsonify({"ok": True, "data": res})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

# --- API CRUD CONSULTATIONS ---
@app.route("/api/consultations", methods=["GET"])
def api_search_consultations():
    try:
        data = db.search_consultations(request.args)
        return jsonify({"ok": True, "data": data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/consultations/<int:consultation_id>", methods=["GET"])
def api_get_consultation(consultation_id):
    try:
        # โยนไปให้ db.py จัดการหั่นวันที่-เวลาให้หน้าเว็บ
        data = db.get_consultation(consultation_id)
        return jsonify({"ok": True, "data": data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/consultations", methods=["POST"])
def api_create_consultation():
    try:
        # โยนข้อมูลไปให้ db.create_consultation ตรวจสอบและบันทึก
        res = db.create_consultation(request.json)
        return jsonify({"ok": True, "data": res})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.route("/api/consultations/<int:consultation_id>", methods=["PUT"])
def api_update_consultation(consultation_id):
    try:
        # โยนข้อมูลไปให้ db.update_consultation ตรวจสอบและอัปเดต
        res = db.update_consultation(consultation_id, request.json)
        return jsonify({"ok": True, "data": res})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.route("/api/consultations/<int:consultation_id>", methods=["DELETE"])
def api_delete_consultation(consultation_id):
    try:
        res = db.delete_consultation(consultation_id)
        return jsonify({"ok": True, "data": res})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

# --- API REPORTS ---
@app.route("/api/reports/summary", methods=["GET"])
def api_report_summary():
    try:
        data = db.report_summary()
        return jsonify({"ok": True, "data": data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/reports", methods=["GET"])
def api_reports_list():
    data = [{"key": k, "title": t} for k, t, _ in db.REPORTS]
    return jsonify({"ok": True, "data": data})

@app.route("/api/reports/<key>", methods=["GET"])
def api_report_detail(key):
    for k, _, fn in db.REPORTS:
        if k == key:
            try:
                return jsonify({"ok": True, "data": fn()})
            except Exception as e:
                return jsonify({"ok": False, "error": str(e)}), 500
    return jsonify({"ok": False, "error": "Not Found"}), 404

if __name__ == "__main__":
    app.run(debug=True, port=5000)