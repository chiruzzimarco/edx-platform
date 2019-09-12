"""
Video block Transformer
"""
from __future__ import absolute_import

import six
from django.conf import settings

from xmodule.video_module.video_utils import rewrite_video_url
from openedx.core.djangoapps.content.block_structure.transformer import BlockStructureTransformer


class VideoBlockURLTransformer(BlockStructureTransformer):

    @classmethod
    def name(cls):
        return "video_url"

    WRITE_VERSION = 1
    READ_VERSION = 1

    def __init__(self):
        self.cdn_url = getattr(settings, 'VIDEO_CDN_URL', {}).get('default')

    @classmethod
    def collect(cls, block_structure):
        pass

    def transform(self, usage_info, block_structure):

        for block_key in block_structure:
            if block_key.block_type != 'video':
                continue
            student_view_data = block_structure.get_xblock_field(block_key, 'student_view_data')
            encoded_videos = student_view_data['encoded_videos']
            for video_data in six.itervalues(encoded_videos):
                video_data['url'] = rewrite_video_url(self.cdn_url, video_data['url'])

            block_structure.set_transformer_block_field(block_key, self, 'student_view_data', student_view_data)
