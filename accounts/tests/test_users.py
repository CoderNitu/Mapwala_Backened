# accounts/tests/test_users.py
from django.test import TestCase
from django.core.management import call_command
from rest_framework.test import APIClient
from django.urls import reverse
from accounts.models import Role, User

class UserRBACTests(TestCase):
    def setUp(self):
        # seed roles & capabilities
        call_command('seed_rbac')
        # create superuser and attach admin role
        admin_role = Role.objects.get(key='admin')
        self.admin = User.objects.create_superuser(username='admin', email='admin@example.com', password='AdminPass123')
        self.admin.role = admin_role
        self.admin.save()

        # create regular user (no special role)
        self.regular = User.objects.create_user(username='regular', email='reg@example.com', password='RegPass123')

        self.client = APIClient()

    def get_token(self, username, password):
        url = reverse('token_obtain_pair')
        resp = self.client.post(url, {'username': username, 'password': password}, format='json')
        self.assertEqual(resp.status_code, 200)
        return resp.data['access']

    def test_admin_can_create_user(self):
        token = self.get_token('admin', 'AdminPass123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        # get an existing role id (sales)
        sales_role = Role.objects.get(key='sales')
        url = '/api/accounts/users/'
        payload = {
            "username": "john",
            "password": "StrongPass!23",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "role_id": sales_role.id,
            "reports_to": None
        }
        resp = self.client.post(url, payload, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(User.objects.filter(username='john').exists())

    def test_non_admin_cannot_create_user(self):
        token = self.get_token('regular', 'RegPass123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        url = '/api/accounts/users/'
        payload = {
            "username": "unauth",
            "password": "pass1234",
            "first_name": "Unauth",
            "last_name": "User",
            "email": "unauth@example.com",
        }
        resp = self.client.post(url, payload, format='json')
        self.assertIn(resp.status_code, (401, 403))  # either auth fail or forbidden

    def test_change_manager_and_cycle_prevention(self):
        # admin creates manager A and subordinate B
        token = self.get_token('admin', 'AdminPass123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        # create A
        resp_a = self.client.post('/api/accounts/users/', {
            "username": "mgrA", "password":"Apass12345", "first_name":"A", "last_name":"Mgr",
            "email":"a@example.com", "role_id": Role.objects.get(key='gm').id
        }, format='json')
        self.assertEqual(resp_a.status_code, 201)
        a_id = resp_a.data['id']

        # create B (reports_to A)
        resp_b = self.client.post('/api/accounts/users/', {
            "username": "userB", "password":"Bpass12345", "first_name":"B", "last_name":"User",
            "email":"b@example.com", "role_id": Role.objects.get(key='sales').id,
            "reports_to": a_id
        }, format='json')
        self.assertEqual(resp_b.status_code, 201)
        b_id = resp_b.data['id']

        # Now attempt to set A.reports_to = B (this would create cycle) -> should fail
        change_url = f'/api/accounts/users/{a_id}/change_manager/'
        resp_cycle = self.client.post(change_url, {"reports_to": b_id}, format='json')
        self.assertEqual(resp_cycle.status_code, 400)
        self.assertIn('Invalid manager', resp_cycle.data.get('detail', '') or '')

        # Admin can set B's manager to null (allowed)
        change_b = f'/api/accounts/users/{b_id}/change_manager/'
        resp_unassign = self.client.post(change_b, {"reports_to": None}, format='json')
        self.assertEqual(resp_unassign.status_code, 200)
        # reload B
        b_user = User.objects.get(pk=b_id)
        self.assertIsNone(b_user.reports_to)
