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

#TODO TEST beggining + create model for it and uuid for test with result + improve serializer to show ur last tries

#NOT WORK YET
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


    def retrieve(self, request, *args, **kwargs):
        course_pk = self.kwargs.get('course_pk')
        section_pk = self.kwargs.get('section_pk')
        block_pk = self.kwargs.get('block_pk')
        pk = self.kwargs.get('pk')

        block, test = self.get_block_and_test(course_pk,section_pk,block_pk)
        test_questions = get_object_or_404(TestQuestions, pk=pk, test_block=test)
        serializer = RawTestSerializer(test_questions)
        return Response(serializer.data,status=status.HTTP_200_OK)


    def create(self,request ,*args, **kwargs):
        course_pk = self.kwargs.get('course_pk')
        section_pk = self.kwargs.get('section_pk')
        block_pk = self.kwargs.get('block_pk')

        course = get_object_or_404(Course,pk=course_pk)
        section = get_object_or_404(CourseSections, pk=section_pk, course=course)

        if not CoLecturerOrAbove().has_object_permission(request,self,course):
            raise PermissionDenied("You're not allowed to do this ")

        else:
            block = get_object_or_404(SectionContent, pk=block_pk, section=section)
            test = get_object_or_404(TestBlock, section=block)
            serializer = TestCreateUpdateSerializer(data=request.data,context={'test': test})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            output_serializer = RawTestSerializer(serializer.instance)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)


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

    def destroy(self, request, *args, **kwargs):
        course_pk = self.kwargs.get('course_pk')
        section_pk = self.kwargs.get('section_pk')
        block_pk = self.kwargs.get('block_pk')
        pk = self.kwargs.get('pk')

        block, test = self.get_block_and_test(course_pk, section_pk, block_pk)
        question = get_object_or_404(TestQuestions, pk=pk, test_block=test)
        question.delete()
        output_serializer = AdminSectionContentMultiSerializer(block)
        return Response(output_serializer.data, status=status.HTTP_204_NO_CONTENT)



#DO i need 1more viewset???
#TODO delete later
class TestQuestionsView(APIView):
    permission_classes = (IsAuthenticated, CoLecturerOrAbove)
    authentication_classes = (JWTAuthentication,)

    def get_block(self,course_pk,section_pk,block_pk,):
        course = get_object_or_404(Course, pk=course_pk)
        section = get_object_or_404(CourseSections, pk=section_pk, course=course)
        block = get_object_or_404(SectionContent, pk=block_pk, section=section, content_type='test')
        test_block = get_object_or_404(TestBlock, section=block)
        return course, test_block

    def post(self, request, course_pk, section_pk, block_pk):
        course, test_block = self.get_block(course_pk, section_pk, block_pk)
        check_object_permissions(self, request, course)

        serializer = TestCreateUpdateSerializer(data=request.data, context={'test_block': test_block})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def patch(self, request, course_pk, section_pk, block_pk, pk):
        course, test_block = self.get_block(course_pk, section_pk, block_pk)
        question = get_object_or_404(TestQuestions, pk=pk, test_block=test_block)
        serializer = TestCreateUpdateSerializer(instance=question, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        output_serializer = RawTestSerializer(test_block)
        return Response(output_serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, course_pk, section_pk, block_pk, pk):
        course, test_block = self.get_block(course_pk, section_pk, block_pk)
        question = get_object_or_404(TestQuestions, pk=pk, test_block=test_block)
        question.delete()
        output_serializer = RawTestSerializer(test_block)
        return Response(output_serializer.data, status=status.HTTP_204_NO_CONTENT)