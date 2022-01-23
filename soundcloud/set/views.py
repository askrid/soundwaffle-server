from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from set.models import Set, SetTrack
from set.serializers import *
from soundcloud.utils import CustomObjectPermissions
from track.models import Track
from user.models import User


@extend_schema_view( 
    list=extend_schema(
        summary="List of Sets",
        responses={
            200: OpenApiResponse(response=SimpleSetSerializer, description='OK'),
            404: OpenApiResponse(description='Not Found'),
        }
    ),
    create=extend_schema(
        summary="Create Set",
        responses={
            201: OpenApiResponse(response=SetSerializer, description='Created'),
            400: OpenApiResponse(description='Bad Request'),
            401: OpenApiResponse(description='Unauthorized'),
        }
    ),
    update=extend_schema(
        summary="Update Set",
        responses={
            '200': OpenApiResponse(response=SetMediaUploadSerializer, description='OK'),
            '400': OpenApiResponse(description='Bad Request'),
            '401': OpenApiResponse(description='Unauthorized'),
            '403': OpenApiResponse(description='Permission Denied'),
            '404': OpenApiResponse(description='Not Found'),
        }
    ),
    partial_update=extend_schema(
        summary="Partial Update Set",
        responses={
            '200': OpenApiResponse(response=SetMediaUploadSerializer, description='OK'),
            '400': OpenApiResponse(description='Bad Request'),
            '401': OpenApiResponse(description='Unauthorized'),
            '403': OpenApiResponse(description='Permission Denied'),
            '404': OpenApiResponse(description='Not Found'),
        }
    ),
    retrieve=extend_schema(
        summary="Retrieve Set",
        responses={
            '200': OpenApiResponse(response=SetSerializer, description='OK'),
            '404': OpenApiResponse(description='Not Found')
        }
    ),
    destroy=extend_schema(
        summary="Delete Set",
        responses={
            '204': OpenApiResponse(description='No Content'),
            '401': OpenApiResponse(description='Unauthorized'),
            '403': OpenApiResponse(description='Permission Denied'),
            '404': OpenApiResponse(description='Not Found'),
        }
    ),
    likers=extend_schema(
        summary="Get Set's Likers",
        parameters=[
            OpenApiParameter("page", OpenApiTypes.INT, OpenApiParameter.QUERY, description='A page number within the paginated result set.'),
            OpenApiParameter("page_size", OpenApiTypes.INT, OpenApiParameter.QUERY, description='Number of results to return per page.'),
        ],
        responses={
            '200': OpenApiResponse(response=SimpleUserSerializer(many=True), description='OK'),
            '404': OpenApiResponse(description='Not Found'),
        }
    ),
    reposters=extend_schema(
        summary="Get Set's Reposters",
        parameters=[
            OpenApiParameter("page", OpenApiTypes.INT, OpenApiParameter.QUERY, description='A page number within the paginated result set.'),
            OpenApiParameter("page_size", OpenApiTypes.INT, OpenApiParameter.QUERY, description='Number of results to return per page.'),
        ],
        responses={
            '200': OpenApiResponse(response=SimpleUserSerializer(many=True), description='OK'),
            '404': OpenApiResponse(description='Not Found'),
        }
    )

)
class SetViewSet(viewsets.ModelViewSet):
    permission_classes = (CustomObjectPermissions, )
    filter_backends = (OrderingFilter, )
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    lookup_url_kwarg = 'set_id'

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return SetMediaUploadSerializer
        if self.action in ['list']:
            return SimpleSetSerializer
        if self.action in ['likers', 'reposters']:
            return SimpleUserSerializer
        else:
            return SetSerializer

    def get_queryset(self):
        if self.action in ['likers', 'reposters']:
            self.set = getattr(self, 'set', None) or get_object_or_404(Set, id=self.kwargs[self.lookup_url_kwarg])
            if self.action == 'likers':
                return User.objects.prefetch_related('followers', 'owned_sets').filter(likes__set=self.set)
            if self.action == 'reposters':
                return User.objects.prefetch_related('followers', 'owned_sets').filter(reposts__set=self.set)
        else:
            return Set.objects.all().prefetch_related('tracks__artist')
    
    # 1. POST /sets/ - 빈 playlist 생성 - mixin 이용
    # 2. PUT /sets/{set_id} - mixin 이용
    # 3. GET /sets/{set_id} - mixin 이용
    # 4. DELETE /sets/{set_id} - mixin 이용

    # 5. GET /sets/{set_id}/likers
    @action(detail=True)
    def likers(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    # 6. GET /sets/{set_id}/reposters
    @action(detail=True)
    def reposters(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


@extend_schema_view( 
    tracks=extend_schema(
        summary="Add/Remove Track in Set",
        responses={
            '200': OpenApiResponse(description='OK'),
            '400': OpenApiResponse(description="Bad Request"),
            '401': OpenApiResponse(description='Unauthorized'),
            '403': OpenApiResponse(description='Permission Denied'),
            '404': OpenApiResponse(description='Not Found'),
        }
    )
)
class SetTrackViewSet(viewsets.GenericViewSet): 
    permission_classes = (CustomObjectPermissions, )
    lookup_url_kwarg = 'set_id'
    serializer_class = SetTrackService
    queryset = Set.objects.all()
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['set'] = self.get_object()
        track_id=self.request.data.get('track_id')
        if track_id is None:
            context['track'] = None
            return context
        context['track'] = get_object_or_404(Track, id=track_id)
        return context
    
    # 7. POST /sets/{set_id}/tracks (add track to playlist)
    # 8. DELETE /sets/{set_id}/tracks (remove track from playlist)
    @action(methods=['POST', 'DELETE'], detail=True)
    def tracks(self, request, *args, **kwargs):
        service = self.get_serializer()
        if request.method == 'POST':
            return self._add(service)
        else:
            return self._remove(service)

    def _add(self, service):
        status, data = service.create()
        return Response(status=status, data=data)

    def _remove(self, service):
        status, data = service.delete()
        return Response(status=status, data=data)
