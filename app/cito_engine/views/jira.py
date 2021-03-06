# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
from django.views.generic.edit import FormView
from django.http import HttpResponse
from django.shortcuts import redirect
from cito_engine.forms.jira_form import JIRAForm, JIRAUpdateForm, JIRABulkModifyForm
from cito_engine.models import JIRATickets, Incident
from braces.views import LoginRequiredMixin


class JIRAAddView(LoginRequiredMixin, FormView):
    """
    View to add Supression
    """
    template_name = 'generic_form.html'
    form_class = JIRAForm
    success_url = '/incidents/'

    def get_context_data(self, **kwargs):
        context = super(JIRAAddView, self).get_context_data(**kwargs)
        context['page_title'] = context['box_title'] = 'Add JIRA'
        return context

    def form_valid(self, form):
        try:
            incident = Incident.objects.get(pk=form.cleaned_data.get('incident_id'))
        except Incident.DoesNotExist, Incident.MultipleObjectsReturned:
            redirect('/incidents/')
            return
        try:
            ticket = form.create_jira(username=self.request.user.username)
        except Exception as e:
            return HttpResponse(status=500, content=e)
        JIRATickets.objects.create(user=self.request.user, incident=incident, ticket=ticket)
        return redirect('/incidents/view/%s/' % incident.id)

class JIRAUpdateView(LoginRequiredMixin, FormView):
    """
    View to manually update the JIRA ticket ID for incident
    """
    template_name = 'generic_form.html'
    form_class = JIRAUpdateForm
    success_url = '/incidents/'

    def get_context_data(self, **kwargs):
        context = super(JIRAUpdateView, self).get_context_data(**kwargs)
        context['page_title'] = context['box_title'] = 'Manually update JIRA'
        return context

    def form_valid(self, form):
        try:
            incident = Incident.objects.get(pk=form.cleaned_data.get('incident_id'))
        except Incident.DoesNotExist, Incident.MultipleObjectsReturned:
            redirect('/incidents/')
            return
        # Get the ticket or create one
        # Have to use this method because JIRATickets.user is a mandatory column, hence
        # cannot use get_or_create
        try:
            ticket = JIRATickets.objects.get(incident=incident)
            ticket.user = self.request.user
        except JIRATickets.DoesNotExist:
            ticket = JIRATickets.objects.create(incident=incident, user=self.request.user)

        ticket.ticket = form.cleaned_data.get('ticket')
        ticket.save()
        return redirect('/incidents/view/%s/' % incident.id)

class JIRABulkUpdateView(LoginRequiredMixin, FormView):
    template_name = 'generic_form.html'
    form_class = JIRABulkModifyForm
    success_url = '/incidents/'

    def get_context_data(self, **kwargs):
        context = super(JIRABulkUpdateView, self).get_context_data(**kwargs)
        context['page_title'] = context['box_title'] = 'Bulk modify JIRA for incidents'
        return context

    def form_valid(self, form):
        incidents = form.cleaned_data.get('incidents')
        jira_id = form.cleaned_data.get('jira_id')
        # make sure we received a list of incident ids
        try:
            incident_list = [int(i) for i in incidents.split(',')]
        except:
            return HttpResponse(status=400, content=b'Bad instance IDs')

        if not incident_list:
            return redirect(self.success_url)

        for incident in Incident.objects.filter(pk__in=incident_list):
            try:
                ticket = JIRATickets.objects.get(incident=incident)
                ticket.user = self.request.user
            except JIRATickets.DoesNotExist:
                ticket = JIRATickets.objects.create(incident=incident, user=self.request.user)

            ticket.ticket = jira_id
            ticket.save()

        return redirect(self.success_url)