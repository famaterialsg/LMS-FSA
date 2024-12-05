from django.shortcuts import render, get_object_or_404, redirect
from role.models import Role, RoleModule
from role.forms import RoleForm, ExcelImportForm
from django.contrib import messages
from django.http import HttpResponse
from module_group.models import Module
from django.contrib.auth.models import Permission
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from user.models import Profile
from .admin import RoleResource
from tablib import Dataset
from user.models import User

def role_list(request):
    # Lấy danh sách tất cả các role ngoại trừ "Super Admin"
    roles = Role.objects.exclude(role_name="Super Admin")  # Loại bỏ Super Admin khỏi danh sách roles

    # Lấy tất cả RoleModule (Role - Module liên kết)
    role_modules = RoleModule.objects.all()

    # Form nhập liệu Excel (nếu có)
    form = ExcelImportForm()

    # Trả lại template với các biến đã được cung cấp
    return render(request, 'role_list.html', {
        'roles': roles,
        'form': form,
        'role_modules': role_modules
    })


def role_add(request, role_id=None):
    if role_id:  # Nếu đang chỉnh sửa một role hiện có
        role = get_object_or_404(Role, id=role_id)
        form = RoleForm(request.POST or None, instance=role)
    else:  # Nếu đang tạo mới một role
        role = None
        form = RoleForm(request.POST or None)

    all_modules = Module.objects.all()  # Lấy tất cả các module

    if request.method == 'POST':
        if form.is_valid():
            new_role = form.save()  # Lưu role
            selected_modules_ids = request.POST.getlist('modules')  # Lấy danh sách module được chọn

            # Cập nhật RoleModule (thêm hoặc xóa các module liên quan)
            RoleModule.objects.filter(role=new_role).delete()  # Xóa các liên kết cũ
            for module_id in selected_modules_ids:
                module = Module.objects.get(id=module_id)
                RoleModule.objects.create(role=new_role, module=module)

            # Thông báo thành công và chuyển hướng
            messages.success(request, 'Role and associated modules have been successfully added/updated.')
            return redirect('role:role_list')

    # Xác định các module đã được chọn (nếu đang chỉnh sửa)
    selected_modules = (
        RoleModule.objects.filter(role=role).values_list('module', flat=True) if role else []
    )

    context = {
        'form': form,
        'all_modules': all_modules,
        'selected_modules': selected_modules,
    }
    return render(request, 'role_form.html', context)


def role_edit(request, pk):
    role = get_object_or_404(Role, pk=pk)  # Lấy role cần chỉnh sửa
    form = RoleForm(request.POST or None, instance=role)  # Tạo form liên kết với role
    all_modules = Module.objects.all()  # Lấy danh sách tất cả module

    if request.method == 'POST':
        if form.is_valid():
            updated_role = form.save()  # Lưu role

            # Lấy danh sách module được chọn từ form
            selected_modules_ids = request.POST.getlist('modules')

            # Cập nhật RoleModule (xóa các liên kết cũ và thêm mới)
            RoleModule.objects.filter(role=updated_role).delete()  # Xóa liên kết cũ
            for module_id in selected_modules_ids:
                module = Module.objects.get(id=module_id)
                RoleModule.objects.create(role=updated_role, module=module)

            # Thông báo thành công và chuyển hướng
            messages.success(request, 'Role and associated modules have been successfully updated.')
            return redirect('role:role_list')

    # Lấy danh sách module đã được chọn để hiển thị
    selected_modules = RoleModule.objects.filter(role=role).values_list('module', flat=True)

    context = {
        'form': form,
        'all_modules': all_modules,
        'selected_modules': selected_modules,
    }
    return render(request, 'role_form.html', context)

def role_delete(request, pk):
    # Lấy đối tượng role theo primary key
    role = get_object_or_404(Role, pk=pk)
    
    # Kiểm tra xem có người dùng nào đang mang role này hay không
    users_with_role = User.objects.filter(profile__role=role)
    error_message = None  # Biến lưu thông báo lỗi nếu cần

    if request.method == 'POST':
        if users_with_role.exists():
            error_message = "Không thể xóa role này vì có người dùng đang mang role này."
        else:
            role.delete()
            messages.success(request, "Role đã được xóa thành công.")
            return redirect('role:role_list')  # Quay lại danh sách role

    # Render trang xác nhận xóa với role, danh sách người dùng và thông báo lỗi
    return render(request, 'role_confirm_delete.html', {
        'role': role,
        'users_with_role': users_with_role,  # Truyền danh sách người dùng mang role này
        'error_message': error_message,      # Truyền thông báo lỗi nếu có
    })


def export_roles(request):
    # Tạo resource
    resource = RoleResource()
    queryset = Role.objects.all()

    # Xuất dữ liệu
    dataset = resource.export(queryset)

    # Tạo phản hồi với định dạng Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=lms_roles.xlsx'

    # Ghi dữ liệu vào phản hồi dưới dạng XLSX
    response.write(dataset.xlsx)  # Đảm bảo sử dụng đúng phương thức để xuất ra xlsx

    return response


def import_roles(request):
    resource = RoleResource()

    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')

        # Kiểm tra xem file có được tải lên không
        if not uploaded_file:
            messages.error(request, "Không tìm thấy tệp tin để nhập.")
            return redirect('role:role_list')

        if uploaded_file.size == 0:  # Kiểm tra nếu tệp rỗng
            messages.error(request, "Tệp không được để trống.")
            return redirect('role:role_list')

        file_format = uploaded_file.name.split('.')[-1].lower()
        dataset = Dataset()

        # Xử lý định dạng tệp
        formats = {
            'csv': lambda: dataset.load(uploaded_file.read().decode('utf-8'), format='csv'),
            'json': lambda: dataset.load(uploaded_file.read().decode('utf-8'), format='json'),
            'yaml': lambda: dataset.load(uploaded_file.read().decode('utf-8'), format='yaml'),
            'tsv': lambda: dataset.load(uploaded_file.read().decode('utf-8'), format='tsv'),
            'xlsx': lambda: dataset.load(uploaded_file.read(), format='xlsx'),
        }

        # Kiểm tra và xử lý tệp
        try:
            if file_format in formats:
                formats[file_format]()  # Gọi hàm xử lý định dạng
            else:
                messages.error(request, "Định dạng tệp không hợp lệ. Hỗ trợ các định dạng: csv, json, yaml, tsv, xlsx.")
                return redirect('role:role_list')
        except Exception as e:
            messages.error(request, f"Lỗi khi đọc tệp: {e}")
            return redirect('role:role_list')

        # Kiểm tra và nhập dữ liệu
        result = resource.import_data(dataset, dry_run=True)

        if not result.has_validation_errors():
            resource.import_data(dataset, dry_run=False)
            messages.success(request, "Người dùng đã được nhập thành công!")
        else:
            invalid_rows = result.invalid_rows
            error_messages = [f"Lỗi tại hàng {row['row']}: {row['error']}" for row in invalid_rows]
            messages.error(request, "Có lỗi khi nhập người dùng:\n" + "\n".join(error_messages))

        return redirect('role:role_list')

    messages.error(request, "Không thể nhập người dùng.")
    return redirect('role:role_list')


@login_required
def select_role(request):
    if request.method == 'POST':
        selected_role_name = request.POST.get('role')  # Get role_name instead of id
        if selected_role_name:
            try:
                role = Role.objects.get(role_name=selected_role_name)
                if request.user.is_superuser or request.user.profile.role.role_name == "Manager":
                    request.session['temporary_role'] = role.role_name
                    messages.success(request, "Temporary role has been saved.")
                    
                    # If the selected role is "Student", redirect to the Student Portal
                    if role.role_name == "Student":
                        return redirect('student_portal:course_list')
                else:
                    profile = Profile.objects.get(user=request.user)
                    profile.role = role
                    profile.save()
                    messages.success(request, "Role has been updated.")
            except Role.DoesNotExist:
                messages.error(request, "Role does not exist.")
            except Profile.DoesNotExist:
                messages.error(request, "This user does not have a profile.")
        else:
            messages.warning(request, "Please select a role.")
    return redirect('main:home')


@login_required
def reset_role(request):
    if request.method == 'POST':
        # Xóa role tạm thời khỏi session
        if 'temporary_role' in request.session:
            del request.session['temporary_role']
            messages.success(request, "Vai trò tạm thời đã được đặt lại. Bạn đã khôi phục quyền superuser.")
        else:
            messages.info(request, "Không có vai trò tạm thời nào để đặt lại.")

    return redirect('main:home')
