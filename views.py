from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, logout, login as auth_login
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import uuid
from datetime import datetime
import os
from .models import *
from django.utils import timezone
from .utils import *
import random
from django.db.models import Q, Sum
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings

# Create your views here.

def register(request):
    if request.method == 'POST':
        firstName = request.POST.get('firstName')
        lastName = request.POST.get('lastName')
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirmPassword = request.POST.get('confirmPassword')

        if password != confirmPassword:
            messages.error(request, "Passwords do not match!")
            return redirect('register')
                                
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken. Please choose a different username.")
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already taken! Please use a different email.")
            return redirect('register')
        
        # Correct field names
        User.objects.create_user(
            first_name = firstName,
            last_name = lastName,
            username = username,
            email = email,
            password = password
        )
        messages.success(request, 'User registered successfully')
        return redirect('login')
  
    return render(request, 'register.html')

def login(request):
    if request.method == 'POST':

        email = request.POST.get('email')
        password = request.POST.get('password')
        print('pppppppppppppp')

        user = authenticate(request, email=email, password=password)
        if user is not None:
            auth_login(request, user)
            request.session['login'] = 'user'
            return redirect('user_dashboard')
        else:
            messages.error(request, "Invalid credentials.")
    return render(request, 'login.html')


def user_dashboard(request):
    return render(request, 'dashboard.html')


def logout(request):
    request.session.flush()
    return render(request, 'index.html')

@login_required
def upload_file(request):
    """Handle file upload with model storage"""
    
    if request.method == 'GET':
        # Render the upload page
        return render(request, 'upload_files.html')
    
    elif request.method == 'POST':
        try:
            # Check if files are present
            if not request.FILES:
                return JsonResponse({
                    'success': False,
                    'error': 'No files selected for upload'
                }, status=400)
            
            # Get all uploaded files from all categories
            uploaded_files = []
            file_fields = ['files', 'videos', 'audio']
            
            for field_name in file_fields:
                files = request.FILES.getlist(field_name)
                for file in files:
                    uploaded_files.append({
                        'file': file,
                        'category': field_name,
                        'original_name': file.name
                    })
            
            # If no files found in the expected fields, check for any files
            if not uploaded_files:
                for field_name in request.FILES:
                    files = request.FILES.getlist(field_name)
                    for file in files:
                        uploaded_files.append({
                            'file': file,
                            'category': 'general',
                            'original_name': file.name
                        })
            
            if not uploaded_files:
                return JsonResponse({
                    'success': False,
                    'error': 'No files found in request'
                }, status=400)
            
            # Process each file
            successful_uploads = []
            
            for file_info in uploaded_files:
                file = file_info['file']
                category = file_info['category']
                
                try:
                    # Read file content
                    file_content = file.read()
                    
                    # Generate unique filename
                    unique_id = uuid.uuid4().hex[:8]
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    file_extension = os.path.splitext(file.name)[1]
                    safe_filename = f"{timestamp}_{unique_id}{file_extension}"
                    
                    # Create upload directory based on category
                    upload_dir = f"uploads/{category}"
                    
                    # Ensure the directory exists (create directories if they don't exist)
                    if not os.path.exists(upload_dir):
                        os.makedirs(upload_dir)

                    # Save the file
                    file_path = f"{upload_dir}/{safe_filename}"
                    saved_path = default_storage.save(file_path, ContentFile(file_content))

                    print('ooooooooooooooooooooooooooooooooooooooooooo')

                    private_key, public_key, rsa_private_key, rsa_public_key = load_constant_keys()
                    signature = sign_message(private_key, file_path)
                    aes_key = generate_aes_key()
                    print(aes_key) 
                    encrypt_file_with_aes(file_path, aes_key)
                    
                    # Create database record
                    uploaded_file = UploadedFile.objects.create(
                        user=request.user,
                        original_name=file.name,
                        saved_name=safe_filename,
                        file_path=saved_path,
                        file_size=len(file_content),
                        category=category,
                        uploaded_at=timezone.now()
                    )

                    file_data = {
                        'id': str(uploaded_file.id),
                        'original_name': uploaded_file.original_name,
                        'saved_name': uploaded_file.saved_name,
                        'file_path': uploaded_file.file_path,
                        'file_size': uploaded_file.file_size,
                        'category': uploaded_file.category,
                        'uploaded_at': uploaded_file.uploaded_at.isoformat(),
                        'formatted_size': uploaded_file.formatted_size
                    }

                    print(file_data)
                    successful_uploads.append(file_data)

                    print(f"✅ Successfully uploaded: {file.name} as {safe_filename} (ID: {uploaded_file.id})")
                    
                except Exception as e:
                    print(f"❌ Error processing {file.name}: {str(e)}")
                    continue
            
            if successful_uploads:
                return JsonResponse({
                    'success': True,
                    'message': f'Successfully uploaded {len(successful_uploads)} file(s)',
                    'uploaded_files': successful_uploads,
                    'total_files': len(successful_uploads)
                })
            else:
                return JsonResponse({'success': False, 'error': 'No files were successfully uploaded'}, status=500)

        except Exception as e:
            print(f"❌ Upload error: {str(e)}")
            return JsonResponse({'success': False, 'error': f'Upload failed: {str(e)}'}, status=500)
    
    else:
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

def get_uploaded_files(request):
    """Get all uploaded files for the current user"""
    if request.user.is_authenticated:
        files = UploadedFile.objects.filter(user=request.user).order_by('-uploaded_at')
        file_list = []
        for file in files:
            file_list.append({
                'id': str(file.id),
                'original_name': file.original_name,
                'saved_name': file.saved_name,
                'file_path': file.file_path,
                'file_size': file.file_size,
                'formatted_size': file.formatted_size,
                'category': file.category,
                'uploaded_at': file.uploaded_at.isoformat(),
                'file_url': file.file_url
            })
        return JsonResponse({
            'success': True,
            'files': file_list,
            'total_files': len(file_list)
        })
    else:
        return JsonResponse({
            'success': False,
            'error': 'Authentication required'
        }, status=401)
    
@login_required
def file_list(request):
    """Display all files for the current user"""
    # Get filter parameters
    category = request.GET.get('category', 'all')
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', '-uploaded_at')
    page_number = request.GET.get('page', 1)
    
    # Start with user's files
    files = UploadedFile.objects.filter(user=request.user)
    
    # Apply filters
    if category != 'all':
        files = files.filter(category=category)
    
    if search_query:
        files = files.filter(
            Q(original_name__icontains=search_query) |
            Q(category__icontains=search_query)
        )
    
    # Apply sorting
    valid_sorts = {
        'newest': '-uploaded_at',
        'oldest': 'uploaded_at',
        'largest': '-file_size',
        'smallest': 'file_size',
        'name': 'original_name'
    }
    sort_field = valid_sorts.get(sort_by, '-uploaded_at')
    files = files.order_by(sort_field)
    
    # Pagination
    paginator = Paginator(files, 12)  # 12 files per page
    page_obj = paginator.get_page(page_number)
    
    # Calculate total storage used
    total_storage = files.aggregate(total_size=Sum('file_size'))['total_size'] or 0
    
    # Convert to human readable format
    if total_storage == 0:
        formatted_total = "0B"
    else:
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        size = total_storage
        while size >= 1024 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
        formatted_total = f"{size:.2f} {size_names[i]}"
    
    context = {
        'files': page_obj,
        'total_size': formatted_total,
        'current_category': category,
        'search_query': search_query,
        'sort_by': sort_by,
    }
    
    return render(request, 'viewFiles.html', context)

@login_required
def download_file(request, file_id):
    """Download a specific file"""
    try:
        file_obj = get_object_or_404(UploadedFile, id=file_id, user=request.user)
        file_path = os.path.join(settings.MEDIA_ROOT, file_obj.file_path)
        
        if os.path.exists(file_path):
            # For encrypted files, you might want to decrypt here
            with open(file_path, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type="application/octet-stream")
                response['Content-Disposition'] = f'attachment; filename="{file_obj.original_name}"'
                return response
        else:
            return JsonResponse({'error': 'File not found on server'}, status=404)
            
    except UploadedFile.DoesNotExist:
        return JsonResponse({'error': 'File not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Download failed: {str(e)}'}, status=500)
    

@login_required
def delete_file(request, file_id):
    """Delete a specific file"""
    try:
        file_obj = get_object_or_404(UploadedFile, id=file_id, user=request.user)
        file_path = os.path.join(settings.MEDIA_ROOT, file_obj.file_path)
        
        # Delete physical file
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete database record
        file_obj.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'File deleted successfully'
            })
        else:
            messages.success(request, 'File deleted successfully')
            return redirect('file_list')
        
    except UploadedFile.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'File not found'}, status=404)
        else:
            messages.error(request, 'File not found')
            return redirect('file_list')
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': f'Delete failed: {str(e)}'}, status=500)
        else:
            messages.error(request, f'Delete failed: {str(e)}')
            return redirect('file_list')
    

