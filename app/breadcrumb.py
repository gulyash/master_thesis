def get_breadcrumb_data(request):
    breadcrumbs = [item.replace('-', ' ').title() for item in request.rel_url.parts if item != '/']
    return breadcrumbs
