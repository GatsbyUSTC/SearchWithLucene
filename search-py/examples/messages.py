from __future__ import absolute_import
from message import MessageSend, MessageRecv
from message.common import ErrorSend, ErrorRecv
from database import models
from examples.convert import Convertor
from django.db import transaction

def register_message():
    for msg_type in (RetrievePopularRecv, RetrieveRecentRecv):
        msg_type.register()

class RetrievePopularRecv(MessageRecv):
    def parse(self, data):
        self.require_fields(data, 'range')
        (self.start, self.max_count) = Convertor.get_range(data['range'])
        self.categories = data.get('categories') or []
        return True

    def handle_impl(self):
        result = []
        (count, records) = self.retrieve_list(self.start, self.max_count, self.categories)
        for entry in records:
            result.append(Convertor.basic_video_object(entry))
        self.reply_result(
            count  = count,
            result = result
        )

    def retrieve_list(self, start, max_count, categories):
        result_set = models.Content.objects.select_related()              \
                     .filter(status = models.CONTENT_STATUS_READY)
        if len(categories):
            result_set = result_set.filter(category_id__in = categories)
        return (result_set.count(), result_set.order_by(
            '-watch_count', '-rating_count', '-rating_total', '-creation_time')[start:(start + max_count)])

    @classmethod
    def get_message_type(cls):
        return 'popular'

class RetrieveRecentRecv(MessageRecv):
    def parse(self, data):
        self.require_fields(data, 'user_id', 'count')
        self.user_id = data['user_id']
        self.count   = data['count']
        return True

    def handle_impl(self):
        result = []
        for obj in self.retrieve_list(self.user_id, self.count):
            result.append(Convertor.basic_video_object(obj))
        self.reply_result(
            result = result
        )

    @transaction.commit_on_success
    def retrieve_list(self, user_id, count):
        session_ids = models.SessionParticipant.objects.values('session_id')    \
                    .filter(user_id = user_id)
        content_ids = models.SessionVideo.objects.values('content_id')          \
                    .filter(id__in=session_ids).order_by('-update_time')
        id_list = []
        for content in content_ids:
            content_id = content['content_id']
            if count > 0:
                if not content_id in id_list:
                    id_list.append(content_id)
                    count -= 1
            else:
                break
        contents = models.Content.objects.select_related()                      \
                     .filter(id__in=id_list)
        content_dict = {}
        for content in contents:
            content_dict[content.id] = content
        result = []
        for content_id in id_list:
            content = content_dict.get(content_id)
            if content is not None:
                result.append(content)
        return result

    @classmethod
    def get_message_type(cls):
        return 'recent'

