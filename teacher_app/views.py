from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from courses_app.models import CourseSections, Course, TestQuestions, TestBlock, SectionContent
from courses_app.serializers import SectionContentCreateUpdateSerializer, SectionContentSerializer, \
    AdminSectionContentMultiSerializer
from courses_app.utils import check_object_permissions
from main.permissions import CoLecturerOrAbove, StudentOrAbove
from teacher_app.serializers import TestCreateUpdateSerializer, RawTestSerializer


# Create your views here.

#TESTED
class TestViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, StudentOrAbove)
    authentication_classes = (JWTAuthentication,)

    def get_block_and_test(self, course_pk, section_pk, block_pk):
        course = get_object_or_404(Course,pk=course_pk)
        section = get_object_or_404(CourseSections,pk=section_pk,course=course)
        block = get_object_or_404(SectionContent, pk=block_pk, section=section)
        test = get_object_or_404(TestBlock, section=block)
        return block, test

    @extend_schema(summary="get test question",
                   parameters=[
        OpenApiParameter(name='course_pk', location=OpenApiParameter.PATH, required=True, type=OpenApiTypes.INT),
        OpenApiParameter(name='section_pk', location=OpenApiParameter.PATH, required=True, type=OpenApiTypes.INT),
        OpenApiParameter(name='block_pk', location=OpenApiParameter.PATH, required=True, type=OpenApiTypes.INT),
        OpenApiParameter(name='pk', description="test_pk", location=OpenApiParameter.PATH, required=True, type=OpenApiTypes.INT)],
                    responses={200: RawTestSerializer,
                               404: OpenApiResponse(description="Block/Section/Test question not found"),
                               403: OpenApiResponse(description="Permission Denied"),
                               },
    )
    def retrieve(self, request, *args, **kwargs):
        course_pk = self.kwargs.get('course_pk')
        section_pk = self.kwargs.get('section_pk')
        block_pk = self.kwargs.get('block_pk')
        pk = self.kwargs.get('pk')

        block, test = self.get_block_and_test(course_pk,section_pk,block_pk)
        test_questions = get_object_or_404(TestQuestions, pk=pk, test_block=test)
        serializer = RawTestSerializer(test_questions)
        return Response(serializer.data,status=status.HTTP_200_OK)


    @extend_schema(summary="create test question",
                   parameters=[
                       OpenApiParameter(name='course_pk', location=OpenApiParameter.PATH, required=True, type=OpenApiTypes.INT),
                       OpenApiParameter(name='section_pk', location=OpenApiParameter.PATH, required=True, type=OpenApiTypes.INT),
                       OpenApiParameter(name='block_pk', location=OpenApiParameter.PATH, required=True, type=OpenApiTypes.INT)],
                   request = TestCreateUpdateSerializer,
                   responses = {201: RawTestSerializer,
                                404: OpenApiResponse(description="Block/Section question not found") ,
                                403: OpenApiResponse(description="Permission Denied") },
                   )
    def create(self,request ,*args, **kwargs):
        course_pk = self.kwargs.get('course_pk')
        section_pk = self.kwargs.get('section_pk')
        block_pk = self.kwargs.get('block_pk')

        course = get_object_or_404(Course, pk=course_pk)
        section = get_object_or_404(CourseSections, pk=section_pk, course=course)

        if not CoLecturerOrAbove().has_object_permission(request, self,course):
            raise PermissionDenied("You're not allowed to do this ")

        else:
            block = get_object_or_404(SectionContent, pk=block_pk, section=section)
            test = get_object_or_404(TestBlock, section=block)
            serializer = TestCreateUpdateSerializer(data=request.data,context={'test': test})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            output_serializer = RawTestSerializer(serializer.instance)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)


    @extend_schema(summary="update test question",
                   parameters=[
                    OpenApiParameter(name='course_pk', location=OpenApiParameter.PATH, required=True, type=OpenApiTypes.INT),
                    OpenApiParameter(name='section_pk', location=OpenApiParameter.PATH, required=True, type=OpenApiTypes.INT),
                    OpenApiParameter(name='block_pk', location=OpenApiParameter.PATH, required=True, type=OpenApiTypes.INT),
                    OpenApiParameter(name='pk', description="test_pk", location=OpenApiParameter.PATH, required=True, type=OpenApiTypes.INT)],
                   request=TestCreateUpdateSerializer,
                   responses = {200: RawTestSerializer,
                                404: OpenApiResponse(description="Block/Section/Test question not found"),
                                403: OpenApiResponse(description="Permission Denied")}
                   )
    def partial_update(self,request, *args, **kwargs):
        course_pk = self.kwargs.get('course_pk')
        section_pk = self.kwargs.get('section_pk')
        block_pk = self.kwargs.get('block_pk')
        pk = self.kwargs.get('pk')
        course = get_object_or_404(Course, pk=course_pk)
        block, test = self.get_block_and_test(course_pk, section_pk, block_pk)
        check_object_permissions(self, request, course)


        questions = get_object_or_404(TestQuestions, pk=pk, test_block=test)
        serializer = TestCreateUpdateSerializer(instance=questions, data=request.data, partial=True,)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        output_serializer = RawTestSerializer(serializer.instance)
        return Response(output_serializer.data, status=status.HTTP_200_OK)


    @extend_schema(summary="test question delete",
                   parameters=[
                       OpenApiParameter(name='course_pk', location=OpenApiParameter.PATH, required=True, type=OpenApiTypes.INT),
                       OpenApiParameter(name='section_pk', location=OpenApiParameter.PATH, required=True, type=OpenApiTypes.INT),
                       OpenApiParameter(name='block_pk', location=OpenApiParameter.PATH, required=True, type=OpenApiTypes.INT),
                       OpenApiParameter(name='pk', description="test_pk", location=OpenApiParameter.PATH, required=True, type=OpenApiTypes.INT)],
                   responses={202: AdminSectionContentMultiSerializer,
                              404: OpenApiResponse(description="Block/Section/Test question not found"),
                              403: OpenApiResponse(description="Permission Denied")
                              }
                   )
    def destroy(self, request, *args, **kwargs):
        course_pk = self.kwargs.get('course_pk')
        section_pk = self.kwargs.get('section_pk')
        block_pk = self.kwargs.get('block_pk')
        pk = self.kwargs.get('pk')

        block, test = self.get_block_and_test(course_pk, section_pk, block_pk)
        question = get_object_or_404(TestQuestions, pk=pk, test_block=test)
        question.delete()
        output_serializer = AdminSectionContentMultiSerializer(block)
        return Response(output_serializer.data, status=status.HTTP_202_ACCEPTED)


