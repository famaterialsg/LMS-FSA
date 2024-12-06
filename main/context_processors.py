# context_processors.py
from .models import SiteStatus
from django.urls import resolve

def site_status(request):
    # Lấy bản ghi đầu tiên của SiteStatus (trạng thái trang web)
    site_status = SiteStatus.objects.first()

    # Nếu có bản ghi, trả về trạng thái của nó, nếu không thì coi như trang web không bị khóa
    return {
        'is_site_locked': not site_status.status if site_status else False
    }


def breadcrumb(request):
    # Lấy session của breadcrumb hoặc khởi tạo mới
    breadcrumbs = request.session.get('breadcrumbs', [{"name": "Home", "url": "/"}])

    current_path = request.path
    resolver_match = request.resolver_match
    app_name = resolver_match.app_name if resolver_match else None

    # Nếu đang ở trang chủ, chỉ hiển thị Home
    if current_path == '/':
        breadcrumbs = [{"name": "Home", "url": "/"}]
    else:
        if resolver_match:
            url_name = resolver_match.url_name
            current_title = url_name.replace('_', ' ').capitalize() if url_name else ""

            # Kiểm tra nếu breadcrumbs hiện tại không khớp với đường dẫn mới
            if not breadcrumbs or breadcrumbs[-1]["url"] != current_path:
                # Điều kiện đặc biệt cho Book search
                if "book search" in current_title.lower():
                    breadcrumbs = [{"name": "Home", "url": "/"}]
                    breadcrumbs.append({"name": "Book search", "url": current_path})
                
                elif app_name == "reports":
                    breadcrumbs = [{"name": "Home", "url": "/"}]
                    
                    # Kiểm tra nếu là trang báo cáo chính (dashboard)
                    if current_path == "/reports/":
                        breadcrumbs.append({"name": "Report", "url": "/reports/"})
                    else:
                        # Các báo cáo khác
                        breadcrumbs.append({"name": "Report", "url": "/reports/"})
                        breadcrumbs.append({"name": current_title, "url": current_path})


                # Điều kiện đặc biệt cho module_group/modules
                elif current_path.startswith('/module_group/modules/'):
                    breadcrumbs = [{"name": "Home", "url": "/"}]
                    breadcrumbs.append({"name": "Module Group List", "url": "/module_group/"})  # Sửa thành /module_group/
                    breadcrumbs.append({"name": "Modules", "url": current_path})
                
                # Điều kiện đặc biệt cho Activity, Achievement, Quiz Bank
                elif app_name in ["activity", "achievement", "quiz_bank"]:
                    breadcrumbs = [{"name": "Home", "url": "/"}]
                    breadcrumbs.append({"name": app_name.capitalize(), "url": current_path})
                
                # Xử lý các module khác
                elif "list" in current_title.lower():
                    breadcrumbs = [{"name": "Home", "url": "/"}]
                    breadcrumbs.append({"name": f"{app_name.capitalize()} List", "url": current_path})
                else:
                    # Xử lý cho các chức năng khác
                    if len(breadcrumbs) > 1 and "list" in breadcrumbs[-1]["name"].lower():
                        breadcrumbs.append({"name": current_title, "url": current_path})
                    else:
                        breadcrumbs = [{"name": "Home", "url": "/"}]
                        breadcrumbs.append({"name": f"{app_name.capitalize()} List", "url": f"/{app_name}/list/"})
                        breadcrumbs.append({"name": current_title, "url": current_path})

    # Cập nhật session
    request.session['breadcrumbs'] = breadcrumbs

    return {
        'breadcrumb': breadcrumbs
    }