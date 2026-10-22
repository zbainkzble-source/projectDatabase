const $ = (s) => document.querySelector(s);
let currentEntity = "learners";
let editingId = null;

// โครงสร้างฟิลด์และฟอร์มสำหรับแต่ละตาราง
const ENTITIES = {
  learners: {
    title: "ผู้เรียน",
    idField: "รหัสผู้เรียน",
    search: [
      { key: "name", label: "ชื่อผู้เรียน", type: "text" },
      { key: "email", label: "อีเมล", type: "text" }
    ],
    form: [
      { key: "name", label: "ชื่อ-นามสกุล", type: "text", required: true },
      { key: "email", label: "อีเมล", type: "email", required: true },
      { key: "join_date", label: "วันที่สมัคร (YYYY-MM-DD)", type: "date" }
    ]
  },
  courses: {
    title: "คอร์สเรียน",
    idField: "คอร์สID", // 👈 ต้องเป็น "คอร์สID"
    search: [
      { key: "title", label: "ชื่อคอร์ส", type: "text" },
      { key: "category", label: "หมวดหมู่", type: "text" }
    ],
    form: [
      { key: "title", label: "ชื่อคอร์ส", type: "text", required: true },
      { key: "category", label: "หมวดหมู่", type: "text", required: true },
      { key: "price_7days", label: "ราคาเช่า 7 วัน (บาท)", type: "number", required: true },
      { key: "price_30days", label: "ราคาเช่า 30 วัน (บาท)", type: "number", required: true },
      { key: "price_lifetime", label: "ราคาซื้อขาดตลอดชีพ (บาท)", type: "number", required: true },
      { key: "expert_name", label: "อาจารย์ประจำวิชา", type: "text", required: true },
      { key: "prerequisite_id", label: "รหัสวิชาที่ต้องเรียนก่อน (ถ้ามี)", type: "number" }
    ]
  },
  enrollments: {
    title: "การลงทะเบียน (เช่า/ซื้อ)",
    idField: "รหัสลงทะเบียน",
    search: [
      { key: "learner_id", label: "รหัสผู้เรียน", type: "number" },
      { key: "course_id", label: "รหัสคอร์ส", type: "number" },
      { key: "rental_type", label: "ประเภทสิทธิ์", type: "select", options: [["", "ทั้งหมด"], ["7_days", "เช่า 7 วัน"], ["30_days", "เช่า 30 วัน"], ["lifetime", "ซื้อขาด"]] },
      { key: "status", label: "สถานะ", type: "select", options: [["", "ทั้งหมด"], ["studying", "กำลังเรียน"], ["completed", "เรียนจบแล้ว"]] }
    ],
    form: [
      { key: "learner_id", label: "รหัสผู้เรียน (learner_id)", type: "number", required: true },
      { key: "course_id", label: "รหัสคอร์ส (course_id)", type: "number", required: true },
      { key: "enroll_date", label: "วันที่ลงทะเบียน", type: "date" },
      { key: "rental_type", label: "ประเภทการเช่า/ซื้อ", type: "select", required: true, options: [["7_days", "เช่า 7 วัน"], ["30_days", "เช่า 30 วัน"], ["lifetime", "ซื้อขาดตลอดชีพ"]] },
      { key: "expire_date", label: "วันหมดอายุสิทธิ์ (ถ้าเช่า)", type: "date" },
      { key: "status", label: "สถานะการเรียน", type: "select", required: true, options: [["studying", "กำลังเรียน"], ["completed", "เรียนจบแล้ว"]] }
    ]
  },
  consultations: {
    title: "นัดปรึกษาอาจารย์ประจำวิชา",
    idField: "รหัสนัดปรึกษา",
    search: [
      { key: "learner_id", label: "รหัสผู้เรียน", type: "number" },
      { key: "course_id", label: "รหัสคอร์ส", type: "number" },
      { key: "status", label: "สถานะ", type: "select", options: [["", "ทั้งหมด"], ["requested", "ส่งคำขอ"], ["scheduled", "นัดหมายแล้ว"], ["completed", "เสร็จสิ้น"], ["cancelled", "ยกเลิก"]] }
    ],
    form: [
      { key: "learner_id", label: "รหัสผู้เรียน (learner_id)", type: "number", required: true },
      { key: "course_id", label: "รหัสคอร์ส (course_id)", type: "number", required: true },
      // แยกเป็น 2 ช่อง: type "date" จะขึ้นปฏิทิน, type "time" จะขึ้นให้เลือกเวลา
      { key: "consult_date", label: "วันที่นัดหมาย", type: "date", required: true },
      { key: "consult_time", label: "เวลาที่นัดหมาย", type: "time", required: true },
      { key: "duration_min", label: "ระยะเวลา (นาที)", type: "number", required: true },
      { key: "fee", label: "ค่าบริการ (บาท)", type: "number", required: true },
      { key: "status", label: "สถานะ", type: "select", required: true, options: [["requested", "ส่งคำขอ"], ["scheduled", "นัดหมายแล้ว"], ["completed", "เสร็จสิ้น"], ["cancelled", "ยกเลิก"]] },
      { key: "notes", label: "หมายเหตุ / รายละเอียดการปรึกษา", type: "text" }
    ]
  }
};

async function api(url, method = "GET", data = null) {
  try {
    const opts = { method, headers: { "Content-Type": "application/json" } };
    if (data) opts.body = JSON.stringify(data);
    const response = await fetch(url, opts);
    
    // ดักจับกรณีที่เซิร์ฟเวอร์พังแล้วตีกลับมาเป็นหน้าเว็บแทน JSON
    const contentType = response.headers.get("content-type") || "";
    if (!contentType.includes("application/json")) {
      return { ok: false, error: "เกิดข้อผิดพลาดจากฝั่งเซิร์ฟเวอร์" };
    }
    
    return await response.json();
  } catch (e) {
    console.error(e);
    return { ok: false, error: "การเชื่อมต่อขัดข้อง หรือข้อมูลไม่ถูกต้อง" };
  }
}

function renderSearchFields() {
  const config = ENTITIES[currentEntity];
  $("#searchTitle").textContent = " — " + config.title;
  const container = $("#searchFields");
  container.innerHTML = config.search.map(f => {
    if (f.type === "select") {
      return `<div class="field"><label>${f.label}</label><select id="s_${f.key}">${f.options.map(([v, l]) => `<option value="${v}">${l}</option>`).join("")}</select></div>`;
    }
    return `<div class="field"><label>${f.label}</label><input type="${f.type}" id="s_${f.key}"></div>`;
  }).join("");
}

async function doSearch() {
  const config = ENTITIES[currentEntity];
  const params = new URLSearchParams();
  config.search.forEach(f => {
    const val = $(`#s_${f.key}`)?.value;
    if (val) params.append(f.key, val);
  });

  const res = await api(`/api/${currentEntity}?${params.toString()}`);
  const st = $("#status"), thead = $("#tableHead"), tbody = $("#tableBody");
  thead.innerHTML = ""; tbody.innerHTML = "";

  if (!res.ok) { st.className = "status err"; st.textContent = "⚠️ " + res.error; return; }
  const rows = res.data || [];
  if (!rows.length) { st.className = "status"; st.textContent = "ไม่พบข้อมูลที่ค้นหา"; return; }

  st.textContent = "";
  const cols = Object.keys(rows[0]);
  thead.innerHTML = cols.map(c => `<th>${c}</th>`).join("") + "<th>จัดการ</th>";

  tbody.innerHTML = rows.map(row => {
    const idVal = row[config.idField];
    const cells = cols.map(c => `<td>${row[c] ?? "—"}</td>`).join("");
    return `<tr>${cells}<td>
      <button class="btn sm" onclick="openEdit('${idVal}')">✏️</button>
      <button class="btn sm del" onclick="deleteRow('${idVal}')">🗑️</button>
    </td></tr>`;
  }).join("");
}

function openAddModal() {
  editingId = null;
  $("#modalTitle").textContent = "เพิ่ม" + ENTITIES[currentEntity].title;
  renderFormFields({});
  $("#modal").classList.remove("hidden");
}

async function openEdit(id) {
  editingId = id;
  const res = await api(`/api/${currentEntity}/${id}`);
  if (!res.ok) { alert(res.error); return; }
  $("#modalTitle").textContent = "แก้ไข" + ENTITIES[currentEntity].title;
  renderFormFields(res.data);
  $("#modal").classList.remove("hidden");
}

function renderFormFields(data) {
  const fields = ENTITIES[currentEntity].form;
  $("#formFields").innerHTML = fields.map(f => {
    const val = data[f.key] ?? "";
    if (f.type === "select") {
      return `<div class="field"><label>${f.label}</label><select id="f_${f.key}">${f.options.map(([v, l]) => `<option value="${v}" ${val == v ? "selected" : ""}>${l}</option>`).join("")}</select></div>`;
    }
    return `<div class="field"><label>${f.label}</label><input type="${f.type}" id="f_${f.key}" value="${val}" ${f.required ? "required" : ""}></div>`;
  }).join("");
}

async function saveForm() {
  const fields = ENTITIES[currentEntity].form;
  const payload = {};
  for (const f of fields) {
    const val = $(`#f_${f.key}`).value;
    if (f.required && !val) { alert(`กรุณากรอก ${f.label}`); return; }
    payload[f.key] = val;
  }

  const method = editingId ? "PUT" : "POST";
  const url = editingId ? `/api/${currentEntity}/${editingId}` : `/api/${currentEntity}`;
  const res = await api(url, method, payload);

  if (!res.ok) { alert("เกิดข้อผิดพลาด: " + res.error); return; }
  $("#modal").classList.add("hidden");
  doSearch();
}

async function deleteRow(id) {
  if (!confirm("คุณต้องการลบข้อมูลนี้ใช่หรือไม่?")) return;
  const res = await api(`/api/${currentEntity}/${id}`, "DELETE");
  if (!res.ok) { alert(res.error); return; }
  doSearch();
}

// Event Listeners
document.querySelectorAll(".tab").forEach(tab => {
  tab.addEventListener("click", (e) => {
    document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
    e.target.classList.add("active");
    currentEntity = e.target.dataset.entity;
    renderSearchFields();
    doSearch();
  });
});

$("#btnSearch").addEventListener("click", doSearch);
$("#btnClear").addEventListener("click", () => { renderSearchFields(); doSearch(); });
$("#btnAdd").addEventListener("click", openAddModal);
$("#btnSave").addEventListener("click", saveForm);
$("#btnCancel").addEventListener("click", () => $("#modal").classList.add("hidden"));

// เริ่มต้นระบบ
renderSearchFields();
doSearch();