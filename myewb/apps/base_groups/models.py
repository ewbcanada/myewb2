"""myEWB base groups models declarations

This file is part of myEWB
Copyright 2009 Engineers Without Borders (Canada) Organisation and/or volunteer contributors
Some code derived from Pinax, copyright 2008-2009 James Tauber and Pinax Team, licensed under the MIT License

Last modified on 2009-07-29
@author Joshua Gorner, Benjamin Best
"""

import datetime

from django.core.urlresolvers import reverse
from django.contrib.auth.models import  User
from django.utils.translation import ugettext_lazy as _
from django.db import models, connection
from django.core.mail import EmailMessage

from groups.base import Group

class BaseGroup(Group):
    """Base group (from which networks, communities, projects, etc. derive).
    
    Not intended to be instantiated by itself.
    """
    
    model = models.CharField(_('group model'), max_length=500, null=True, blank=True)
    parent = models.ForeignKey('self', related_name="children", verbose_name=_('parent'), null=True, blank=True)
    
    member_users = models.ManyToManyField(User, through="GroupMember", verbose_name=_('members'))
    # TODO: parent groups
	
	# private means only members can see the group
    private = models.BooleanField(_('private'), default=False)
	
    def user_is_member(self, user):
        return (self.members.filter(user=user).count() > 0)
            
    def user_is_admin(self, user):
        return (self.members.filter(user=user, is_admin=True).count() > 0)

    def get_absolute_url(self):
        return reverse('group_detail', kwargs={'group_slug': self.slug})

    def get_member_emails(self):
        members_with_emails = self.members.select_related(depth=1).exclude(user__email='')
        return [member.user.email for member in members_with_emails]

    def send_mail_to_members(self, subject, body, html=False, fail_silently=False):
        """
        Creates and sends an email to all members of a network using Django's
        EmailMessage.
        Takes in a a subject and a message and an optional fail_silently flag.
        Automatically sets:
        from_email: group_name <group_slug@ewb.ca>
        to: list-group_slug@ewb.ca
        bcc: list of member emails
        """
        msg = EmailMessage(
                subject=subject, 
                body=body, 
                from_email='%s <%s@ewb.ca>' % (self.name, self.slug), 
                to=['list-%s@ewb.ca' % self.slug],
                bcc=self.get_member_emails(),
                )
        if html:
            msg.content_subtype = "html"
        msg.send(fail_silently=fail_silently)
	
	# TODO:
	# mailing list
	# list of members (NOT CSV)
	
class GroupMember(models.Model):
    group = models.ForeignKey(BaseGroup, related_name="members", verbose_name=_('group'))
    user = models.ForeignKey(User, related_name="member_groups", verbose_name=_('user'))
    is_admin = models.BooleanField(_('admin'), default=False)
    admin_title = models.CharField(_('admin title'), max_length=500, null=True, blank=True)
    joined = models.DateTimeField(_('joined'), default=datetime.datetime.now)

    # away = models.BooleanField(_('away'), default=False)
    # away_message = models.CharField(_('away_message'), max_length=500)
    # away_since = models.DateTimeField(_('away since'), default=datetime.now)

class GroupLocation(models.Model):
    group = models.ForeignKey(BaseGroup, related_name="locations", verbose_name=_('group'))
    place = models.CharField(max_length=100, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)