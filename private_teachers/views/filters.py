# -*- coding: utf-8 -*-
from dideman.dide.views.filters import render_template

def privateteacher(request):
    from dideman.private_teachers.admin import PrivateTeacherAdmin
    from dideman.private_teachers.models import PrivateTeacher
    return render_template(request, PrivateTeacher, PrivateTeacherAdmin)
