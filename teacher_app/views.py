from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from courses_app.models import CourseSections, Course, TestQuestions
from courses_app.serializers import SectionContentCreateUpdateSerializer, SectionContentSerializer
from courses_app.utils import check_object_permissions
from main.permissions import CoLecturerOrAbove
from teacher_app.serializers import TestCreateUpdateSerializer, RawTestSerializer


# Create your views here.
#TODO student kick/promote(in course)/sections + sections_content create

#TODO add-test / add-lecture
#TODO TEST
class SectionBlockTestCreate(APIView):
    permission_classes = (IsAuthenticated, CoLecturerOrAbove)
    authentication_classes = (JWTAuthentication,)

    def post(self, request, course_pk, section_pk):
        course = Course.objects.get(pk=course_pk)
        section = get_object_or_404(CourseSections, pk=section_pk, course=course)

        check_object_permissions(self, request, course)

        serializer = TestCreateUpdateSerializer(data=request.data, context={'request': request,'section': section})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        output_serializer = RawTestSerializer(serializer.instance)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

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
    #TODO Patch for test(order + field)