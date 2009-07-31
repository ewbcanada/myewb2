"""myEWB base groups generic views

This file is part of myEWB
Copyright 2009 Engineers Without Borders (Canada) Organisation and/or volunteer contributors
Some code derived from Pinax, copyright 2008-2009 James Tauber and Pinax Team, licensed under the MIT License

Last modified on 2009-07-29
@author Joshua Gorner, Benjamin Best
"""

from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils.datastructures import SortedDict

from base_groups.models import BaseGroup, GroupMember
from base_groups.forms import GroupMemberForm

def members_index(request, group_slug, group_model=None, form_class=GroupMemberForm,
        template_name='base_groups/members_index.html', new_template_name='base_groups/new_member.html'):
    # handle generic call
    if group_model is None:
        group = get_object_or_404(BaseGroup, slug=group_slug)
        return HttpResponseRedirect(reverse('%s_members_index' % group.model, kwargs={'group_slug': group_slug}))
        
    user = request.user    
        
    group = get_object_or_404(group_model, slug=group_slug)
    if request.method == 'GET':
        members = GroupMember.objects.filter(group=group)
        return render_to_response(
            template_name,
            {
                'group': group,
                'members': members,
                'is_admin': group.user_is_admin(user),
            },
            context_instance=RequestContext(request),
        )
    elif request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            member = form.save(commit=False)
            # General users can only add themselves as members
            if user == member.user or user.is_staff or group.user_is_admin(user):   
                if not (user.is_staff or group.user_is_admin(user)):
                    # General users cannot make themselves admins
                    member.is_admin = False
                    member.admin_title = ""
                member.group = group
                member.save()
                return HttpResponseRedirect(reverse('%s_member_detail' % group_model._meta.module_name, kwargs={'group_slug': group_slug, 'username': member.user.username}))
            else:
                return render_to_response(
                    new_template_name,
                    {
                        'group': group,
                        'form': form,
                        'is_admin': group.user_is_admin(user),
                    },
                    context_instance=RequestContext(request),
                )
        else:
            return render_to_response(
                new_template_name,
                {
                    'group': group,
                    'form': form,
                    'is_admin': group.user_is_admin(user),
                },
                context_instance=RequestContext(request),
            )

@login_required
def new_member(request, group_slug, group_model=None, form_class=GroupMemberForm,
        template_name='base_groups/new_member.html', index_template_name='base_groups/members_index.html'):
    # handle generic call
    if group_model is None:
        group = get_object_or_404(BaseGroup, slug=group_slug)
        model_name = group.model
        return HttpResponseRedirect(reverse('%s_new_member' % group.model, kwargs={'group_slug': group_slug}))    
        
    group = get_object_or_404(group_model, slug=group_slug)
    
    if request.method == 'POST':
        return members_index(request, group_slug, group_model, form_class, index_template_name, template_name)
    form = form_class()
    return render_to_response(
        template_name,
        {
            'group': group,
            'form': form,
            'is_admin': group.user_is_admin(request.user),
        },
        context_instance=RequestContext(request),
    )

def member_detail(request, group_slug, username, group_model=None, form_class=GroupMemberForm, 
        template_name='base_groups/member_detail.html', edit_template_name='base_groups/edit_member.html'):
    # handle generic call
    if group_model is None:
        group = get_object_or_404(BaseGroup, slug=group_slug)
        return HttpResponseRedirect(reverse('%s_member_detail' % group.model, kwargs={'group_slug': group_slug, 'username': username}))    
        
    group = get_object_or_404(group_model, slug=group_slug)
    user = get_object_or_404(User, username=username)
    member = get_object_or_404(GroupMember, group=group, user=user)
    # retrieve details
    if request.method == 'GET':
        return render_to_response(
            template_name,
            {
                'group': group,
                'member': member,
                'is_admin': group.user_is_admin(user),
            },
            context_instance=RequestContext(request),
        )
    # update existing resource
    elif request.method == 'POST':
        form = form_class(request.POST, instance=member)
        # if form saves, return detail for saved resource
        if form.is_valid():
            member = form.save()
            return render_to_response(
                template_name,
                {
                    'group': group,
                    'member': member,
                    'is_admin': group.user_is_admin(user),
                },
                context_instance=RequestContext(request),
            )
        # if save fails, go back to edit_resource page
        else:
            return render_to_response(
                edit_template_name,
                {
                    'group': group,
                    'form': form,
                    'member': member,
                    'is_admin': group.user_is_admin(user),
                },
                context_instance=RequestContext(request),
            )

@login_required
def edit_member(request, group_slug, username, group_model=None, form_class=GroupMemberForm, 
        template_name='base_groups/edit_member.html', detail_template_name='base_groups/member_detail.html'):
    # handle generic call
    if group_model is None:
        group = get_object_or_404(BaseGroup, slug=group_slug)
        return HttpResponseRedirect(reverse('%s_edit_member' % group.model, kwargs={'group_slug': group_slug, 'username': username}))         
    
    group = get_object_or_404(group_model, slug=group_slug)
    user = get_object_or_404(User, username=username)
    if request.method == 'POST':
        # this results in a non-ideal URL (/../edit) but only way we can save changes
        return member_detail(request, group_slug, username, group_model, form_class, detail_template_name, template_name)
    member = get_object_or_404(GroupMember, group=group, user=user)
    form = form_class(instance=member)
    return render_to_response(
        template_name,
        {
            'group': group,
            'form': form,
            'member': member,
            'is_admin': group.user_is_admin(user),
        },
        context_instance=RequestContext(request),
    )

@login_required
def delete_member(request, group_slug, username, group_model=None):    
    # handle generic call
    if group_model is None:
        group = get_object_or_404(BaseGroup, slug=group_slug)
        return HttpResponseRedirect(reverse('%s_delete_member' % group.model, kwargs={'group_slug': group_slug, 'username': username}))
        
    group = get_object_or_404(group_model, slug=group_slug)
    user = get_object_or_404(User, username=username)
    member = get_object_or_404(GroupMember, group=group, user=user)
    if request.method == 'POST':
        member.delete()
        return HttpResponseRedirect(reverse('%s_members_index' % group_model._meta.module_name, kwargs={'group_slug': group_slug,}))
    