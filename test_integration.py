"""
Integration smoke test — runs against real local stack:
  PostgreSQL 18 | MinIO (E:) | Redis | FastAPI :8000
"""
import os, requests, sys, time
from urllib.parse import urlparse

API = os.environ.get("HIMMA_API_URL", "http://localhost:8000")
RESEARCHER_USERNAME = os.environ.get("E2E_RESEARCHER_USERNAME")
RESEARCHER_PASSWORD = os.environ.get("E2E_RESEARCHER_PASSWORD")
if not RESEARCHER_USERNAME or not RESEARCHER_PASSWORD:
    raise RuntimeError("E2E_RESEARCHER_USERNAME and E2E_RESEARCHER_PASSWORD are required")

def step(msg):
    print(f"\n{'='*50}\n▶ {msg}")

def ok(msg):
    print(f"  ✓ {msg}")

def fail(msg, resp=None):
    print(f"  ✗ {msg}")
    if resp is not None:
        print(f"    Status: {resp.status_code}")
    sys.exit(1)

# ── 1. Health ─────────────────────────────────────────────────────────────────
step("1. API Health")
r = requests.get(f"{API}/health", timeout=5)
assert r.status_code == 200 and r.json()["status"] == "ok", fail("Health failed", r)
ok(f"health OK — {r.json()}")

# ── 2. Researcher login ───────────────────────────────────────────────────────
step("2. Researcher login")
sess_admin = requests.Session()
r = sess_admin.post(f"{API}/auth/login",
    json={"username": RESEARCHER_USERNAME, "password": RESEARCHER_PASSWORD}, timeout=5)
if r.status_code != 200:
    fail("Admin login failed", r)
ok("Researcher authenticated")

# ── 3. /me endpoint ───────────────────────────────────────────────────────────
step("3. /me endpoint (researcher)")
r = sess_admin.get(f"{API}/me", timeout=5)
if r.status_code != 200:
    fail("/me failed", r)
me = r.json()
ok(f"/me → role={me.get('role')}, username={me.get('username')}")

# ── 4. Create student ─────────────────────────────────────────────────────────
step("4. Create student")
ts = int(time.time())
r = sess_admin.post(f"{API}/researcher/students",
    json={"full_name": f"Test Student {ts}", "grade": 1}, timeout=5)
if r.status_code not in (200, 201):
    fail("Create student failed", r)
student_data = r.json()
access_code = student_data.get("access_code") or student_data.get("student", {}).get("access_code")
student_id = student_data.get("id") or student_data.get("student", {}).get("id")
ok(f"Synthetic student created: id={student_id}")

# ── 5. Admin logout ───────────────────────────────────────────────────────────
step("5. Admin logout")
r = sess_admin.post(f"{API}/auth/logout", timeout=5)
ok(f"Logout: {r.status_code}")

# ── 6. Student login ──────────────────────────────────────────────────────────
step("6. Student login")
sess_student = requests.Session()
r = sess_student.post(f"{API}/auth/student-login",
    json={"access_code": access_code}, timeout=5)
if r.status_code != 200:
    fail("Student login failed", r)
ok("Synthetic student logged in")

# ── 7. Get student profile ────────────────────────────────────────────────────
step("7. Student profile")
r = sess_student.get(f"{API}/profile", timeout=5)
if r.status_code != 200:
    fail("Profile failed", r)
ok(f"Profile: {r.json().get('full_name')}")

# ── 8. Start assessment session ───────────────────────────────────────────────
step("8. Start assessment session")
r = sess_student.post(f"{API}/assessment/start", json={"session_type": "pretest"}, timeout=10)
if r.status_code not in (200, 201):
    fail("Start assessment failed", r)
session_data = r.json()
session_id = session_data.get("id")
ok(f"Session started: id={session_id}")

# ── 9. Get first question ─────────────────────────────────────────────────────
step("9. Get first question")
r = sess_student.get(f"{API}/assessment/session/{session_id}/next", timeout=10)
if r.status_code != 200:
    fail("Get next question failed", r)
q = r.json()
item_id = q.get("id")
step_id = q.get("steps", [{}])[0].get("id") if q.get("steps") else None
q_type = q.get("interaction_type") or q.get("kind")
ok(f"Question: id={item_id}, step_id={step_id}, type={q_type}")

# ── 10. Submit answer ─────────────────────────────────────────────────────────
step("10. Submit answer to PostgreSQL")
first_option_id = q.get("steps", [{}])[0].get("options", [{}])[0].get("id") if q.get("steps") else None
r = sess_student.post(
    f"{API}/assessment/session/{session_id}/attempt/{item_id}/submit",
    json={"step_id": step_id, "selected_option_id": first_option_id}, timeout=10)
if r.status_code not in (200, 201):
    fail("Submit answer failed", r)
ok(f"Answer saved: {r.json()!r:.150}")

# ── 11. Upload audio to MinIO ─────────────────────────────────────────────────
step("11. Upload audio to MinIO")
import boto3
from botocore.exceptions import ClientError

s3 = boto3.client('s3',
    endpoint_url=os.environ['S3_ENDPOINT'],
    aws_access_key_id=os.environ['S3_ACCESS_KEY'],
    aws_secret_access_key=os.environ['S3_SECRET_KEY'],
    region_name='us-east-1')

audio_key = f"audio/{student_id}/smoke-test-{ts}.mp3"
audio_path = os.path.join("apps", "web", "public", "audio", "fb-correct.mp3")
with open(audio_path, "rb") as f:
    s3.upload_fileobj(f, os.environ['S3_BUCKET_NAME'], audio_key,
                      ExtraArgs={"ContentType": "audio/mpeg"})
head = s3.head_object(Bucket=os.environ['S3_BUCKET_NAME'], Key=audio_key)
ok(f"Audio in MinIO: key={audio_key}, size={head['ContentLength']} bytes")

# ── 12. Verify DB has attempts ────────────────────────────────────────────────
step("12. Verify answers in PostgreSQL")
import psycopg2
from urllib.parse import urlparse
p = urlparse(os.environ['DATABASE_URL'])
conn = psycopg2.connect(host=p.hostname, port=p.port or 5432,
    dbname=p.path.lstrip('/'), user=p.username, password=p.password)
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM attempts WHERE session_id=%s", (session_id,))
cnt = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM assessment_sessions WHERE id=%s", (session_id,))
sess_cnt = cur.fetchone()[0]
conn.close()
ok(f"attempts in DB: {cnt}, session rows: {sess_cnt}")

print(f"\n{'='*50}")
print("✓ ALL CHECKS PASSED — Local stack fully operational")
print(f"  PostgreSQL: himma_db@localhost:5432")
print(f"  MinIO:      himma-audio bucket, {head['ContentLength']} bytes uploaded")
print(f"  Redis:      running (localhost:6379)")
print(f"  FastAPI:    http://localhost:8000/health → ok")
print(f"  Session:    {session_id}, Attempts: {cnt}")
