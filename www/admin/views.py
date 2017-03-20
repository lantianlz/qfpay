# -*- coding: utf-8 -*-

import urllib
import re
import json
from django.contrib import auth
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.shortcuts import render_to_response

from misc.decorators import staff_required, common_ajax_response, verify_permission, member_required

# @verify_permission('')
@member_required
def home(request):
    return HttpResponseRedirect('/admin/shop')
