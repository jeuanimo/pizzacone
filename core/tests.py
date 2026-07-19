from django.test import TestCase
from django.urls import reverse

from .models import VenueRequest


class VenueRequestFormTests(TestCase):
	def test_visit_page_creates_venue_request(self):
		response = self.client.post(
			reverse('core:visit'),
			{
				'organization_name': 'Downtown Arts Council',
				'contact_name': 'Taylor Eventson',
				'contact_email': 'taylor@example.com',
				'contact_phone': '(555) 555-1234',
				'requested_date': '2026-09-12',
				'requested_start_time': '11:00',
				'requested_end_time': '14:00',
				'venue_name': 'Riverwalk Plaza',
				'venue_address': '123 Riverwalk Ave, Springfield, IL',
				'estimated_attendance': 250,
				'message': 'We would love to host your truck for our fall community event.',
			},
		)

		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, reverse('core:visit'))
		self.assertEqual(VenueRequest.objects.count(), 1)
		request_obj = VenueRequest.objects.first()
		self.assertEqual(request_obj.organization_name, 'Downtown Arts Council')
		self.assertEqual(request_obj.venue_name, 'Riverwalk Plaza')
