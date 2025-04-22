from django import template
from django.urls import reverse, NoReverseMatch

register = template.Library()

@register.simple_tag(takes_context=True)
def active_class(context, url_name):
    request = context['request']
    try:
        path = reverse(url_name)
        if request.path.startswith(path):
            return "active-sidebar"
    except NoReverseMatch:
        return ""
    return ""

@register.simple_tag(takes_context=True)
def admin_active_class(context, *view_names):
    current_view = context.request.resolver_match.view_name
    if current_view in view_names:
        return "admin-active-sidebar"
    return ""


# from django import template

# register = template.Library()

# @register.simple_tag(takes_context=True)
# def active_class(context, url_name):
#     from django.urls import reverse
#     request = context['request']
#     try:
#         if request.path == reverse(url_name):
#             return "active-sidebar"
#     except:
#         return ""
#     return ""



# from django import template

# register = template.Library()

# @register.simple_tag(takes_context=True)
# def active_class(context, *view_names):
#     current_view = context.request.resolver_match.view_name
#     if current_view in view_names:
#         return "active-sidebar"
#     return ""


# {% active_class 'orders' 'order_detail' %}
