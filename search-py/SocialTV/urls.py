from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

from account.views import account_register, account_activate, account_login, account_portal, account_logout, account_tuhaozuopengyou, account_resend, account_chatconfig, account_session_key, account_search, account_info, account_agreement, issue_report, enduser_portal, enterprise_portal, enterprise_search 

from content.views import forward_request, content_upload#content_list, content_search, content_upload
from epg.views import epg_add, channel_list, program_list, channel_get, channel_edit
from access.views import access_list, access_add, access_list_as_select



urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'SocialTV.views.home', name='home'),
    # url(r'^SocialTV/', include('SocialTV.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    url(r'^$', account_login),

    ('^users/chatconfig/$', account_chatconfig),
    ('^users/session_key/$', account_session_key),
    ('^users/resend/$', account_resend),
    ('^users/agreement/$', account_agreement),
    ('^users/registration/$', account_register),
    ('^users/activation/$', account_activate),
    ('^users/login/$', account_login),
    ('^users/logout/$', account_logout),
    ('^users/portal/$', account_portal),
    ('^users/enduser_portal/$', enduser_portal),
    ('^users/enterprise_portal/$', enterprise_portal),
    ('^users/search/$', account_search),
    ('^users/info/$', account_info),
    ('^search/$', forward_request),
    ('^content/list/$', forward_request),
    ('^content/my/$', forward_request),
    ('^content/upload/$', content_upload),
    ('^issue/report/$', issue_report),
    #('^search/$', content_search),

    #(r'^site_media/(?P<path>.*)$', 'django.views.static.serve',
    #        {'document_root': 'WebPortal/'}),
    
    ('^epg/add/$', epg_add),
    ('^epg/channel/list/$', channel_list),
    ('^epg/channel/get/$', channel_get),
    ('^epg/channel/edit/$', channel_edit),
    ('^epg/program/list/$', program_list),

    ('^access/add/$',access_add),
    ('^access/list/$',access_list),
    ('^access/list_as_select/$',access_list_as_select),

    ('^enterprise/search/$', enterprise_search)

    
)
