-- ============================================================
-- schema.sql - ระบบเช่าและซื้อคอร์สเรียนออนไลน์ (6 ตาราง)
-- ============================================================

-- ปิดการตรวจ Foreign Key ชั่วคราวเพื่อให้ Drop Table ได้โดยไม่ติด Error
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS consultation;
DROP TABLE IF EXISTS progress;
DROP TABLE IF EXISTS enrollment;
DROP TABLE IF EXISTS lesson;
DROP TABLE IF EXISTS course;
DROP TABLE IF EXISTS learner;
DROP TABLE IF EXISTS subscription_course; -- ลบตารางเก่าที่เคยค้างไว้ (ถ้ามี)
DROP TABLE IF EXISTS subscription;        -- ลบตารางเก่าที่เคยค้างไว้ (ถ้ามี)
DROP TABLE IF EXISTS expert;              -- ลบตารางเก่าที่เคยค้างไว้ (ถ้ามี)

-- เปิดการตรวจ Foreign Key กลับคืน
SET FOREIGN_KEY_CHECKS = 1;

-- 1. ตารางผู้เรียน (Learner)
CREATE TABLE learner (
    learner_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    join_date DATE NOT NULL DEFAULT (CURRENT_DATE)
);

-- 2. ตารางคอร์สเรียน (Course)
CREATE TABLE course (
    course_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    price_7days DECIMAL(10,2) NOT NULL,      -- ราคาเช่า 7 วัน
    price_30days DECIMAL(10,2) NOT NULL,     -- ราคาเช่า 30 วัน
    price_lifetime DECIMAL(10,2) NOT NULL,   -- ราคาซื้อขาดตลอดชีพ
    prerequisite_id INT NULL,
    expert_name VARCHAR(100) NOT NULL,       -- อาจารย์ประจำวิชา
    FOREIGN KEY (prerequisite_id) REFERENCES course(course_id) ON DELETE SET NULL
);

-- 3. ตารางบทเรียน (Lesson)
CREATE TABLE lesson (
    lesson_id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    title VARCHAR(100) NOT NULL,
    seq_no INT NOT NULL UNIQUE,
    duration_min INT NOT NULL,
    FOREIGN KEY (course_id) REFERENCES course(course_id) ON DELETE CASCADE
);

-- 4. ตารางการลงทะเบียนเรียน (Enrollment)
CREATE TABLE enrollment (
    enroll_id INT AUTO_INCREMENT PRIMARY KEY,
    learner_id INT NOT NULL,
    course_id INT NOT NULL,
    enroll_date DATE NOT NULL DEFAULT (CURRENT_DATE),
    rental_type ENUM('7_days', '30_days', 'lifetime') NOT NULL DEFAULT '30_days',
    expire_date DATE NULL,
    amount_paid DECIMAL(10,2) NOT NULL,
    status ENUM('studying', 'completed') NOT NULL DEFAULT 'studying',
    FOREIGN KEY (learner_id) REFERENCES learner(learner_id),
    FOREIGN KEY (course_id) REFERENCES course(course_id),
    UNIQUE (learner_id, course_id)
);

-- 5. ตารางความก้าวหน้าการเรียน (Progress)
CREATE TABLE progress (
    learner_id INT NOT NULL,
    lesson_id INT NOT NULL,
    watched BOOLEAN NOT NULL DEFAULT FALSE,
    completed_date DATE NULL DEFAULT (CURRENT_DATE),
    PRIMARY KEY (learner_id, lesson_id),
    FOREIGN KEY (learner_id) REFERENCES learner(learner_id),
    FOREIGN KEY (lesson_id) REFERENCES lesson(lesson_id)
);

-- 6. ตารางการขอปรึกษาอาจารย์ประจำวิชา (Consultation)
CREATE TABLE consultation (
    consultation_id INT AUTO_INCREMENT PRIMARY KEY,
    learner_id INT NOT NULL,
    course_id INT NOT NULL,
    consultation_date DATETIME NOT NULL,
    duration_min INT NOT NULL DEFAULT 30,
    fee DECIMAL(10,2) NOT NULL DEFAULT 300.00,
    status ENUM('requested', 'scheduled', 'completed', 'cancelled') NOT NULL DEFAULT 'requested',
    notes TEXT NULL,
    FOREIGN KEY (learner_id) REFERENCES learner(learner_id),
    FOREIGN KEY (course_id) REFERENCES course(course_id)
);

-- ============================================================
-- INSERT DATA SAMPLE
-- ============================================================

INSERT INTO learner (name, email, join_date) VALUES
('Chabai',   'chabai145@gmail.com', '2026-04-10'),
('Thorne',   'thorne174@gmail.com', '2025-11-07'),
('Ayato',    'ayato182@gmail.com',  '2026-03-26'),
('ing',      'ing@gmail.com',       '2026-02-03'),
('tle',      'tle@gmail.com',       '2026-09-13'),
('FirstOne', 'FirstOne@gmail.com',  '2026-08-01');

INSERT INTO course (course_id, title, category, price_7days, price_30days, price_lifetime, prerequisite_id, expert_name) VALUES
(1, 'Java',                        'Programming',        190.00,  390.00,  1290.00, NULL, 'Dr.Jason'),
(2, 'Object Oriented Programming', 'Programming',        290.00,  490.00,  1590.00, 1,    'Dr.Peete'),
(3, 'HTML CSS Javascript',         'Web Development',    250.00,  450.00,  1490.00, NULL, 'Dr.Jonsone'),
(4, 'Database',                    'Data',               290.00,  590.00,  1790.00, NULL, 'Dr.Minnian'),
(5, 'Datacom',                     'Computer Networks',  390.00,  790.00,  2590.00, NULL, 'Dr.Zhongli'),
(6, 'Machine Learning',            'AI',                 690.00,  1490.00, 4990.00, 5,   'Dr.Mickey'),
(7, 'Python Programming',          'Programming',        290.00,  590.00,  1990.00, NULL, 'Dr.Harry'),
(8, 'Web Design',                  'Web Development',    290.00,  550.00,  1890.00, 3,    'Dr.Lohen');

INSERT INTO lesson (course_id, title, seq_no, duration_min) VALUES
(1, 'Introduction to Java',           1, 30),
(1, 'Variables and Data Types',       2, 35),
(1, 'Methods and Arrays',             3, 40),
(2, 'Class and Object',               4, 40),
(2, 'Encapsulation',                  5, 35),
(2, 'Inheritance',                    6, 45),
(3, 'HTML Basics',                    7, 30),
(3, 'CSS Basics',                     8, 35),
(3, 'JavaScript Basics',              9, 40),
(4, 'Database Concepts',             10, 35),
(4, 'SQL Basics',                    11, 40),
(4, 'SELECT and JOIN',               12, 45),
(5, 'Intro to Data Communication',   13, 30),
(5, 'Network Devices',               14, 35),
(5, 'Network Basics',                15, 40),
(6, 'Intro to Machine Learning',     16, 35),
(6, 'Training Data',                 17, 40),
(6, 'Simple Prediction',             18, 45),
(7, 'Python Basics',                 19, 30),
(7, 'Variables and Conditions',      20, 35),
(7, 'Loops and Functions',           21, 40),
(8, 'Web Design Basics',             22, 30),
(8, 'Layout and Colors',             23, 35),
(8, 'Responsive Web Design',         24, 45);

INSERT INTO enrollment (learner_id, course_id, enroll_date, rental_type, expire_date, amount_paid, status) VALUES
(1, 1, '2026-09-25', '7_days',   '2026-10-02', 190.00,  'completed'),
(2, 1, '2026-09-27', '30_days',  '2026-10-27', 390.00,  'studying'),
(5, 5, '2026-10-02', 'lifetime', NULL,         2590.00, 'completed'),
(5, 6, '2026-10-03', '7_days',   '2026-10-10', 690.00,  'studying'),
(6, 1, '2026-10-05', '30_days',  '2026-11-04', 390.00,  'studying');

INSERT INTO progress (learner_id, lesson_id, watched, completed_date) VALUES
(1, 1,  TRUE,  '2026-09-25'),
(1, 2,  TRUE,  '2026-09-26'),
(1, 3,  FALSE, NULL),
(2, 1,  TRUE,  '2026-09-27'),
(2, 4,  TRUE,  '2026-09-28'),
(5, 13, TRUE,  '2026-09-30'),
(6, 1,  FALSE, NULL);

INSERT INTO consultation (learner_id, course_id, consultation_date, duration_min, fee, status, notes) VALUES
(1, 1, '2026-10-10 10:00:00', 30, 300.00, 'scheduled', 'ปรึกษาเรื่อง Java กับ Dr.Jason'),
(2, 4, '2026-10-11 13:00:00', 30, 300.00, 'requested', 'สอบถามเรื่อง SQL กับ Dr.Minnian'),
(5, 5, '2026-10-12 14:00:00', 30, 300.00, 'requested', 'ปรึกษาเรื่อง Datacom กับ Dr.Zhongli');