from .models import SiteText


def site_text(request):
    """Makes every SiteText block available in every template as `site_text.<key>`.

    Usage: {{ site_text.home_hero_title|default:"Fallback copy"|linebreaksbr }}
    """
    return {'site_text': {obj.key: obj.content for obj in SiteText.objects.all()}}
