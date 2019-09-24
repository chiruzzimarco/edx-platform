"""
Video block Transformer
"""
from __future__ import absolute_import

import six
from django.conf import settings

from xmodule.video_module.video_utils import rewrite_video_url
from openedx.core.djangoapps.content.block_structure.transformer import BlockStructureTransformer


class VideoBlockURLTransformer(BlockStructureTransformer):
    """
    Transformer to re-write video urls for the mobile applications
    to server content from edx-video.
    """

    @classmethod
    def name(cls):
        return "video_url"

    WRITE_VERSION = 1
    READ_VERSION = 1
    STUDENT_VIEW_DATA = 'student_view_data'
    CDN_URL = getattr(settings, 'VIDEO_CDN_URL', {}).get('default', 'https://edx-video.net')
    VIDEO_FORMAT_EXCEPTIONS = ['youtube', 'fallback']

    @classmethod
    def collect(cls, block_structure):
        """
        collect and store video block's student view data.
        """
        for block_key in block_structure.topological_traversal(
            filter_func=lambda block_key: block_key.block_type == 'video',
            yield_descendants_of_unyielded=True,
        ):
            xblock = block_structure.get_xblock(block_key)
            block_structure.set_transformer_block_field(
                block_key, cls, cls.STUDENT_VIEW_DATA, xblock.student_view_data()
            )

    def transform(self, usage_info, block_structure):
        """
        Re-write all the video blocks' encoded videos URLs.

        For the encoded_videos dictionary, all the available video format URLs
        will be re-written to serve the videos from edx-video.net
        with YouTube and fallback URL as an exception. Fallback URL is an exception
        because when there is no video profile data in VAL, the user specified
        data from all_sources is taken, which can be URL from any CDN.
        """
        for block_key in block_structure.topological_traversal(
            filter_func=lambda block_key: block_key.block_type == 'video',
            yield_descendants_of_unyielded=True,
        ):
            student_view_data = block_structure.get_transformer_block_field(
                block_key, self, self.STUDENT_VIEW_DATA
            )
            encoded_videos = student_view_data['encoded_videos']

            for video_format, video_data in six.iteritems(encoded_videos):
                if video_format in self.VIDEO_FORMAT_EXCEPTIONS:
                    continue
                video_data['url'] = rewrite_video_url(self.CDN_URL, video_data['url'])
