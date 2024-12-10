from django.http import HttpResponse
from django.urls import reverse
from .models import SiteStatus

class SiteLockMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Bỏ qua các yêu cầu vào trang admin, trang mở khóa và nếu là admin
        if request.path.startswith(reverse('admin:index')) or \
           request.path.startswith('/admin/') or \
           request.path.startswith('/unlock-site/') or \
           request.user.is_staff:  # Kiểm tra xem người dùng có phải là admin không
            return self.get_response(request)

        # Kiểm tra trạng thái khóa/mở khóa trang web
        site_status = SiteStatus.objects.first()

        # Nếu trạng thái là 'khóa' và trang không phải là trang admin hoặc trang mở khóa, trả về lỗi 503
        if site_status and not site_status.status:
            # Nếu trang không phải trang admin hoặc không phải là trang mở khóa
            if not request.path.startswith('/unlock-site/'):
                return HttpResponse("The website is currently undergoing maintenance. Please return later.", status=503)

        # Tiếp tục xử lý yêu cầu bình thường
        response = self.get_response(request)
        return response
