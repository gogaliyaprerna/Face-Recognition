from django.shortcuts import render, redirect
import base64
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import *
import face_recognition

@csrf_exempt
def register(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        face_image_data = request.POST['image']

        if not face_image_data:
            return JsonResponse({'status': 'Error', 'message': 'No face image uploaded'}, status=400)
        face_image_data = face_image_data.split(",")[1]
        face_image = ContentFile(base64.b64decode(face_image_data), name=f'{username}.jpg')
        try:
            user = User(username=username)
            user.set_password(password)
            user.save()
        except Exception:
            return JsonResponse({'status': 'Error', 'message': 'User already exists'})

        Userimages.objects.create(user=user, face_image=face_image)

        return JsonResponse({'status': 'Success', 'message': 'User Registered Successfully'})

    return render(request, 'register.html')


@csrf_exempt
def login_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        face_image_data = request.POST['face_image']

        # Get the user by username
        try:
            user = User.objects.get(username=username)
            if not user.check_password(password):
                return JsonResponse({'status': 'error', 'message': 'Incorrect password.'})
        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'User not found.'})

        # Convert base64 image data to a file
        try:
            face_image_data = face_image_data.split(",")[1]
            uploaded_image = ContentFile(base64.b64decode(face_image_data), name=f'{username}_face.jpg')
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Failed to decode image: {str(e)}'})

        # Compare the uploaded face image with the stored face image
        try:
            uploaded_face_image = face_recognition.load_image_file(uploaded_image)
            uploaded_face_encoding = face_recognition.face_encodings(uploaded_face_image)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Error processing uploaded image: {str(e)}'})

        if uploaded_face_encoding:
            uploaded_face_encoding = uploaded_face_encoding[0]
            user_images = Userimages.objects.filter(user=user).first()
            if user_images:
                stored_face_image_path = user_images.face_image.path
                try:
                    stored_face_image = face_recognition.load_image_file(stored_face_image_path)
                    stored_face_encoding = face_recognition.face_encodings(stored_face_image)[0]

                    # Compare the faces
                    match = face_recognition.compare_faces([stored_face_encoding], uploaded_face_encoding)
                    if match[0]:
                        return JsonResponse({'status': 'success', 'message': 'Login successful!'})
                    else:
                        return JsonResponse({'status': 'error', 'message': 'Face recognition failed.'})
                except FileNotFoundError:
                    return JsonResponse({'status': 'error', 'message': 'Stored face image file is missing.'})
                except Exception as e:
                    return JsonResponse({'status': 'error', 'message': f'Error processing stored image: {str(e)}'})
            else:
                return JsonResponse({'status': 'error', 'message': 'No stored face image found for user.'})

        return JsonResponse({'status': 'error', 'message': 'No face detected in the image.'})

    return render(request, 'login.html')
