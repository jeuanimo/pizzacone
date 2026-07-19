from django.core.management.base import BaseCommand

from core.models import SiteText


class Command(BaseCommand):
    help = 'Seeds editable site text blocks with the current hardcoded copy (safe to re-run — never overwrites existing edits).'

    def handle(self, *args, **options):
        blocks = [
            {
                'key': 'home_hero_title', 'section': SiteText.SECTION_HOME,
                'label': 'Home — Hero Headline',
                'description': 'The big headline on the homepage, over the pizza cone photo.',
                'content': 'All of the Flavor. None of the Mess.',
            },
            {
                'key': 'home_hero_subtitle', 'section': SiteText.SECTION_HOME,
                'label': 'Home — Hero Subheadline',
                'description': 'The smaller line of text right under the big headline on the homepage.',
                'content': 'Hot, fresh pizza baked right into a crispy cone — made to order at our counter.',
            },
            {
                'key': 'home_promo_title', 'section': SiteText.SECTION_HOME,
                'label': 'Home — Promo Section Title',
                'description': 'The heading above the Frozen Lemonade photo, further down the homepage.',
                'content': 'New! Frozen Lemonade',
            },
            {
                'key': 'home_promo_body', 'section': SiteText.SECTION_HOME,
                'label': 'Home — Promo Section Text',
                'description': 'The paragraph next to the Frozen Lemonade photo on the homepage.',
                'content': 'Cool off with our frozen lemonade, topped with real strawberries. The perfect pair for your pizza cone.',
            },
            {
                'key': 'about_heading', 'section': SiteText.SECTION_ABOUT,
                'label': 'About — Page Heading',
                'description': 'The big heading at the top of the About page.',
                'content': 'About The Pizza Cone Co.',
            },
            {
                'key': 'about_paragraph_1', 'section': SiteText.SECTION_ABOUT,
                'label': 'About — Paragraph 1',
                'description': 'The first paragraph of body text on the About page.',
                'content': (
                    'We took everything you love about pizza and made it portable. Every Pizza Cone '
                    'is hot, fresh, and made to order — hand-loaded with melted mozzarella and your '
                    'favorite toppings, baked right into a crispy, edible cone. No plate, no fork, '
                    'no mess. Just grab it, love it, and repeat.'
                ),
            },
            {
                'key': 'about_paragraph_2', 'section': SiteText.SECTION_ABOUT,
                'label': 'About — Paragraph 2',
                'description': 'The second paragraph of body text on the About page, right below the first.',
                'content': (
                    "Whether you're craving Cheese, Pepperoni, Italian Sausage, Veggie, or our "
                    'Meat Lovers cone, we\'ve got a flavor for everyone — plus a Frozen Lemonade '
                    'with real strawberries to wash it down.'
                ),
            },
            {
                'key': 'visit_subtitle', 'section': SiteText.SECTION_VISIT,
                'label': 'Find Us — Page Subtitle',
                'description': 'The line of text under the "Find Us" heading, at the top of the Find Us page.',
                'content': "We move around — here's where to catch us.",
            },
            {
                'key': 'visit_event_blurb', 'section': SiteText.SECTION_VISIT,
                'label': 'Find Us — Event Request Blurb',
                'description': 'The short note above the venue-booking form, near the bottom of the Find Us page.',
                'content': 'Fill this out and our staff will follow up with availability and next steps.',
            },
            {
                'key': 'contact_phone', 'section': SiteText.SECTION_CONTACT,
                'label': 'Contact — Phone Number',
                'description': 'The phone number shown in the site footer, the Find Us page, and the Contact page.',
                'content': '618-593-9237',
            },
            {
                'key': 'contact_hours', 'section': SiteText.SECTION_CONTACT,
                'label': 'Contact — Store Hours',
                'description': 'The "Typical Hours" text shown near the bottom of the Find Us page.',
                'content': 'Mon–Sat: 11am–9pm  |  Sun: 12pm–7pm',
            },
            {
                'key': 'contact_tagline', 'section': SiteText.SECTION_CONTACT,
                'label': 'Contact — Tagline',
                'description': 'The short line under the phone number in the site footer\'s "Contact" column.',
                'content': 'Grab it. Love it. Repeat.',
            },
            {
                'key': 'footer_visit_blurb', 'section': SiteText.SECTION_FOOTER,
                'label': 'Footer — Visit Us Blurb',
                'description': 'The two lines of text under "Visit Us" in the site footer, on every page.',
                'content': 'Hot & fresh, made to order.\nEasy to hold. Hard to put down.',
            },
        ]

        created_count = 0
        for data in blocks:
            key = data.pop('key')
            obj, created = SiteText.objects.get_or_create(key=key, defaults=data)
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created "{obj.label}"'))
            else:
                self.stdout.write(f'"{obj.label}" already exists, skipping.')

        self.stdout.write(self.style.SUCCESS(f'Site text seeding complete ({created_count} created).'))
