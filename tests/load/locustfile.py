"""
Load test for the SamadhanSetu API (results and method: docs/LOAD_TEST.md).

Simulates the traffic mix of a district pilot:
  * Citizens (90% of users) sign in once per session, then browse the public
    challenge list page by page, open challenge details, check "My
    Challenges", occasionally submit a new report, and occasionally sign in
    again (a new session).
  * Officers (10%) work the review queue: the 100-item list the admin
    Challenge Management screen loads, filtered by escalation tier, and open
    individual reports.

Every non-2xx response counts as a failure.

Seed first:  PYTHONPATH=. python scripts/seed_load_test_data.py
Run:         locust -f tests/load/locustfile.py --host http://127.0.0.1:8008 \
               --headless -u 100 -r 10 -t 3m --csv docs/load_test/run --html docs/load_test/run.html

Environment: LOAD_TEST_PASSWORD (default password123), LOAD_TEST_CITIZENS (50),
LOAD_TEST_OFFICER (officer.ranchi@jharkhand.gov.in), LOAD_TEST_WAIT ("1,3" seconds).
"""
import os
import random
import uuid

from locust import HttpUser, between, task

API = "/api/v1"
PASSWORD = os.getenv("LOAD_TEST_PASSWORD", "password123")
CITIZENS = int(os.getenv("LOAD_TEST_CITIZENS", "50"))
OFFICER = os.getenv("LOAD_TEST_OFFICER", "officer.ranchi@jharkhand.gov.in")
WAIT_MIN, WAIT_MAX = (float(x) for x in os.getenv("LOAD_TEST_WAIT", "1,3").split(","))
PAGE_SIZE = 20

DISTRICTS = [
    ("Ranchi", 23.3441, 85.3096), ("Dhanbad", 23.7957, 86.4304), ("East Singhbhum", 22.8046, 86.2029),
    ("Palamu", 24.0416, 84.0734), ("Hazaribagh", 23.9925, 85.3637), ("Giridih", 24.1860, 86.3072),
    ("Dumka", 24.2677, 87.2489), ("Gumla", 23.0428, 84.5422),
]
REPORTS = [
    ("Village handpump broken for two weeks", "Water Resources",
     "The only handpump in our tola has been broken for two weeks and families walk 2 km for drinking water."),
    ("Transformer burnt, hamlet without power", "Energy",
     "The transformer serving our hamlet burnt out last week and 40 houses have had no electricity since."),
    ("Potholes on the road to the block office", "Urban Infrastructure",
     "Deep potholes on the main road to the block office caused two motorcycle accidents this month."),
    ("No doctor at the primary health centre", "Healthcare",
     "The primary health centre has had no doctor for a month and patients are sent 30 km away."),
    ("School has only one teacher for five classes", "Education",
     "Our primary school has one teacher for five classes and children are not learning to read."),
    ("Drain blocked, dirty water entering houses", "Sanitation",
     "The village drain has been blocked for months and dirty water enters houses whenever it rains."),
]


class _ApiUser(HttpUser):
    abstract = True
    wait_time = between(WAIT_MIN, WAIT_MAX)
    email = ""

    def on_start(self):
        self.challenge_ids = []
        self.login()

    def login(self):
        self.client.headers.pop("Authorization", None)
        with self.client.post(f"{API}/auth/login", json={"email": self.email, "password": PASSWORD},
                              name="POST /auth/login", catch_response=True) as res:
            if res.status_code == 200 and "access_token" in res.json():
                self.client.headers["Authorization"] = f"Bearer {res.json()['access_token']}"
                res.success()
            else:
                res.failure(f"login {res.status_code}")

    def list_page(self, page: int, page_size: int, name: str, **filters):
        params = {"page": page, "page_size": page_size, **filters}
        with self.client.get(f"{API}/challenges", params=params, name=name, catch_response=True) as res:
            if res.status_code != 200:
                res.failure(f"list {res.status_code}")
                return
            ids = [c["id"] for c in res.json()]
            if ids:
                self.challenge_ids = ids
            self.total_pages = int(res.headers.get("X-Total-Pages", "1") or 1)

    def view_detail(self):
        if not self.challenge_ids:
            self.list_page(1, PAGE_SIZE, "GET /challenges?page=[n]")
        if self.challenge_ids:
            cid = random.choice(self.challenge_ids)
            self.client.get(f"{API}/challenges/{cid}", name="GET /challenges/[id]")


class Citizen(_ApiUser):
    weight = 9

    def on_start(self):
        self.email = f"loadtest.citizen{random.randint(1, CITIZENS):03d}@loadtest.example.org"
        self.total_pages = 1
        super().on_start()

    @task(10)
    def browse_challenges(self):
        self.list_page(random.randint(1, max(1, self.total_pages)), PAGE_SIZE, "GET /challenges?page=[n]")

    @task(6)
    def open_challenge(self):
        self.view_detail()

    @task(3)
    def my_challenges(self):
        self.client.get(f"{API}/challenges/my", name="GET /challenges/my")

    @task(1)
    def submit_challenge(self):
        title, category, description = random.choice(REPORTS)
        district, lat, lon = random.choice(DISTRICTS)
        payload = {
            "title": title,
            "description": description,
            "category": category,
            "urgency": random.choice(["Low", "Medium", "High"]),
            "affected_population": random.choice([40, 120, 300, 900]),
            "location": {
                "district_name": district,
                "block_name": f"{district} Block {random.randint(1, 6)}",
                "village_or_city": f"Village {random.randint(1, 90)}",
                "latitude": round(lat + random.uniform(-0.05, 0.05), 6),
                "longitude": round(lon + random.uniform(-0.05, 0.05), 6),
            },
            "source_type": "MOBILE_APP",
            "consent_given": True,
            "idempotency_key": str(uuid.uuid4()),
        }
        self.client.post(f"{API}/challenges", json=payload, name="POST /challenges")

    @task(1)
    def sign_in_again(self):
        self.login()


class Officer(_ApiUser):
    weight = 1
    email = OFFICER

    @task(5)
    def review_queue(self):
        tier = random.choice([None, "PANCHAYAT", "BLOCK", "DISTRICT"])
        filters = {"tier": tier} if tier else {}
        self.list_page(1, 100, "GET /challenges?page=1&page_size=100 (review queue)", **filters)

    @task(3)
    def open_report(self):
        self.view_detail()
