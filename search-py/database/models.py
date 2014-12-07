# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#     * Rearrange models' order
#     * Make sure each model has one field with primary_key=True
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin.py sqlcustom [appname]'
# into your database.
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=30)
    class Meta:
        db_table = 'category'

class Activation(models.Model):
    user = models.OneToOneField(User, primary_key=True)
    state = models.IntegerField()
    activation_key = models.CharField(max_length=32, null=True)
    class Meta:
        db_table = 'activation'

class Content(models.Model):
    id = models.CharField(max_length=32, primary_key=True)
    title = models.CharField(max_length=100)
    owner = models.ForeignKey(User, null=True)
    category = models.ForeignKey(Category, null=True)
    creation_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now_add=True)
    watch_count = models.IntegerField(default=0)
    status = models.IntegerField()
    description = models.TextField(max_length=25000)
    rating_total = models.IntegerField()
    rating_count = models.IntegerField()
    video_info = models.TextField()
    checksum = models.CharField(max_length=32)
    class Meta:
        db_table = 'content'

class Device(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User)
    type = models.IntegerField()
    token = models.CharField(max_length=32, null=True)
    class Meta:
        db_table = 'device'

class OttContent(models.Model):
    content = models.OneToOneField(Content, primary_key=True)
    ottsource = models.ForeignKey('OttSource')
    original_link = models.CharField(max_length=255, null=True)
    class Meta:
        db_table = 'ott_content'

class OttSource(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=128)
    link = models.CharField(max_length=256, null=True)
    icon = models.CharField(max_length=256, null=True)
    class Meta:
        db_table = 'ott_source'

class Rating(models.Model):
    content = models.ForeignKey(Content)
    user = models.ForeignKey(User)
    score = models.IntegerField()
    class Meta:
        db_table = 'rating'
        unique_together = ("content", "user")

class SessionParticipant(models.Model):
    session = models.ForeignKey('SessionVideo')
    user = models.ForeignKey(User)
    class Meta:
        db_table = 'session_participant'
        unique_together = ("session", "user")

class SessionVideo(models.Model):
    id = models.AutoField(primary_key=True)
    owner = models.ForeignKey(User)
    content = models.ForeignKey(Content)
    update_time = models.DateTimeField(auto_now=True)
    position = models.IntegerField()
    type = models.IntegerField()
    class Meta:
        db_table = 'session_video'

class SharedMedia(models.Model):
    id = models.CharField(max_length=32, primary_key=True)
    sender = models.ForeignKey(User, related_name='sender')
    creation_time = models.DateTimeField(auto_now=True)
    title = models.TextField(null=True)
    type = models.IntegerField()
    class Meta:
        db_table = 'shared_media'

class Tag(models.Model):
    id = models.AutoField(primary_key=True)
    content = models.ForeignKey(Content)
    name = models.CharField(max_length=30)
    class Meta:
        db_table = 'tag'

###     new models start here   ###
class AccessGroup(models.Model):

    PAYMENT_TYPE_SUBSCRIPTION = 1
    PAYMENT_TYPE_PER_VIEW = 2
    PAYMENT_TYPE_FREE = 3
    PAYMENT_TYPES = (
        (PAYMENT_TYPE_SUBSCRIPTION, 'only subscribed users can view'),
        (PAYMENT_TYPE_PER_VIEW, 'users should pay for every viewing'),
        (PAYMENT_TYPE_FREE, 'users are free to view')
    )

    DRM_TYPE_SESSION_ENCRYPTION = 1
    DRM_TYPE_WIDEVINE = 2
    DRM_TYPE_NONE = 3
    DRM_TYPES = (
        (DRM_TYPE_SESSION_ENCRYPTION, 'protect video via session encryption'),
        (DRM_TYPE_WIDEVINE, 'protect video with Widevine'),
        (DRM_TYPE_NONE, 'users are free to view')
    )

    id = models.AutoField(primary_key=True)
    owner = models.ForeignKey('Enterprise')
    name = models.CharField(max_length=45)
    payment_type = models.IntegerField(choices=PAYMENT_TYPES, default=PAYMENT_TYPE_FREE, blank=True)
    price = models.IntegerField()      #price in Singapore cents
    subscription_type = models.CharField(max_length=12)
    drm_scheme =  models.IntegerField(choices=DRM_TYPES, default=DRM_TYPE_NONE, blank=True)
    availability = models.CharField(max_length=6)   #public, in-system-only
    class Meta:
        db_table = 'access_group'

class ContentAccessGroup(models.Model):
    content = models.ForeignKey('Content')
    access_group = models.ForeignKey('AccessGroup')  #if none, 
    class Meta:
        unique_together = (("content", "access_group"),)

class UserAccessGroup(models.Model):
    user = models.ForeignKey(User)
    access_group = models.ForeignKey('AccessGroup')
    class Meta:
        unique_together = (("user", "access_group"),)

class ContentEncodingProfile(models.Model):
    content = models.ForeignKey('Content')
    encoding_profile = models.ForeignKey('EncodingProfile', null= True)
    class Meta:
        unique_together = (("content", "encoding_profile"),)

class ContentAdGroup(models.Model):
    content = models.ForeignKey('Content')
    ad_group = models.ForeignKey('AdGroup')
    class Meta:
        unique_together = (("content", "ad_group"),)

class AdConfig(models.Model):
    content = models.ForeignKey('Content', primary_key=True)
    name = models.CharField(max_length=45)
    preplay_ad = models.IntegerField()
    overlay_ad = models.IntegerField()
    pause_ad = models.IntegerField()
    text_ad = models.IntegerField()
    class Meta:
        db_table = 'ad_config'

class AdConfigGroup(models.Model):
    config = models.ForeignKey(AdConfig)
    group = models.ForeignKey('AdGroup')
    class Meta:
        db_table = 'ad_config_group'

class AdGroup(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=45)
    owner = models.ForeignKey('Enterprise')
    class Meta:
        db_table = 'ad_group'

class Advertisement(models.Model):
    AD_TYPE_PRE_PLAY = 1
    AD_TYPE_PAUSE_AD = 2
    AD_TYPE_OVERLAY  = 3
    AD_TYPES = (
        (AD_TYPE_PRE_PLAY, 'display the ad before video start to play'),
        (AD_TYPE_PAUSE_AD, 'display the ad when video pauses'),
        (AD_TYPE_OVERLAY, 'display the ad as a overlay')
    )

    id = models.AutoField(primary_key=True)
    ad_group = models.ForeignKey(AdGroup)
    type = models.IntegerField(choices=AD_TYPES, default=AD_TYPE_PRE_PLAY)
    file_path = models.CharField(max_length=255)
    duration = models.IntegerField()
    can_close = models.IntegerField(blank=True, null=True)
    link = models.CharField(max_length=255)
    position_x = models.FloatField(blank=True, null=True)
    position_y = models.FloatField(blank=True, null=True)
    height = models.FloatField(blank=True, null=True)
    width = models.FloatField(blank=True, null=True)
    class Meta:
        db_table = 'advertisement'

class Channel(models.Model):
    EPG_TYPE_FILE = 1
    EPG_TYPE_URL = 2
    EPG_TYPES = (
        (EPG_TYPE_FILE, 'upload a file (XML or EXCEL) as EPG source'),
        (EPG_TYPE_URL, 'submit a URL as EPG source'),
    )

    name = models.CharField(max_length=45)
    owner = models.ForeignKey('Enterprise', null=True)
    source = models.ForeignKey('SourceInfo', null=True)
    description = models.TextField()
    additional_info = models.TextField(blank=True)
    epg_type = models.IntegerField(choices=EPG_TYPES, default=EPG_TYPE_FILE, blank=True)
    epg_address = models.CharField(max_length=255, blank=True)
    encoding_profile = models.ForeignKey('EncodingProfile', null= True)
    class Meta:
        db_table = 'channel'

class EncodingConfig(models.Model):
    id = models.AutoField(primary_key=True)
    profile = models.ForeignKey('EncodingProfile')
    width = models.IntegerField()
    height = models.IntegerField()
    framerate = models.FloatField()
    video_config = models.CharField(max_length=255)
    audio_config = models.CharField(max_length=255)
    encode_param = models.CharField(max_length=255, blank=True)
    format = models.CharField(max_length=30)
    class Meta:
        db_table = 'encoding_config'

class EncodingProfile(models.Model):
    id = models.AutoField(primary_key=True)
    owner = models.ForeignKey('Enterprise', blank=True, null=True)
    name = models.CharField(max_length=45)
    class Meta:
        db_table = 'encoding_profile'

class EnterpisePermission(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=10)
    display_name = models.CharField(max_length=45)
    description = models.TextField()
    class Meta:
        db_table = 'enterpise_permission'

class Enterprise(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=45)
    email = models.CharField(max_length=45)
    website = models.CharField(max_length=255, blank=True)
    icon = models.CharField(max_length=255, blank=True)
    expire_date = models.DateField(blank=True, null=True)
    class Meta:
        db_table = 'enterprise'

class EnterpriseRole(models.Model):
    id = models.AutoField(primary_key=True)
    enterprise = models.ForeignKey(Enterprise, blank=True, null=True)
    name = models.CharField(max_length=45)
    class Meta:
        db_table = 'enterprise_role'

class EnterpriseRolePerm(models.Model):
    role = models.ForeignKey(EnterpriseRole)
    permission = models.ForeignKey(EnterpisePermission)
    class Meta:
        db_table = 'enterprise_role_perm'

class EnterpriseUser(models.Model):
    user = models.ForeignKey(User)
    enterprise = models.ForeignKey(Enterprise)
    role = models.ForeignKey(EnterpriseRole, db_column='role', null=True)
    class Meta:
        db_table = 'enterprise_user'

class Package(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=45)
    provider = models.ForeignKey(Enterprise)
    description = models.TextField()
    target_users = models.CharField(max_length=11)   #should it better be AccessGroup?
    access_group = models.ForeignKey(AccessGroup, blank=True, null= True)
    expire_date = models.DateTimeField(blank=True, null=True)
    class Meta:
        db_table = 'package'

class PackageItem(models.Model):
    id = models.AutoField(primary_key=True)
    package = models.ForeignKey(Package, blank=True, null=True)
    sub_access_group = models.ForeignKey(AccessGroup)
    sub_content = models.ForeignKey(Content, blank=True, null=True)
    sub_channel = models.ForeignKey(Channel, blank=True, null=True)
    sub_provider = models.ForeignKey(Enterprise, blank=True, null=True)
    validity_period = models.TimeField(blank=True, null=True)
    class Meta:
        db_table = 'package_item'

class Program(models.Model):
    content = models.ForeignKey(Content, null=True)
    name = models.CharField(max_length=128)
    channel = models.ForeignKey(Channel, null=True)
    start_time = models.DateTimeField()
    duration = models.IntegerField()   #time in seconds
    source = models.ForeignKey('SourceInfo', blank=True, null=True)
    encoding_profile = models.ForeignKey(EncodingProfile, blank=True, null=True)
    additional_info = models.TextField(blank=True)
    class Meta:
        db_table = 'program'

class Rendition(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    content = models.ForeignKey(Content)
    encoding_config = models.ForeignKey(EncodingConfig)
    size = models.BigIntegerField(blank=True, null=True)
    class Meta:
        db_table = 'rendition'

class SharedMediaReceiver(models.Model):
    content = models.ForeignKey(SharedMedia)
    receiver = models.ForeignKey(User, related_name='receiver')
    class Meta:
        db_table = 'shared_media_receiver'
        unique_together = ("content", "receiver")

class SourceInfo(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    type = models.CharField(max_length=13)
    address = models.CharField(max_length=255)
    allow_record = models.IntegerField()
    class Meta:
        db_table = 'source_info'

class Subscription(models.Model):
    id = models.AutoField(primary_key=True)
    package = models.ForeignKey(Package)
    user = models.ForeignKey(User)
    expire_date = models.DateTimeField(blank=True, null=True)
    class Meta:
        db_table = 'subscription'

class SynGroup(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=45)
    owner = models.ForeignKey(Enterprise)
    class Meta:
        db_table = 'syn_group'

class SynGroupTarget(models.Model):
    syn_group = models.ForeignKey(SynGroup)
    syn_target = models.ForeignKey('SynTarget')
    class Meta:
        db_table = 'syn_group_target'

class SynTarget(models.Model):
    id = models.AutoField(primary_key=True)
    owner = models.ForeignKey(Enterprise)
    website_id = models.CharField(max_length=45)
    name = models.CharField(max_length=45)
    access_token = models.CharField(max_length=45)
    description = models.TextField(blank=True)
    class Meta:
        db_table = 'syn_target'

class Syndication(models.Model):
    target = models.ForeignKey(SynTarget)
    content = models.ForeignKey(Content)
    external_id = models.CharField(max_length=255)
    class Meta:
        db_table = 'syndication'

class VodContent(models.Model):
    content = models.ForeignKey(Content, primary_key = True)
    owner = models.ForeignKey(Enterprise)
    class Meta:
        db_table = 'vod_content'

class AdaptationData(models.Model):
    id = models.AutoField(primary_key=True)
    video = models.ForeignKey(Content)
    owner = models.ForeignKey(Enterprise)
    data = models.TextField()
    class Meta:
        db_table = 'adaptation'
        unique_together = ("video", "owner")

###     new models end here   ###

class TVNews(models.Model):
    user = models.ForeignKey(User)
    time = models.DateTimeField(auto_now_add=True)
    content = models.TextField()

class TVPlaylist(models.Model):
    user = models.ForeignKey(User)
    content = models.ForeignKey(Content)
    class Meta:
        unique_together = ("user", "content")

class UserProfile(models.Model):
    user = models.ForeignKey(User)
    phone = models.CharField(max_length = 15)
    avatar = models.CharField(max_length = 128)
    class Meta:
        db_table = 'user_profile'

def get_xmpp_name_from_user(user):
    import re
    MAX_LEN = 6
    name = 'u' + str(user.id) + "".join(re.split("[^a-zA-Z]*", user.first_name[:MAX_LEN] + user.last_name[:MAX_LEN]))
    return name.lower()

CONTENT_STATUS_READY        = 1
CONTENT_STATUS_TRANSCODING  = 2
CONTENT_STATUS_CORRUPTED    = 3
CONTENT_STATUS_DELETED      = 4

SESSION_VIDEO_TYPE_SINGLE   = 1
SESSION_VIDEO_TYPE_SHARED   = 2

SHARED_MEDIA_TYPE_IMAGE     = 1
SHARED_MEDIA_TYPE_CLIP      = 2

DEVICE_TYPE_PC              = 1
DEVICE_TYPE_MOBILE          = 2
DEVICE_TYPE_TV              = 3

ACTIVATION_UNACTIVATED      = 1

###                 ###
#       Error ID      #
###                 ###

#General

INVALID_PARAMETER = 1101 #There is something wrong with the user input.
INTERNAL_ERROR_GENERAL = 1201  #Internal server error. E.g. a service is down.
PERMISSION_DENIED = 1301 #The user do not have certain permission.

#User
USER_ALREADY_EXIST = 2101 #There is a user with the same name exists.
USER_INVALID_NAME = 2102 #The login id is not a valid email address, or it is not end with ntu.edu.sg.

USER_NOT_LOGIN = 2201 #The user has not login into the system.
USER_LOGIN_FAILED = 2202 #User not found or wrong password.
USER_LOGIN_INACTIVATED = 2203 #The user has not been activated yet.

USER_ACTIVATION_ACTIVATED = 2301
USER_ACTIVATION_INVALID_KEY = 2302
USER_ACTIVATION_EXPIRED = 2303

#Content
CONTENT_LIMIT_REACHED = 3101 #The user has reached his resource limit.
CONTENT_IO_FAILED = 3201  #Failed to read or write content.

