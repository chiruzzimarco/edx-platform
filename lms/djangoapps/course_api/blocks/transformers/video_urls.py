"""
Video block Transformer
"""
from __future__ import absolute_import

from django.conf import settings

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
            svd = block_structure.get_xblock_field(block_key, 'student_view_data')
            # Initial testing
            svd['length'] = 6
            svd = block_structure.set_transformer_block_field(block_key, self, 'student_view_data', svd)
