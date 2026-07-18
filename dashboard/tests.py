from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from menu.models import Category, MenuItem


User = get_user_model()


class StaffMenuManagementTests(TestCase):
	def setUp(self):
		self.category = Category.objects.create(name='Pizza Cones')
		self.staff_user = User.objects.create_user(
			username='staff_member',
			password='secure-password-123',
			is_staff=True,
		)
		self.customer_user = User.objects.create_user(
			username='customer_user',
			password='secure-password-123',
			is_staff=False,
		)

	def _test_image(self, name='menu.gif'):
		# 1x1 transparent GIF
		gif_bytes = (
			b'GIF89a\x01\x00\x01\x00\x80\x00\x00'
			b'\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00'
			b',\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02L\x01\x00;'
		)
		return SimpleUploadedFile(name, gif_bytes, content_type='image/gif')

	def test_staff_can_create_menu_item_with_price_and_image(self):
		self.client.force_login(self.staff_user)

		response = self.client.post(
			reverse('dashboard:menu_item_create'),
			{
				'category': self.category.pk,
				'name': 'Pepperoni Cone',
				'description': 'A classic.',
				'price': '9.50',
				'image': self._test_image('pepperoni.gif'),
				'is_available': 'on',
				'is_featured': '',
				'calories': '650',
				'display_order': '1',
			},
		)

		self.assertEqual(response.status_code, 302)
		created = MenuItem.objects.get(name='Pepperoni Cone')
		self.assertEqual(created.price, Decimal('9.50'))
		self.assertTrue(created.image.name.startswith('menu_items/'))

	def test_staff_can_edit_menu_item_price_and_image(self):
		self.client.force_login(self.staff_user)
		item = MenuItem.objects.create(
			category=self.category,
			name='Margherita Cone',
			price=Decimal('8.00'),
		)

		response = self.client.post(
			reverse('dashboard:menu_item_edit', kwargs={'pk': item.pk}),
			{
				'category': self.category.pk,
				'name': 'Margherita Cone',
				'description': 'Updated description.',
				'price': '10.25',
				'image': self._test_image('margherita.gif'),
				'is_available': 'on',
				'is_featured': 'on',
				'calories': '700',
				'display_order': '2',
				'ingredient_lines-TOTAL_FORMS': '0',
				'ingredient_lines-INITIAL_FORMS': '0',
				'ingredient_lines-MIN_NUM_FORMS': '0',
				'ingredient_lines-MAX_NUM_FORMS': '1000',
			},
		)

		self.assertEqual(response.status_code, 302)
		item.refresh_from_db()
		self.assertEqual(item.price, Decimal('10.25'))
		self.assertTrue(item.is_featured)
		self.assertTrue(item.image.name.startswith('menu_items/'))

	def test_non_staff_cannot_access_menu_item_create(self):
		self.client.force_login(self.customer_user)
		response = self.client.get(reverse('dashboard:menu_item_create'))

		self.assertEqual(response.status_code, 302)
		self.assertTrue(response.url.startswith(reverse('dashboard:login')))
