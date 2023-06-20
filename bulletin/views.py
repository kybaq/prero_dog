from django.conf import settings
from django.views.generic import TemplateView


class IndexView(TemplateView):
    """
    This is the index view of the website.
    :param template_name; Specifies the static display template file.
    """
    template_name = 'bulletin/bulletin_board.html'