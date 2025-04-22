from django import template

register = template.Library()

@register.simple_tag
def build_breadcrumbs(category):
    breadcrumbs = [('Home', '/'), ('All Products', '/products/')]
    for ancestor in category.get_ancestors():
        breadcrumbs.append((ancestor.name, f'/category/{ancestor.slug}/'))
    breadcrumbs.append((category.name, None))
    return breadcrumbs
