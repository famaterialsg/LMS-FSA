import json
from django.shortcuts import render
from django.http import Http404, HttpResponse, JsonResponse, FileResponse
from django.core.files.storage import FileSystemStorage
from LMS_SYSTEM import settings111
from module_group.models import ModuleGroup
from .forms import ExcelUploadForm, MultipleTxtUploadForm, ExamGenerationForm
from tools.libs.utils import excel_to_json, word_to_json, generator
from tools.libs.txtToJson import txt_to_json, extract_code_name
import zipfile
import os
from django.core.files.storage import default_storage
from io import BytesIO, StringIO
import pandas as pd
from django.urls import reverse
from datetime import datetime

def excel_to_json_view(request):
    module_groups = ModuleGroup.objects.all()
    file_names_and_urls = []  # Lưu trữ tên file và URL tải xuống

    # Xóa các file JSON cũ và file ZIP trong thư mục media trước khi xử lý
    for file_name in os.listdir(settings111.MEDIA_ROOT):
        if file_name.endswith('.json') or file_name == 'all_files.zip':
            file_path = os.path.join(settings111.MEDIA_ROOT, file_name)
            if os.path.isfile(file_path):
                os.remove(file_path)

    # Xử lý yêu cầu POST thông thường
    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            json_files = []
            try:
                for excel_file in form.cleaned_data['files']:
                    excel_data = pd.read_excel(excel_file, sheet_name=None)
                    for sheet_name, df in excel_data.items():
                        json_output = excel_to_json(df)
                        json_filename = f"{excel_file.name.split('.')[0]}.json"
                        json_files.append((json_filename, json_output))
                        # Lưu JSON vào thư mục MEDIA
                        json_file_path = os.path.join(settings111.MEDIA_ROOT, json_filename)
                        with open(json_file_path, 'w') as json_file:
                            json_file.write(json_output)
                        
                        file_url = reverse('tools:download_file', args=[json_filename])
                        file_names_and_urls.append({'file_name': json_filename, 'file_url': file_url})
                        
                # Tạo file ZIP chứa tất cả các file JSON
                zip_filename = 'all_files.zip'
                zip_file_path = os.path.join(settings111.MEDIA_ROOT, zip_filename)
                with zipfile.ZipFile(zip_file_path, 'w') as zip_file:
                    for json_filename, json_string in json_files:
                        zip_file.writestr(json_filename, json_string)

                # Tạo URL tải file ZIP
                download_url = os.path.join(settings111.MEDIA_URL, zip_filename)

                success_message = 'Your Excel files have been successfully converted to JSON. You can download them individually or as a ZIP file.'
                print(file_names_and_urls)
                # Trả về trang với thông báo thành công và danh sách file JSON
                return render(request, 'tool_excel_to_json.html', {
                    'module_groups': module_groups,
                    
                    'success_message': success_message,
                    'file_names_and_urls': file_names_and_urls,
                    'download_url': download_url
                })

            except Exception as e:
                print(f"Error processing Excel file '{excel_file.name}': {e}")
                # Thêm xử lý lỗi nếu cần

    else:
        form = ExcelUploadForm()

    return render(request, 'tool_excel_to_json.html', {'module_groups': module_groups,'form': form})

def txt_to_json_view(request):
    module_groups = ModuleGroup.objects.all()
    file_names_and_urls = []  # To store file names and individual download URLs for JSON files

    # Delete old JSON and ZIP files in the MEDIA folder before new processing
    for file_name in os.listdir(settings111.MEDIA_ROOT):
        if file_name.endswith('.json') or file_name == 'all_files.zip':
            file_path = os.path.join(settings111.MEDIA_ROOT, file_name)
            if os.path.isfile(file_path):
                os.remove(file_path)

    if request.method == 'POST':
        num_files = int(request.POST.get('number_of_files', 1))
        form = MultipleTxtUploadForm(request.POST, num_files=num_files)

        if form.is_valid():
            # Create a temporary ZIP file in memory
            zip_buffer = BytesIO()

            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for i in range(num_files):
                    txt_content = form.cleaned_data.get(f'txt_file_{i}')
                    if txt_content:
                        file_name = extract_code_name(txt_content) or f'file_{i + 1}'
                        file_like = StringIO(txt_content)
                        json_output = txt_to_json(file_like, file_name)  # Convert TXT to JSON
                        json_file_name = f'{file_name}.json'

                        json_data = json.loads(json_output)
                        num_questions = len(json_data.get('mc_questions', []))
                        
                        # Write JSON data into the ZIP file
                        zip_file.writestr(json_file_name, json_output)
                        file_names_and_urls.append(
                            (json_file_name, reverse('tools:download_file', args=[json_file_name]), num_questions)
                        )

                        # Save JSON file to MEDIA_ROOT directory
                        json_file_path = os.path.join(settings111.MEDIA_ROOT, json_file_name)
                        with open(json_file_path, 'w') as json_file:
                            json_file.write(json_output)

            zip_buffer.seek(0)

            # Create ZIP file name
            zip_filename = 'all_files.zip'
            zip_file_path = os.path.join(settings111.MEDIA_ROOT, zip_filename)

            # Save the ZIP file to the temporary folder
            with open(zip_file_path, 'wb') as f:
                f.write(zip_buffer.getvalue())

            # Download URL for the ZIP file
            download_url = reverse('tools:download_all_as_zip', args=[zip_filename])

            success_message = 'Your JSON files have been successfully created. You can download them individually or as a ZIP file.'
            
            # Return the page with information and download links
            return render(request, 'tool_txt_to_json.html', {
                'module_groups': module_groups,
                'file_names_and_urls': file_names_and_urls,
                'success_message': success_message,
                'download_url': download_url,
            })

    else:
        form = MultipleTxtUploadForm(initial={'number_of_files': 1})  # Default to 1 file

    return render(request, 'tool_txt_to_json.html', {
        'module_groups': module_groups,
        'form': form
    })

def exam_generator_view(request):
    module_groups = ModuleGroup.objects.all()
    form = ExamGenerationForm()
    success_message = None  
    download_url = None
    sheet_count = 0

    if request.method == 'POST':
        form = ExamGenerationForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']
            number_of_exams = form.cleaned_data['number_of_exams']
            number_of_questions_per_exam = form.cleaned_data['number_of_questions']

            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                try:
                    # Kiểm tra nếu file trống
                    if excel_file.size == 0:
                        return HttpResponse("Uploaded file is empty.", status=400)

 #                   print(f"Uploaded file name: {excel_file.name}")
 #                   print(f"Uploaded file size: {excel_file.size} bytes")
                    df_combined = pd.DataFrame()

                    # Đọc file theo định dạng tương ứng
                    if excel_file.name.endswith('.xlsx'):
                        xls = pd.ExcelFile(excel_file, engine='openpyxl')
                        sheet_count = len(xls.sheet_names)

                    elif excel_file.name.endswith('.csv'):
                        try:
                            df_combined = pd.read_csv(excel_file, encoding='utf-8', header=0)
                        except UnicodeDecodeError:
                            try:
                                df_combined = pd.read_csv(excel_file, encoding='latin1', header=0)
                            except UnicodeDecodeError:
                                df_combined = pd.read_csv(excel_file, encoding='windows-1252', header=0)

                    elif excel_file.name.endswith('.json'):
                        df_combined = pd.read_json(excel_file)

                    else:
                        return HttpResponse("Unsupported file format.", status=400)

                    # Kiểm tra xem DataFrame có dữ liệu không
                    if xls is not None: 
                        pass
                    elif df_combined.empty or df_combined.shape[1] == 0:
                        return HttpResponse("No columns found in the uploaded file.", status=400)

#                    if not hasattr(xls, 'sheet_name'):
#                        return HttpResponse('No sheet found!', status=400)
                    #print(df_combined.head())  # Debug: in ra dữ liệu

                    total_files_created = 0
                    sheet_number = 1

                    # đọc số sheet  
                    for sheet_name in xls.sheet_names:
                        df_sheet = pd.read_excel(xls, sheet_name=sheet_name)

                        if df_sheet.empty or df_sheet.shape[1]==0:
                            continue
                        df_combined = df_sheet


                    # Tạo các bài kiểm tra
                        for count in range(number_of_exams):
                            output_file, df_combined = generator(excel_file, {sheet_name: number_of_questions_per_exam})  # Thay đổi tên sheet nếu cần
                            json_output = excel_to_json(df_combined)

                            # Lưu dữ liệu JSON vào ZIP
                            json_file_name = f'sheet_{sheet_number}_exam_{count + 1}.json'
                            zip_file.writestr(json_file_name, json_output)
                            total_files_created += 1

                            # Lưu file Excel vào ZIP
                            excel_file_name = f'sheet_{sheet_number}_exam_{count + 1}.xlsx'
                            zip_file.writestr(excel_file_name, output_file.getvalue())
                            total_files_created += 1

                        sheet_number += 1
                except Exception as e:
                    return HttpResponse(f"An error occurred while processing the file: {str(e)}", status=400)

            zip_buffer.seek(0)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            zip_filename = f'exams_{timestamp}.zip'
            zip_file_path = os.path.join(settings111.MEDIA_ROOT, zip_filename)

            with open(zip_file_path, 'wb') as f: 
                f.write(zip_buffer.getvalue())

            download_url = reverse('tools:download_zip_file', args=[zip_filename])
            success_message = f'{total_files_created} files were successfully created. Click the button below to download.'

            return render(request, 'generate_exams.html', {
                'module_groups': module_groups,
                'form': form,
                'success_message': success_message,
                'download_url': download_url,
                'sheet_count': sheet_count,
            })

    return render(request, 'generate_exams.html', {
        'module_groups': module_groups,
        'form': form,
        'sheet_count': sheet_count,
    })
 
def download_zip_file(request, filename): # main
    file_path = os.path.join(settings111.MEDIA_ROOT, filename)

    if not os.path.exists(file_path):
        return HttpResponse("File not found.", status=404)

    with open(file_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response

def download_zip_file_2(request, filename): # dự trữ 2
    file_path = os.path.join(settings111.MEDIA_ROOT, filename)
    return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=filename)

def download_all_as_zip(request, filename):
    # Path to the ZIP file
    zip_file_path = os.path.join(settings111.MEDIA_ROOT, filename)

    # Check if the file exists
    if os.path.exists(zip_file_path):
        # Open the ZIP file and return it to the user
        with open(zip_file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
    else:
        # Return an error if the file does not exist
        return HttpResponse("File not found.", status=404)


def download_file(request, filename):
    file_path = os.path.join(settings111.MEDIA_ROOT, filename)
    
    with open(file_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response


