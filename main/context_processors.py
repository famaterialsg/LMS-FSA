# context_processors.py
from .models import SiteStatus

def site_status(request):
    # Lấy bản ghi đầu tiên của SiteStatus (trạng thái trang web)
    site_status = SiteStatus.objects.first()

    # Nếu có bản ghi, trả về trạng thái của nó, nếu không thì coi như trang web không bị khóa
    return {
        'is_site_locked': not site_status.status if site_status else False
    }
from django.urls import resolve

def breadcrumb(request):
    # Lấy session của breadcrumb hoặc khởi tạo mới
    breadcrumbs = request.session.get('breadcrumbs', [{"name": "Home", "url": "/"}])

    current_path = request.path
    app_name = request.resolver_match.app_name if request.resolver_match else None

    # Nếu đang ở trang chủ, chỉ hiển thị Home
    if current_path == '/':
        breadcrumbs = [{"name": "Home", "url": "/"}]
    else:
        # Kiểm tra nếu người dùng đang chuyển sang một module khác
        # Nếu không phải trang chủ và không cùng app, reset breadcrumb
        if breadcrumbs and (not current_path.startswith(breadcrumbs[-1]['url']) or (app_name and app_name != breadcrumbs[-1]['url'].strip('/'))):
            breadcrumbs = [{"name": "Home", "url": "/"}]

        # Lấy thông tin về tên đường dẫn hiện tại
        resolver_match = request.resolver_match
        if resolver_match:
            url_name = resolver_match.url_name

            # Thêm app_name vào breadcrumb nếu chưa có
            if app_name and not any(crumb["name"] == app_name.capitalize() for crumb in breadcrumbs):
                breadcrumbs.append({"name": app_name.capitalize(), "url": f"/{app_name}/"})

            # Thêm url_name vào breadcrumb nếu chưa có
            if url_name and not any(crumb["name"] == url_name.replace('_', ' ').capitalize() for crumb in breadcrumbs):
                breadcrumbs.append({"name": url_name.replace('_', ' ').capitalize(), "url": current_path})

    # Cập nhật session
    request.session['breadcrumbs'] = breadcrumbs

    return {
        'breadcrumb': breadcrumbs
    }
