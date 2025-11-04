from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Workspace
from django.utils.timezone import localtime
from rest_framework_simplejwt.authentication import JWTAuthentication
import secrets
from datetime import timedelta
from django.utils.timezone import now, localtime
from PIL import Image, UnidentifiedImageError
from .models import TrainingImage
from users.models import CustomUser
import requests
from utils.custompagination import CustomPagination

User = get_user_model()

class WorkspaceViewSet(viewsets.ViewSet):
    # authentication_classes = [JWTAuthentication]
    # permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="List all workspaces (with optional filters)",
        manual_parameters=[
            openapi.Parameter(
                'created_by', openapi.IN_QUERY,
                description="Filter workspaces by creator's user ID",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'field_assistant_id', openapi.IN_QUERY,
                description="Filter workspaces by Field Assistant's user ID",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'search_key', openapi.IN_QUERY,
                description="Search workspace by name",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'page', openapi.IN_QUERY,
                description="Page number for pagination",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'page_size', openapi.IN_QUERY,
                description="Page size for pagination",
                type=openapi.TYPE_INTEGER
            ),
        ],
        responses={200: openapi.Response(description="Paginated list of workspaces")}
    )
    def list(self, request):
        created_by_id = request.query_params.get("created_by")
        search_key = request.query_params.get("search_key")
        field_assistant_id = request.query_params.get("field_assistant_id")

        raw_workspaces = Workspace.objects.all().order_by('-id')

        if created_by_id:
            raw_workspaces = raw_workspaces.filter(created_by__id=created_by_id)

        if field_assistant_id:
            raw_workspaces = raw_workspaces.filter(field_assistant__id=field_assistant_id)

        if search_key:
            raw_workspaces = raw_workspaces.filter(name__icontains=search_key)

        # Apply pagination
        paginator = CustomPagination()
        paginated_workspaces = paginator.paginate_queryset(raw_workspaces, request)

        workspaces = []
        for ws in paginated_workspaces:
            workspaces.append({
                "id": ws.id,
                "name": ws.name,
                "created_at": localtime(ws.created_at).strftime('%Y-%m-%dT%H:%M:%S'),
                "created_by_id": ws.created_by.id if ws.created_by else None,
                "created_by_name": f"{ws.created_by.first_name} {ws.created_by.last_name}".strip() if ws.created_by else None,
                "is_activated": ws.is_activated,
                "activation_key": ws.activation_key,
                "activation_key_expiry": ws.activation_key_expiry,
                "failed_activation_attempts": ws.failed_activation_attempts,
                "field_assistant_id": ws.field_assistant.id if ws.field_assistant else None,
                "field_assistant_name": f"{ws.field_assistant.first_name} {ws.field_assistant.last_name}".strip() if ws.field_assistant else None,
                "field_assistant_phone_number": ws.field_assistant.phone_number if ws.field_assistant else None,
                "sku_count": ws.sku_count if ws.sku_count else None
            })

        return paginator.get_paginated_response(workspaces)




    @swagger_auto_schema(
        operation_summary="Retrieve a workspace by ID",
        responses={200: openapi.Response(description="Workspace details")}
    )
    def retrieve(self, request, pk=None):
        try:
            ws = Workspace.objects.get(id=pk)
            workspace = {
                "id": ws.id,
                "name": ws.name,
                "created_at": localtime(ws.created_at).strftime('%Y-%m-%dT%H:%M:%S'),
                "created_by_id": ws.created_by.id if ws.created_by else None,
                "created_by_name": f"{ws.created_by.first_name} {ws.created_by.last_name}".strip() if ws.created_by else None,
                "is_activated": ws.is_activated,
                "activation_key": ws.activation_key,
                "activation_key_expiry": ws.activation_key_expiry,
                "failed_activation_attempts": ws.failed_activation_attempts,
                "field_assistant_id": ws.field_assistant.id if ws.field_assistant else None,
                "field_assistant_name": f"{ws.field_assistant.first_name} {ws.field_assistant.last_name}".strip() if ws.field_assistant else None,
                "field_assistant_phone_number": ws.field_assistant.phone_number if ws.field_assistant else None,
                "sku_count":ws.sku_count if ws.sku_count else None
                
            }
            return Response({"results": workspace, "status": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except Workspace.DoesNotExist:
            return Response({"message": "Workspace not found", "status": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)


    @swagger_auto_schema(
        operation_summary="Create a new workspace",
        operation_description="Creates a workspace. The `name` must be unique. `created_by` must be user ID. Only authorized users can create a workspace.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["name", "created_by"],
            properties={
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Unique name of the workspace"),
                "created_by": openapi.Schema(type=openapi.TYPE_INTEGER, description="User ID creating the workspace"),
            }
        ),
        responses={
            201: openapi.Response(description="Workspace created successfully"),
            400: openapi.Response(description="Validation error"),
            403: openapi.Response(description="User not authorized to create workspace"),
        }
    )
    def create(self, request):
        name = request.data.get("name")
        created_by_id = request.data.get("created_by")

        if not name or not created_by_id:
            return Response(
                {"message": "Both 'name' and 'created_by' are required.","status":status.HTTP_400_BAD_REQUEST},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check for user-level workspace name uniqueness
        if Workspace.objects.filter(name__iexact=name, created_by_id=created_by_id).exists():
            return Response(
                {"message": "You already have a workspace with this name", "status": status.HTTP_400_BAD_REQUEST},
                status=status.HTTP_400_BAD_REQUEST
            )


        try:
            creator = User.objects.get(pk=created_by_id)
        except User.DoesNotExist:
            return Response(
                {"message": "Invalid creator user ID.","status":status.HTTP_400_BAD_REQUEST},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not creator.is_authorized:
            return Response(
                {"message": "User is not authorized to create a workspace.","status":status.HTTP_400_BAD_REQUEST},
                status=status.HTTP_403_FORBIDDEN
            )

        workspace = Workspace.objects.create(
            name=name,
            created_by=creator,
            created_at=timezone.now()
        )
        
        webhook_url = "https://chat.googleapis.com/v1/spaces/AAQA_GVsRBw/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=H3N0Z8RohdpZtvPYcMgCGE3Z2CmauEoLXHFsTD3q_l0"
        created_at_str = localtime(workspace.created_at).strftime('%Y-%m-%d %H:%M')

        message_payload = {
            "text": f"""🏗️ *New Workspace Created!*
            📛 Workspace Name: {workspace.name}
            👤 Created By: {creator.first_name} {creator.last_name}
            📅 Created At: {created_at_str}
            ✅ Status: {"Activated" if workspace.is_activated else "Not Activated"}"""
                }

        try:
            resp = requests.post(webhook_url, json=message_payload)
            if resp.status_code != 200:
                print(f"[Webhook] Failed with status {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"[Webhook] Error sending message: {e}")
            
        return Response({
            "message": "Workspace created successfully",
            "workspace": {
                "id": workspace.id,
                "name": workspace.name,
                "created_at": localtime(workspace.created_at).strftime('%Y-%m-%dT%H:%M:%S'),
                "created_by": workspace.created_by.id,
                "is_activated": workspace.is_activated
            },
            "status": status.HTTP_201_CREATED
        }, status=status.HTTP_201_CREATED)
        
    @swagger_auto_schema(
        operation_summary="Update the SKU count of a workspace",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["sku_count"],
            properties={
                "sku_count": openapi.Schema(type=openapi.TYPE_INTEGER, description="New SKU count value")
            }
        ),
        responses={
            200: openapi.Response(description="Workspace SKU count updated successfully"),
            400: openapi.Response(description="Validation error"),
            404: openapi.Response(description="Workspace not found"),
        }
    )
    def update(self, request, pk=None):
        try:
            workspace = Workspace.objects.get(pk=pk)
        except Workspace.DoesNotExist:
            return Response({"message": "Workspace not found", "status": status.HTTP_404_NOT_FOUND},
                            status=status.HTTP_404_NOT_FOUND)

        sku_count = request.data.get("sku_count")
        if sku_count is None:
            return Response({"message": "sku_count is required", "status": status.HTTP_400_BAD_REQUEST},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            sku_count = int(sku_count)
            if sku_count < 5:
                raise ValueError()
        except ValueError:
            return Response({"message": "Sku count must not be less than 5", "status": status.HTTP_400_BAD_REQUEST},
                            status=status.HTTP_400_BAD_REQUEST)

        workspace.sku_count = sku_count
        workspace.save()

        return Response({
            "message": "SKU count updated successfully",
            "workspace": {
                "id": workspace.id,
                "sku_count": workspace.sku_count
            },
            "status": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)



class WorkspaceActivationViewSet(viewsets.ViewSet):

    @swagger_auto_schema(
        operation_summary="Generate activation key for a workspace",
        operation_description="Provide workspace ID and assistant ID to generate activation key (valid for 30 mins).",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["workspace_id", "field_assistant"],
            properties={
                "workspace_id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID of the workspace"),
                "field_assistant": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID of the field assistant (CustomUser)"),
            }
        ),
        responses={
            200: openapi.Response(description="Activation key generated successfully"),
            400: openapi.Response(description="Validation error or workspace not found")
        }
    )
    def create(self, request):
        workspace_id = request.data.get("workspace_id")
        assistant_id = request.data.get("field_assistant")

        if not workspace_id or not assistant_id:
            return Response({"message": "workspace_id and field_assistant ID are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            workspace = Workspace.objects.get(id=workspace_id)
        except Workspace.DoesNotExist:
            return Response({"message": "Workspace not found"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            assistant = CustomUser.objects.get(id=assistant_id)
        except CustomUser.DoesNotExist:
            return Response({"message": "Field assistant with this ID not found"}, status=status.HTTP_400_BAD_REQUEST)

        # Generate activation key and expiry
        activation_key = secrets.token_urlsafe(16)
        expiry_time = timezone.now() + timedelta(minutes=30)

        # Assign and save
        workspace.activation_key = activation_key
        workspace.activation_key_expiry = expiry_time
        workspace.field_assistant = assistant
        workspace.save()

        webhook_url = "https://chat.googleapis.com/v1/spaces/AAQA_GVsRBw/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=H3N0Z8RohdpZtvPYcMgCGE3Z2CmauEoLXHFsTD3q_l0"
        assistant_name = f"{assistant.first_name} {assistant.last_name}".strip()
        phone = assistant.phone_number or "N/A"
        expires_at_str = localtime(expiry_time).strftime("%Y-%m-%d %H:%M")

        message_payload = {
            "text": f"""🔑 *Workspace Activation Key Generated*
            📛 Workspace Name: {workspace.name}
            👤 Field Assistant: {assistant_name}
            📱 Phone: {phone}
            ⏰ Expires At: {expires_at_str}
            🔗 Activation Key: {activation_key}"""
        }

        try:
            resp = requests.post(webhook_url, json=message_payload)
            if resp.status_code != 200:
                print(f"[Webhook] Failed: {resp.status_code} {resp.text}")
        except Exception as e:
            print(f"[Webhook] Error: {e}")
        
        return Response({
            "message": "Activation key generated successfully",
            "workspace_id": workspace.id,
            "activation_key": activation_key,
            "activation_key_expiry": localtime(expiry_time).strftime("%Y-%m-%dT%H:%M:%S"),
            "field_assistant_id": assistant.id
        }, status=status.HTTP_200_OK)

        
        

class WorkspaceValidateViewSet(viewsets.ViewSet):
    """
    POST API to validate a workspace activation key and activate if valid and within 30 minutes.
    """

    @swagger_auto_schema(
        operation_summary="Validate Workspace Activation Key",
        operation_description="Validates and activates a workspace if the activation key is valid and within 30 minutes. "
                              "After 3 failed attempts, the user is de-authorized.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["workspace_id", "activation_key"],
            properties={
                "workspace_id": openapi.Schema(type=openapi.TYPE_INTEGER, description="Workspace ID"),
                "activation_key": openapi.Schema(type=openapi.TYPE_STRING, description="Activation key to validate"),
            }
        ),
        responses={
            200: openapi.Response(description="Activation key is valid and workspace activated."),
            400: openapi.Response(description="Invalid or expired activation key."),
            404: openapi.Response(description="Workspace not found.")
        }
    )
    def create(self, request):
        workspace_id = request.data.get("workspace_id")
        activation_key = request.data.get("activation_key")

        webhook_url = "https://chat.googleapis.com/v1/spaces/AAQA_GVsRBw/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=H3N0Z8RohdpZtvPYcMgCGE3Z2CmauEoLXHFsTD3q_l0"

        if not workspace_id or not activation_key:
            return Response({
                "message": "Both 'workspace_id' and 'activation_key' are required."
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            workspace = Workspace.objects.get(id=workspace_id)
        except Workspace.DoesNotExist:
            return Response({
                "message": "Workspace not found."
            }, status=status.HTTP_404_NOT_FOUND)

        if workspace.is_activated:
            return Response({
                "message": "Workspace is already activated."
            }, status=status.HTTP_400_BAD_REQUEST)

        # ❌ Incorrect activation key
        if workspace.activation_key != activation_key:
            workspace.failed_activation_attempts += 1
            workspace.save()

            if workspace.failed_activation_attempts >= 3 and workspace.created_by:
                workspace.created_by.is_authorized = False
                workspace.created_by.save()

                # 🔔 Webhook: 3 failed attempts, deauthorize user
                assistant_name = f"{workspace.field_assistant.first_name} {workspace.field_assistant.last_name}".strip() if workspace.field_assistant else "N/A"
                creator_name = f"{workspace.created_by.first_name} {workspace.created_by.last_name}".strip() if workspace.created_by else "N/A"
                msg_payload = {
                    "text": f"""🚫 *Workspace Activation Failed*
                    📛 Workspace Name: {workspace.name}
                    👤 Created By: {creator_name}
                    🔑 Wrong Activation Key Used 3 Times
                    🚷 User has been *de-authorized*
                    🧑‍🌾 Field Assistant: {assistant_name}"""
                }

                try:
                    requests.post(webhook_url, json=msg_payload)
                except Exception as e:
                    print(f"[Webhook Error - Deauth]: {e}")

                return Response({
                    "message": "Failed to activate the workspace contact admin for login.",
                    "status": "N5000"
                }, status=status.HTTP_400_BAD_REQUEST)

            # < 3 failed attempts, generic failure
            return Response({
                "message": "Invalid activation key. Please try again.","status":status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)

        # ⏱️ Expiry Check
        if not workspace.activation_key_expiry or workspace.activation_key_expiry < now():
            return Response({
                "message": "The activation key has expired. Please contact admin to request a new key to continue."
            }, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Success
        workspace.is_activated = True
        workspace.failed_activation_attempts = 0
        workspace.save()

        assistant_name = f"{workspace.field_assistant.first_name} {workspace.field_assistant.last_name}".strip() if workspace.field_assistant else "N/A"
        activation_time = localtime(now()).strftime("%Y-%m-%d %H:%M:%S")

        # 🔔 Webhook: Successful Activation
        msg_payload = {
            "text": f"""✅ *Workspace Successfully Activated*
            📛 Workspace Name: {workspace.name}
            🧑‍🌾 Field Assistant: {assistant_name}
            ⏰ Activated At: {activation_time}"""
        }

        try:
            requests.post(webhook_url, json=msg_payload)
        except Exception as e:
            print(f"[Webhook Error - Activation]: {e}")

        return Response({
            "message": "Workspace successfully activated.",
            "workspace_id": workspace.id,
            "activated_at": activation_time
        }, status=status.HTTP_200_OK)
    
        
        
from django.db import transaction
from PIL import Image, UnidentifiedImageError
from rest_framework import viewsets, status, parsers
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import os

class ImageUploadViewSet(viewsets.ViewSet):
    """
    Upload up to 300 training images with automatic validation.
    Skips corrupt/unreadable images to protect training pipeline.
    """
    parser_classes = [parsers.MultiPartParser]
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_CONTENT_TYPES = [
        'image/jpeg',
        'image/png',
        'image/gif',
        'image/webp',
    ]

    @swagger_auto_schema(
        operation_summary="Upload training images",
        operation_description="Uploads up to 300 images. Corrupted or unreadable images will be skipped.",
        manual_parameters=[
            openapi.Parameter(
                name='images',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=True,
                description='Multiple images may be sent using the same field name'
            )
        ],
        responses={
            201: openapi.Response(
                description='Upload results',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'valid_images': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'invalid_images': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'skipped_files': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'filename': openapi.Schema(type=openapi.TYPE_STRING),
                                    'reason': openapi.Schema(type=openapi.TYPE_STRING)
                                }
                            )
                        ),
                        'warnings': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: openapi.Response(
                description='Bad request',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            )
        }
    )
    @transaction.atomic
    def create(self, request):
        files = request.FILES.getlist("images")

        if not files:
            return Response(
                {"message": "No images provided."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(files) > 300:
            return Response(
                {"message": "You can upload a maximum of 300 images."},
                status=status.HTTP_400_BAD_REQUEST
            )

        valid_count = 0
        invalid_count = 0
        failed_files = []
        valid_images = []

        for file in files:
            try:
                # Validate file size
                if file.size > self.MAX_FILE_SIZE:
                    raise ValueError(f"File size exceeds {self.MAX_FILE_SIZE/1024/1024}MB limit")

                # Validate content type
                if file.content_type not in self.ALLOWED_CONTENT_TYPES:
                    raise ValueError(f"Unsupported content type: {file.content_type}")

                # Validate image integrity
                img = Image.open(file)
                img.verify()
                
                # Rewind the file pointer after verification
                if hasattr(file, 'seekable') and file.seekable():
                    file.seek(0)
                
                valid_images.append(file)
                valid_count += 1
                
            except (UnidentifiedImageError, IOError, ValueError) as e:
                invalid_count += 1
                failed_files.append({
                    'filename': file.name,
                    'reason': str(e) if str(e) else "Invalid image file"
                })
                continue

        if valid_images:
            training_images = [
                TrainingImage(image=file) 
                for file in valid_images
            ]
            TrainingImage.objects.bulk_create(training_images)

        response_data = {
            "message": "Upload complete.",
            "valid_images": valid_count,
            "invalid_images": invalid_count,
            "skipped_files": failed_files
        }

        if any(f.size > 5*1024*1024 for f in valid_images):
            response_data["warnings"] = "Large files detected - processing may take longer"

        return Response(response_data, status=status.HTTP_201_CREATED)
    
    


class FielEngineerVerification(viewsets.ViewSet):

    @swagger_auto_schema(
        operation_description="Verify if the given phone number belongs to the field engineer assigned to the workspace.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['workspace_id', 'phone_number'],
            properties={
                'workspace_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the workspace'),
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='Phone number of the field engineer'),
            },
        ),
        responses={
            200: openapi.Response(
                description="Verification Result",
                examples={
                    "application/json": {
                        "status": True,
                        "message": "Field assistant is correctly assigned."
                    }
                }
            ),
            400: "Invalid input or data not found"
        }
    )
    def create(self, request):
        workspace_id = request.data.get("workspace_id")
        phone_number = request.data.get("phone_number")

        if not workspace_id or not phone_number:
            return Response(
                {"status": False, "message": "workspace_id and phone_number are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            workspace = Workspace.objects.get(id=workspace_id)
        except Workspace.DoesNotExist:
            return Response(
                {"status": False, "message": "Workspace not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        if not workspace.field_assistant:
            return Response(
                {"status": False, "message": "No field assistant assigned to this workspace."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if workspace.field_assistant.phone_number == phone_number:
            return Response({"status": True, "message": "Field assistant is correctly assigned."})
        else:
            return Response({"status": False, "message": "Incorrect field assistant."}, status=status.HTTP_400_BAD_REQUEST)
