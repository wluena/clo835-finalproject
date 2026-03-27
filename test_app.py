import unittest
from app import app

class BasicTests(unittest.TestCase):
    def test_main_page(self):
        # This tests if the app can at least initialize without crashing
        tester = app.test_client(self)
        response = tester.get('/', content_type='html/text')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()