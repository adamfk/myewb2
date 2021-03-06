"""myEWB CHAMP views

This file is part of myEWB
Copyright 2010 Engineers Without Borders Canada

@author Francis Kung

Ideally, I'd like to split out the different metric types and make them pluggable:
define a different template segment for each, then build a list and include/parse dynamically
(instead of having them fixed in run_stats() here)....
"""

import csv
from datetime import date

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render_to_response
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseNotFound, HttpResponseRedirect, HttpResponse, HttpResponseForbidden
from django.db.models import Q
from django.template import RequestContext

from base_groups.decorators import group_admin_required
from networks.decorators import chapter_president_required
from networks.models import Network
from champ.models import *
from champ.forms import *
from siteutils import schoolyear
from siteutils.helpers import fix_encoding

def run_query(query, filters):
    for f in filters:
        query = query.filter(**f)
    return query

def run_stats(filters):
    # FIXME: these all need to be rewritten with aggregate functions when we go to django 1.1 !!!!!
    ml_metrics = run_query(MemberLearningMetrics.objects.all(), filters)
    ml_hours = 0
    ml_attendance = 0
    ml_num = ml_metrics.count()
    for m in ml_metrics:
        ml_hours += m.duration * m.attendance
        ml_attendance += m.attendance
    if ml_num:
        ml_attendance = ml_attendance / ml_num
        
    pe_metrics = run_query(PublicEngagementMetrics.objects.all(), filters)
    pe_people = 0
    for p in pe_metrics:
        pe_people += p.level1 + p.level2 + p.level3
    
    po_metrics = run_query(PublicAdvocacyMetrics.objects.all(), filters)
    po_contacts = 0
    for p in po_metrics:
        po_contacts += p.units
    
    ce_metrics = run_query(CurriculumEnhancementMetrics.objects.all(), filters)
    ce_students = 0
    ce_hours = 0
    for c in ce_metrics:
        ce_students += c.students
        ce_hours += c.hours
    
    wo_metrics = run_query(WorkplaceOutreachMetrics.objects.all(), filters)
    wo_professionals = 0
    wo_presentations = 0
    for w in wo_metrics:
        wo_professionals += w.attendance 
        wo_presentations += w.presentations
    
    so_metrics = run_query(SchoolOutreachMetrics.objects.all(), filters)
    so_students = 0
    so_presentations = 0
    for s in so_metrics:
        so_students += s.students
        so_presentations += s.presentations
    
    fundraising_metrics = run_query(FundraisingMetrics.objects.all(), filters)
    fundraising_dollars = 0
    for f in fundraising_metrics:
        fundraising_dollars += f.revenue
    
    publicity_metrics = run_query(PublicationMetrics.objects.all(), filters)
    publicity_hits = publicity_metrics.count()
    
    context = {}
    context['ml_hours'] = ml_hours
    context['ml_attendance'] = ml_attendance
    context['pe_people'] = pe_people
    context['po_contacts'] = po_contacts
    context['ce_students'] = ce_students
    context['ce_hours'] = ce_hours
    context['wo_professionals'] = wo_professionals
    context['wo_presentations'] = wo_presentations
    context['so_students'] = so_students
    context['so_presentations'] = so_presentations
    context['fundraising_dollars'] = fundraising_dollars
    context['publicity_hits'] = publicity_hits
    
    return context

def build_filters(year=None, month=None, term=None):
    activity_filters = []
    metric_filters = []
    
    if year:
        year = int(year)
    if month:
        month = int(month)
    if year and month:
        activity_filters.append({'date__year': year})
        activity_filters.append({'date__month': month})
        metric_filters.append({'activity__date__year': year})
        metric_filters.append({'activity__date__month': month})
    elif year and term:
        if term == 'winter':
            start = date(year, 1, 1)
            end = date(year, 4, 30)
            activity_filters.append({'date__range': (start, end)})
            metric_filters.append({'activity__date__range': (start, end)})
        elif term == 'summer':
            start = date(year, 5, 1)
            end = date(year, 8, 31)
            activity_filters.append({'date__range': (start, end)})
            metric_filters.append({'activity__date__range': (start, end)})
        elif term == 'fall':
            start = date(year, 9, 1)
            end = date(year, 12, 31)
            activity_filters.append({'date__range': (start, end)})
            metric_filters.append({'activity__date__range': (start, end)})
    elif year:
        start = date(year, 5, 1)
        end = date(year+1, 4, 30)
        activity_filters.append({'date__range': (start, end)})
        metric_filters.append({'activity__date__range': (start, end)})
            
    return activity_filters, metric_filters
    
@login_required()
def dashboard(request, year=None, month=None, term=None,
              group_slug=None):

    activity_filters, metric_filters = build_filters(year, month, term)
    
    if group_slug:
        activity_filters.append({'group__slug': group_slug})
        metric_filters.append({'activity__group__slug': group_slug})
        journals = run_query(Journal.objects.all(), activity_filters).count()
        
        grp = get_object_or_404(Network, slug=group_slug)
    else:
        journals = 0
        grp = None

    activity_filters.append({'visible': True})
    metric_filters.append({'activity__visible': True})
    metric_filters.append({'activity__confirmed': True})
    context = run_stats(metric_filters)

    context['unconfirmed'] = run_query(Activity.objects.filter(confirmed=False), activity_filters).count()
    context['confirmed'] = run_query(Activity.objects.filter(confirmed=True), activity_filters).count()
    context['journals'] = journals
    
    context['group'] = None
    context['yearplan'] = None    
    context['is_group_admin'] = False
    if grp:
        context['group'] = grp
    
        context['is_group_admin'] = grp.user_is_admin(request.user)
        context['is_president'] = grp.user_is_president(request.user)
            
        if year:
            yp = YearPlan.objects.filter(group=grp, year=year)
        else:
            yp = YearPlan.objects.filter(group=grp, year=date.today().year)
        if yp.count():
            context['yearplan'] = yp[0]
            
    context['year'] = year
    context['month'] = month
    context['term'] = term
    
    context['nowyear'] = schoolyear.school_year()
    if year:
        context['prevyear'] = int(year) - 1
        context['nextyear'] = int(year) + 1
    
    context['nowmonth'] = ("%d" % date.today().month).rjust(2, '0')
    if month:
        if month == "01":
            context['prevmonth'] = (12, int(year)-1)
        else:
            context['prevmonth'] = (("%d" % (int(month)-1)).rjust(2, '0'), year)
        if month == "12":
            context['nextmonth'] = ("01", int(year)+1)
        else:
            context['nextmonth'] = (("%d" % (int(month)+1)).rjust(2, '0'), year)

    context['nowterm'] = schoolyear.term()
    if term:
        context['prevterm'] = schoolyear.prevterm(term, year)
        context['nextterm'] = schoolyear.nextterm(term, year)
    
    context['allgroups'] = Network.objects.filter(chapter_info__isnull=False, is_active=True).order_by('name')
    
    return render_to_response('champ/dashboard.html',
                              context,
                              context_instance=RequestContext(request))

@group_admin_required()
def new_activity(request, group_slug):
    group = get_object_or_404(Network, slug=group_slug)
    metric_forms = {}
    showfields = {"all": True}
    
    if request.method == 'POST':
        champ_form = ChampForm(request.POST)
        
        # also create forms for the selected metrics
        forms_valid = champ_form.is_valid()
        for m, mname in ALLMETRICS:
            if m in request.POST:
                metric_forms[m] = METRICFORMS[m](request.POST,
                                                 prefix=m)
                forms_valid = forms_valid and metric_forms[m].is_valid()
                showfields[m] = True

        if forms_valid:
            # save the activity
            activity = champ_form.save(commit=False)
            activity.creator = request.user
            activity.editor = request.user
            activity.group = group
            activity.save()
            
            # and save all associated metrics
            for m in metric_forms:
                metric = metric_forms[m].save(commit=False)
                metric.activity=activity
                metric.save()
            
            request.user.message_set.create(message="Activity recorded")
            return HttpResponseRedirect(reverse('champ_dashboard', kwargs={'group_slug': group_slug}))
            
        else:
            # create all the other metric forms as blank forms
            for m, mname in ALLMETRICS:
                if m not in metric_forms:
                    metric_forms[m] = METRICFORMS[m](prefix=m)
                    if not m == "all":
                        showfields[m] = False
                 
    else:
        champ_form = ChampForm()
        for m, mname in ALLMETRICS:
            metric_forms[m] = METRICFORMS[m](prefix=m)
                       
    return render_to_response('champ/new_activity.html',
                              {'group': group,
                               'champ_form': champ_form,
                               'metric_names': ALLMETRICS,
                               'metric_forms': metric_forms,
                               'showfields': showfields,
                               'edit': False,
                               'is_group_admin': True,
                               'is_president': group.user_is_president(request.user)
                               },
                              context_instance=RequestContext(request))
    
@group_admin_required()
def confirmed(request, group_slug):
    group = get_object_or_404(Network, slug=group_slug)
    activities = Activity.objects.filter(confirmed=True,
                                         visible=True,
                                         group__slug=group_slug)
    activites = activities.order_by('-date')
    
    return render_to_response('champ/activity_list.html',
                              {'confirmed': True,
                               'activities': activities,
                               'group': group,
                               'is_group_admin': True,
                               'is_president': group.user_is_president(request.user),
                               },
                               context_instance=RequestContext(request))
    
@group_admin_required()
def unconfirmed(request, group_slug):
    group = get_object_or_404(Network, slug=group_slug)
    activities = Activity.objects.filter(confirmed=False,
                                         visible=True,
                                         group__slug=group_slug)
    activites = activities.order_by('-date')
    
    return render_to_response('champ/activity_list.html',
                              {'confirmed': False,
                               'activities': activities,
                               'group': group,
                               'is_group_admin': True,
                               'is_president': group.user_is_president(request.user)
                               },
                               context_instance=RequestContext(request))
    
@group_admin_required()
def activity_detail(request, group_slug, activity_id):
    group = get_object_or_404(Network, slug=group_slug)
    activity = get_object_or_404(Activity, pk=activity_id)
    
    # do we want this?
    # and why do we need to use pk's? (check always fails otherwise)
    if not activity.group.pk == group.pk:
        return HttpResponseForbidden()
    
    if activity.visible == False:
        request.user.message_set.create(message="That activity has been deleted.")
        return HttpResponseRedirect(redirect('champ_dashboard', kwargs={'group_slug': group.slug}))
    
    return render_to_response('champ/activity_detail.html',
                              {'activity': activity,
                               'group': group,
                               'metric_names': ALLMETRICS,
                               'is_admin': group.user_is_admin(request.user),
                               'is_group_admin': True,
                               'is_president': group.user_is_president(request.user)
                               },
                               context_instance=RequestContext(request))
    
@group_admin_required()
def activity_edit(request, group_slug, activity_id):
    group = get_object_or_404(Network, slug=group_slug)
    activity = get_object_or_404(Activity, pk=activity_id)
    
    if not activity.group.pk == group.pk:
        return HttpResponseForbidden()
    
    if activity.visible == False:
        request.user.message_set.create(message="That activity has been deleted.")
        return HttpResponseRedirect(redirect('champ_dashboard', kwargs={'group_slug': group.slug}))
    
    if activity.confirmed:
        request.user.message_set.create(message="This activity is already confirmed - you can't edit it any more")
        return HttpResponseRedirect(reverse('champ_activity', kwargs={'group_slug': group_slug, 'activity_id': activity_id}))

    metric_forms = {}
    showfields = {"all": True}
    
    if request.method == 'POST':
        champ_form = ChampForm(request.POST, instance=activity)
        
        # also create forms for the selected metrics.
        # initialize all to empty
        forms_valid = champ_form.is_valid()
        # then populate the ones we're using for this activity
        metrics = activity.get_metrics()
        for m in metrics:
            if m.metricname in request.POST:
                metric_forms[m.metricname] = METRICFORMS[m.metricname](request.POST,
                                                                       instance=m,
                                                                       prefix=m.metricname)
                showfields[m.metricname] = True
                forms_valid = forms_valid and metric_forms[m.metricname].is_valid()

        for m, mname in ALLMETRICS:
            if m in request.POST and m not in metric_forms:
                metric_forms[m] = METRICFORMS[m](request.POST,
                                                 prefix=m)
                forms_valid = forms_valid and metric_forms[m].is_valid()
                showfields[m] = True
            elif m not in metric_forms:
                metric_forms[m] = METRICFORMS[m](prefix=m)
                showfields[m] = False
                
        if forms_valid:
            activity = champ_form.save()
            saved_fields = {}
            for m in metrics:
                if m.metricname in request.POST:
                    metric_forms[m.metricname].save()
                    saved_fields[m.metricname] = True
                else:
                    m.delete()
            for m, mname in ALLMETRICS:
                if m in request.POST and m not in saved_fields:
                    metric = metric_forms[m].save(commit=False)
                    metric.activity = activity
                    metric.save()
            
            request.user.message_set.create(message="Activity updated.")
            return HttpResponseRedirect(reverse('champ_activity', kwargs={'group_slug': group_slug, 'activity_id': activity_id}))
        
    else:
        champ_form = ChampForm(instance=activity)
        
        # also create forms for the selected metrics.
        # pre-populate the ones we're using for this activity
        metrics = activity.get_metrics()
        for m in metrics:
            metric_forms[m.metricname] = METRICFORMS[m.metricname](instance=m,
                                                                   prefix=m.metricname)
            showfields[m.metricname] = True
            
        # then create forms for the rest too
        for m, mname in ALLMETRICS:
            if m not in metric_forms:
                metric_forms[m] = METRICFORMS[m](prefix=m)
                if not m == "all":
                    showfields[m] = False

    return render_to_response('champ/new_activity.html',
                              {'group': group,
                               'champ_form': champ_form,
                               'metric_names': ALLMETRICS,
                               'metric_forms': metric_forms,
                               'showfields': showfields,
                               'edit': True,
                               'is_admin': group.user_is_admin(request.user),
                               'is_group_admin': True,
                               'is_president': group.user_is_president(request.user)
                               },
                              context_instance=RequestContext(request))

@group_admin_required()
def activity_confirm(request, group_slug, activity_id):
    group = get_object_or_404(Network, slug=group_slug)
    activity = get_object_or_404(Activity, pk=activity_id)
    
    if not activity.group.pk == group.pk:
        return HttpResponseForbidden()
    
    if activity.visible == False:
        request.user.message_set.create(message="That activity has been deleted.")
        return HttpResponseRedirect(redirect('champ_dashboard', kwargs={'group_slug': group.slug}))
    
    if activity.confirmed:
        request.user.message_set.create(message="This activity is already confirmed")

    elif not activity.can_be_confirmed():
        request.user.message_set.create(message="This activity cannot be confirmed yet")

    else:
        activity.confirmed = True
        activity.save()
        request.user.message_set.create(message="Activity confirmed.  Thanks - you rock!")
        
    return HttpResponseRedirect(reverse('champ_activity', kwargs={'group_slug': group_slug, 'activity_id': activity_id}))

@group_admin_required()
def activity_delete(request, group_slug, activity_id):
    group = get_object_or_404(Network, slug=group_slug)
    activity = get_object_or_404(Activity, pk=activity_id)
    
    if not activity.group.pk == group.pk:
        return HttpResponseForbidden()
    
    if request.method == 'POST':
        activity.editor = request.user
        activity.visible = False
        activity.save()
        
        request.user.message_set.create(message="Activity deleted.")
        return HttpResponseRedirect(reverse('champ_dashboard', kwargs={'group_slug': group.slug}))
        
    else:
        return render_to_response('champ/delete.html',
                                  {'group': group,
                                   'activity': activity,
                                   'is_group_admin': True,
                                   'is_president': group.user_is_president(request.user)},
                                  context_instance=RequestContext(request))

@chapter_president_required()
def journal_list(request, group_slug):
    group = get_object_or_404(Network, slug=group_slug)
    
    journals = Journal.objects.filter(group=group)
    if not request.user.has_module_perms('champ'):
        journals = journals.filter(private=False)
        journals = journals | Journal.objects.filter(group=group, private=True, creator=request.user)
    
    journals = journals.order_by('-date')
    
    return render_to_response('champ/journal_list.html',
                              {'group': group,
                               'journals': journals,
                               'is_group_admin': True,
                               'is_president': True,
                               },
                              context_instance=RequestContext(request))

@chapter_president_required()
def journal_new(request, group_slug):
    group = get_object_or_404(Network, slug=group_slug)
    
    if request.method == 'POST':
        form = JournalForm(request.POST)
        
        if form.is_valid():
            journal = form.save(commit=False)
            journal.creator = request.user
            journal.group = group
            journal.save()
            
            request.user.message_set.create(message="Thank you!")
            return HttpResponseRedirect(reverse('champ_journal_detail', kwargs={'group_slug': group_slug, 'journal_id': journal.pk}))
    
    else:
        form = JournalForm()
        
    return render_to_response('champ/journal_new.html',
                              {'group': group,
                               'form': form,
                               'is_group_admin': True,
                               'is_president': True
                               },
                               context_instance=RequestContext(request))

@chapter_president_required()
def journal_detail(request, group_slug, journal_id):
    group = get_object_or_404(Network, slug=group_slug)
    journal = get_object_or_404(Journal, pk=journal_id)
    
    if not journal.group.pk == group.pk:
        return HttpResponseForbidden()
    
    return render_to_response('champ/journal_detail.html',
                              {'journal': journal,
                               'group': group,
                               'is_group_admin': True,
                               'is_president': True,
                               },
                               context_instance=RequestContext(request))

@group_admin_required()
def yearplan(request, group_slug, year=None):
    group = get_object_or_404(Network, slug=group_slug)
    if year == None:
        year = date.today().year
        
    yp, created = YearPlan.objects.get_or_create(group=group, year=year,
                                                 defaults={'last_editor': request.user})
    
    if request.method == 'POST':
        form = YearPlanForm(request.POST,
                            instance=yp)
        
        if form.is_valid():
            yp = form.save(commit=False)
            yp.last_editor = request.user
            yp.save()
            
            request.user.message_set.create(message="Year plan updated")
            return HttpResponseRedirect(reverse('champ_dashboard', kwargs={'group_slug': group_slug, 'year': year}))
    else:
        form = YearPlanForm(instance=yp)
        
    return render_to_response('champ/yearplan.html',
                              {'group': group,
                               'form': form,
                               'year': year,
                               'is_group_admin': True,
                               'is_president': group.user_is_president(request.user)
                               },
                               context_instance=RequestContext(request))

@group_admin_required()
def csv_so(request, group_slug):
    group = get_object_or_404(Network, slug=group_slug)
    return run_so_csv(group=group)

@group_admin_required()
def csv_all(request, group_slug):
    group = get_object_or_404(Network, slug=group_slug)
    return run_full_csv(group=group)
    
@staff_member_required
def csv_global_so(request):
    return run_so_csv()
    
@staff_member_required
def csv_global_all(request):
    return run_full_csv()
    
def run_so_csv(group=None):
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=champ_schooloutreach_%d-%d-%d.csv' % (date.today().month, date.today().day, date.today().year)
    
    writer = csv.writer(response)
    writer.writerow(['Chapter', 'Activity', 'Date',
                     '# Volunteers', 'Prep Hours', 'Execution Hours',
                     'Created', 'Created By', 'Modified',
                     'Modified By', 'Confirmed?',
                     
                     'School Name', 'Teacher Name', 'Teacher Email',
                     'Teacher Phone', 'Num Presentations', 'Num Students',
                     'Grades', 'Class', 'Workshop', 'Num Facilitators', 'Num New Facilitators'])
    
    metrics = SchoolOutreachMetrics.objects.filter(activity__visible=True)
    if group:
        metrics = metrics.filter(activity__group=group)
        
    for m in metrics:
        row = [m.activity.group.name, m.activity.name, m.activity.date,
               m.activity.numVolunteers, m.activity.prepHours, m.activity.execHours,
               m.activity.created_date, m.activity.creator.visible_name(),
               m.activity.modified_date, m.activity.editor.visible_name()]
        if m.activity.confirmed:
            row.append('confirmed')
        else:
            row.append('unconfirmed')
            
        row.extend([m.school_name, m.teacher_name, m.teacher_email, m.teacher_phone, m.presentations, m.students, m.grades, m.subject, m.workshop, m.facilitators, m.new_facilitators])
            
        writer.writerow([fix_encoding(s) for s in row])

    return response
                     
    
def run_full_csv(group=None):
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=champ_activities_%d-%d-%d.csv' % (date.today().month, date.today().day, date.today().year)
    
    writer = csv.writer(response)
    writer.writerow(['Chapter', 'Activity', 'Description', 'Full Date', 'Month',
                     'Planning Year', '# Volunteers', 'Prep Hours', 'Execution Hours',
                     'Goals', 'Outcomes', 'Created', 'Created By', 'Modified',
                     'Modified By', 'Confirmed?', '# Purposes', 'Purpose(s)',
                     
                     'ML?', 'SO?', 'Functioning?', 'Engagement?', 'Advocacy?',
                     'Publicity?', 'Fundraising?', 'WO?', 'CE?',
                      
                     'ML - Type', 'ML - LP Related', 'ML - Curriculum', 
                     'ML - Resources By', 'ML - Duration', 'ML - Attendence',
                     'ML - New Attendence',
                     
                     'SO - School Name', 'SO - Teacher Name', 'SO - Teacher Email',
                     'SO - Teacher Phone', 'SO- Num Presentations', 'SO - Num Students',
                     'SO - Grades', 'SO - Class', 'SO - Workshop',
                     'SO - Num Facilitators', 'SO - Num New Facilitators',
                     
                     'Functioning - Type', 'Functioning - Location', 'Functioning - Purpose',
                     'Functioning - Attendence', 'Functioning - Duration',
                     
                     'Engagement - Type', 'Engagement - Location', 'Engagement - Purpose',
                     'Engagement - Subject', 'Engagement - Level1', 'Engagement - Level2',
                     'Engagement - Level3',
                     
                     'Advocacy - Type', 'Advocacy - Units', 'Advocacy - DecisionMaker',
                     'Advocacy - Position', 'Advocacy - EWB', 'Advocacy - Purpose',
                     'Advocacy - Learned',
                     
                     'Publicity - Outlet', 'Publicity - Type', 'Publicity - Location',
                     'Publicity - Issue', 'Publicity - Circulation',
                     
                     'Fundraising - Goal', 'Fundraising - Revenue', 'Fundraising - Repeat',
                     
                     'WO - Company', 'WO - City', 'WO - Presenters', 'WO - Ambassador',
                     'WO - Email', 'WO - Phone', 'WO - NumPresentations',
                     'WO - Attendence', 'WO - Type',
                     
                     'CE - Name', 'CE - Code', 'CE - NumStudents', 'CE - ClassHours',
                     'CE - Professor', 'CE - Activity'])
    
    activities = Activity.objects.filter(visible=True)
    if group:
        activities = activities.filter(group=group)
        
    for a in activities:
        impact, func, ml, so, pe, pa, wo, ce, pub, fund = a.get_metrics(pad=True)
        
        row = [a.group.name, a.name]
        if impact:
            row.append(impact.description)
        else:
            row.append('')
            
        row.extend([a.date, a.date.strftime('%B'), schoolyear.school_year_name(a.date), a.numVolunteers, a.prepHours, a.execHours])
        
        if impact:
            row.extend([impact.goals, impact.outcome])
        else:
            row.extend(['', ''])
            
        row.extend([a.created_date, a.creator.visible_name(),
                    a.modified_date, a.editor.visible_name()])
        if a.confirmed:
            row.append('confirmed')
        else:
            row.append('unconfirmed')
            
        row.append(len(a.get_metrics()) - 1)
        purposes = ''
        for m in a.get_metrics():
            if not m.metricname == 'all':
                purposes = purposes + m.metricname + '-'
        if len(purposes):
            purposes = purposes[0:-1]
        row.append(purposes)
        
        if ml:
            row.append('1')
        else:
            row.append('0')
        if so:
            row.append('1')
        else:
            row.append('0')
        if func:
            row.append('1')
        else:
            row.append('0')
        if pe:
            row.append('1')
        else:
            row.append('0')
        if pa:
            row.append('1')
        else:
            row.append('0')
        if pub:
            row.append('1')
        else:
            row.append('0')
        if fund:
            row.append('1')
        else:
            row.append('0')
        if wo:
            row.append('1')
        else:
            row.append('0')
        if ce:
            row.append('1')
        else:
            row.append('0')
        
        if ml:
            row.append(ml.type)
            if ml.learning_partner:
                row.append('1')
            else:
                row.append('0')
            row.extend([ml.curriculum, ml.resources_by, ml.duration, ml.attendance, ml.new_attendance])
        else:
            row.extend(['', '', '', '', '', '', ''])
            
        if so:
            row.extend([so.school_name, so.teacher_name, so.teacher_email, so.teacher_phone, so.presentations, so.students, so.grades, so.subject, so.workshop, so.facilitators, so.new_facilitators])
        else:
            row.extend(['', '', '', '', '', '', '', '', '', '', ''])
            
        if func:
            row.extend([func.type, func.location, func.purpose, func.attendance, func.duration])
        else:
            row.extend(['', '', '', '', ''])
        
        if pe:
            row.extend([pe.type, pe.location, pe.purpose, pe.subject, pe.level1, pe.level2, pe.level3])
        else:
            row.extend(['', '', '', '', '', '', ''])
            
        if pa:
            row.extend([pa.type, pa.units, pa.decision_maker, pa.position, pa.ewb, pa.purpose, pa.learned])
        else:
            row.extend(['', '', '', '', '', '', ''])

        if pub:
            row.extend([pub.outlet, pub.type, pub.location, '', pub.circulation])
        else:
            row.extend(['', '', '', '', ''])
            
        if fund:
            row.extend([fund.goal, fund.revenue, ''])
        else:
            row.extend(['', '', ''])
            
        if wo:
            row.extend([wo.company, wo.city, wo.presenters, wo.ambassador, wo.email, wo.phone, wo.presentations, wo.attendance, wo.type])
        else:
            row.extend(['', '', '', '', '', '', '', '', ''])
            
        if ce:
            row.extend([ce.name, ce.code, ce.students, ce.hours, ce.professor, ce.ce_activity])
        else:
            row.extend(['', '', '', '', '', ''])

        writer.writerow([fix_encoding(s) for s in row])
            
    return response
