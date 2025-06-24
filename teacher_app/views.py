from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from courses_app.models import CourseSections, Course, TestQuestions, TestBlock, SectionContent
from courses_app.serializers import SectionContentCreateUpdateSerializer, SectionContentSerializer
from courses_app.utils import check_object_permissions
from main.permissions import CoLecturerOrAbove
from teacher_app.serializers import TestCreateUpdateSerializer, RawTestSerializer


# Create your views here.
#TODO student kick/promote(in course)/sections + sections_content create

class SectionBlockTestAnswers(APIView):
    permission_classes = (IsAuthenticated, CoLecturerOrAbove)
    authentication_classes = (JWTAuthentication,)

    #TODO answers patch
    def patch(self, request, course_pk, section_pk, block_pk):
        course = Course.objects.get(pk=course_pk)
        block = get_object_or_404(CourseSections, pk=block_pk, section_pk=section_pk, course=course)

class SectionBlockCreate(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, CoLecturerOrAbove]

    def post(self, request, course_pk, section_pk, *args, **kwargs):
        course = get_object_or_404(Course, pk=course_pk)
        section = get_object_or_404(CourseSections, pk=section_pk, course=course)

        check_object_permissions(self, request, course)

        serializer = SectionContentCreateUpdateSerializer(data=request.data,
                                                            context={'course': course, 'section': section})
        serializer.is_valid(raise_exception=True)
        new_block = serializer.save()
        output = SectionContentSerializer(new_block)
        return Response(output.data, status=status.HTTP_201_CREATED)
#NOT WORK YET
class TestViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, CoLecturerOrAbove)
    authentication_classes = (JWTAuthentication,)

    def get_course_and_section(self, course_pk, section_pk):
        course = get_object_or_404(Course,pk=course_pk)
        section = get_object_or_404(CourseSections,pk=section_pk,course=course)
        return course,section

    @action(detail=True, methods=['get'],url_name='questions')
    def get_qeustions(self, request,section_pk, pk, *args, **kwargs):
        course, section = self.get_course_and_section(course_pk=pk, section_pk=section_pk)
        check_object_permissions(self, request, course)
        test = get_object_or_404(TestBlock, section=section, pk=pk)
        serializer = RawTestSerializer(test)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'],url_path='questions')
    def add_question(self,request,course_pk,section_pk, *args, **kwargs):
        course, section = self.get_course_and_section(course_pk, section_pk)
        check_object_permissions(self, request, course)

        try:
            test = get_object_or_404(TestBlock, section=section)
        except TestBlock.DoesNotExist:
            raise ValidationError('Test block not found')

        serializer = TestCreateUpdateSerializer(data=request.data,context={'test': test})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        output_serializer = RawTestSerializer(serializer.instance)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['patch'],url_path='questions')
    def question_update(self,request,course_pk,section_pk, pk, *args, **kwargs):
        course, section = self.get_course_and_section(course_pk, section_pk)
        check_object_permissions(self, request, course)

        try:
            test = get_object_or_404(TestBlock, section=section)
        except TestBlock.DoesNotExist:
            raise ValidationError('Test block not found')
        question = get_object_or_404(TestQuestions, test_block=test, pk=pk)

        serializer = TestCreateUpdateSerializer(instance=question,data=request.data, partial=True,)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        output_serializer = RawTestSerializer(serializer.instance)
        return Response(output_serializer.data, status=status.HTTP_200_OK)



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