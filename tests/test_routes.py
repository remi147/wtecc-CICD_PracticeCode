"""
Counter API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
from unittest import TestCase
from service.common import status  # HTTP Status Codes
from service.routes import app, reset_counters


######################################################################
#  T E S T   C A S E S
######################################################################
class CounterTest(TestCase):
    """REST API Server Tests"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.testing = True

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        pass

    def setUp(self):
        """This runs before each test"""
        reset_counters()
        self.app = app.test_client()

    def tearDown(self):
        """This runs after each test"""
        pass

    ##################################################################
    #  I N D E X   &   H E A L T H
    ##################################################################

    def test_index(self):
        """It should return 200 with service metadata"""
        resp = self.app.get("/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data["message"], "Hit Counter Service")
        self.assertIn("version", data)
        self.assertIn("url", data)

    def test_health(self):
        """It should report healthy status"""
        resp = self.app.get("/health")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.get_json()["status"], "OK")

    ##################################################################
    #  C R E A T E   C O U N T E R
    ##################################################################

    def test_create_counter(self):
        """It should Create a counter and return 201 with counter=0"""
        resp = self.app.post("/counters/foo")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        data = resp.get_json()
        self.assertEqual(data["name"], "foo")
        self.assertEqual(data["counter"], 0)

    def test_create_counter_returns_location_header(self):
        """It should return a Location header pointing to the new counter"""
        resp = self.app.post("/counters/bar")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("Location", resp.headers)
        self.assertIn("/counters/bar", resp.headers["Location"])

    def test_create_duplicate_counter(self):
        """It should not Create a duplicate counter — returns 409"""
        self.app.post("/counters/foo")
        resp = self.app.post("/counters/foo")
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)

    def test_create_multiple_counters(self):
        """It should Create several distinct counters independently"""
        for name in ("alpha", "beta", "gamma"):
            resp = self.app.post(f"/counters/{name}")
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        data = self.app.get("/counters").get_json()
        names = [item["name"] for item in data]
        self.assertIn("alpha", names)
        self.assertIn("beta", names)
        self.assertIn("gamma", names)

    ##################################################################
    #  L I S T   C O U N T E R S
    ##################################################################

    def test_list_counters_empty(self):
        """It should return an empty list when no counters exist"""
        resp = self.app.get("/counters")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.get_json()), 0)

    def test_list_counters_after_create(self):
        """It should List counters and reflect newly created ones"""
        self.app.post("/counters/foo")
        data = self.app.get("/counters").get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "foo")
        self.assertEqual(data[0]["counter"], 0)

    ##################################################################
    #  R E A D   C O U N T E R
    ##################################################################

    def test_read_counter(self):
        """It should Read a single counter by name"""
        self.app.post("/counters/foo")
        resp = self.app.get("/counters/foo")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data["name"], "foo")
        self.assertEqual(data["counter"], 0)

    def test_read_missing_counter(self):
        """It should return 404 when reading a non-existent counter"""
        resp = self.app.get("/counters/does_not_exist")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    ##################################################################
    #  U P D A T E   C O U N T E R
    ##################################################################

    def test_update_counter(self):
        """It should increment a counter by 1 on PUT"""
        self.app.post("/counters/foo")
        resp = self.app.put("/counters/foo")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.get_json()["counter"], 1)

    def test_update_counter_increments_correctly(self):
        """It should increment the same counter multiple times"""
        self.app.post("/counters/hits")
        for expected in range(1, 6):
            resp = self.app.put("/counters/hits")
            self.assertEqual(resp.get_json()["counter"], expected)

    def test_update_missing_counter(self):
        """It should return 404 when updating a non-existent counter"""
        resp = self.app.put("/counters/ghost")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_does_not_affect_other_counters(self):
        """It should only increment the targeted counter"""
        self.app.post("/counters/a")
        self.app.post("/counters/b")
        self.app.put("/counters/a")
        self.assertEqual(self.app.get("/counters/a").get_json()["counter"], 1)
        self.assertEqual(self.app.get("/counters/b").get_json()["counter"], 0)

    ##################################################################
    #  D E L E T E   C O U N T E R
    ##################################################################

    def test_delete_counter(self):
        """It should Delete a counter and return 204"""
        self.app.post("/counters/foo")
        resp = self.app.delete("/counters/foo")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_counter_makes_it_unreachable(self):
        """Deleted counter should no longer be found via GET"""
        self.app.post("/counters/foo")
        self.app.delete("/counters/foo")
        self.assertEqual(self.app.get("/counters/foo").status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_counter_removes_from_list(self):
        """Deleted counter should disappear from the list"""
        self.app.post("/counters/foo")
        self.app.delete("/counters/foo")
        self.assertEqual(len(self.app.get("/counters").get_json()), 0)

    def test_delete_idempotent(self):
        """Deleting the same counter twice should both return 204"""
        self.app.post("/counters/foo")
        self.assertEqual(self.app.delete("/counters/foo").status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.app.delete("/counters/foo").status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_non_existent_counter(self):
        """Deleting a counter that never existed should return 204"""
        resp = self.app.delete("/counters/never_created")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    ##################################################################
    #  W O R K F L O W   ( F U L L   L I F E C Y C L E )
    ##################################################################

    def test_full_counter_lifecycle(self):
        """It should support create → read → update → delete lifecycle"""
        name = "lifecycle"
        # Create
        self.assertEqual(self.app.post(f"/counters/{name}").get_json()["counter"], 0)
        # Read
        self.assertEqual(self.app.get(f"/counters/{name}").get_json()["counter"], 0)
        # Update x3
        for i in range(1, 4):
            self.assertEqual(self.app.put(f"/counters/{name}").get_json()["counter"], i)
        # Verify persists
        self.assertEqual(self.app.get(f"/counters/{name}").get_json()["counter"], 3)
        # Delete
        self.assertEqual(self.app.delete(f"/counters/{name}").status_code, status.HTTP_204_NO_CONTENT)
        # Confirm gone
        self.assertEqual(self.app.get(f"/counters/{name}").status_code, status.HTTP_404_NOT_FOUND)

    def test_reset_clears_all_counters(self):
        """After reset, the counters list should be empty"""
        self.app.post("/counters/one")
        self.app.post("/counters/two")
        reset_counters()
        self.assertEqual(len(self.app.get("/counters").get_json()), 0)
