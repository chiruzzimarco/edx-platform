"""
The Discount API Views should return information about discounts that apply to the user and course.

"""
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import six

from django.utils.decorators import method_decorator
from django.http import HttpResponseBadRequest
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from rest_framework.response import Response
from rest_framework.views import APIView

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.cors_csrf.decorators import ensure_csrf_cookie_cross_domain
from openedx.core.djangoapps.waffle_utils import WaffleFlag, WaffleFlagNamespace
from openedx.core.lib.api.authentication import OAuth2AuthenticationAllowInactiveUser
from openedx.core.lib.api.permissions import ApiKeyHeaderPermissionIsAuthenticated
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin

from lms.djangoapps.courseware.date_summary import verified_upgrade_link_is_valid
from course_modes.models import get_cosmetic_verified_display_price
from lms.djangoapps.commerce.utils import EcommerceService
from lms.djangoapps.experiments.stable_bucketing import stable_bucketing_hash_group
from student.models import CourseEnrollment
from track import segment


# .. feature_toggle_name: experiments.mobile_upsell_rev934
# .. feature_toggle_type: flag
# .. feature_toggle_default: False
# .. feature_toggle_description: Toggle mobile upsell enabled
# .. feature_toggle_category: experiments
# .. feature_toggle_use_cases: monitored_rollout
# .. feature_toggle_creation_date: 2019-09-05
# .. feature_toggle_expiration_date: None
# .. feature_toggle_warnings: None
# .. feature_toggle_tickets: REV-934
# .. feature_toggle_status: supported
MOBILE_UPSELL_FLAG = WaffleFlag(
    waffle_namespace=WaffleFlagNamespace(name=u'experiments'),
    flag_name=u'mobile_upsell_rev934',
    flag_undefined_default=False
)
MOBILE_UPSELL_EXPERIMENT = 'mobile_upsell_experiment'


class Rev934(DeveloperErrorViewMixin, APIView):
    """
    **Use Cases**

        Request upsell information for mobile app users

    **Example Requests**

        GET /api/experiments/v0/custom/REV-934/?course_id={course_key_string}

    **Response Values**

        Body consists of the following fields:
            show_upsell:
                whether to show upsell in the moble app in this case
            price:
                (optional) the price to show if show_upsell is true
            basket_url:
                (optional) the url to the checkout page with the course's sku if show_upsell is true
            upsell_flag:
                (optional) false if the upsell flag is off, not present otherwise

        Response:
            {
            "show_upsell": true,
            "price": "$199",
            "basket_url": "https://ecommerce.edx.org/basket/add?sku=abcdef"
            }

    **Parameters:**

        course_key_string:
            The course key that may be upsold

    **Returns**

        * 200 on success with above fields.
        * 401 if there is no user signed in.

        Example response:
        {
            "show_upsell": true,
            "price": "$199",
            "basket_url": "https://ecommerce.edx.org/basket/add?sku=abcdef"
        }
    """
    # https://courses.stage.edx.org/api/experiments/v0/custom/REV-934/?course_id=course-v1%3AedX%2BDemoX%2BDemo_Course

    authentication_classes = (
        JwtAuthentication,
        OAuth2AuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (ApiKeyHeaderPermissionIsAuthenticated,)

    @method_decorator(ensure_csrf_cookie_cross_domain)
    def get(self, request):
        """
        Return the if the course should be upsold in the mobile app, if the user has appropriate permissions.
        """
        if not MOBILE_UPSELL_FLAG.is_enabled():
            return Response({
                'show_upsell': False,
                'upsell_flag': False,
            })

        course_id = request.GET.get('course_id')
        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            return HttpResponseBadRequest("Missing or invalid course_id")

        course = CourseOverview.get_from_id(course_key)
        user = request.user

        try:
            enrollment = CourseEnrollment.objects.select_related(
                'course'
            ).get(user_id=user.id, course_id=course.id)
            user_upsell = verified_upgrade_link_is_valid(enrollment)
        except CourseEnrollment.DoesNotExist:
            user_upsell = True

        basket_link = EcommerceService().upgrade_url(user, course.id)
        upgrade_price = six.text_type(get_cosmetic_verified_display_price(course))
        could_upsell = bool(user_upsell and basket_link)

        bucket = stable_bucketing_hash_group(MOBILE_UPSELL_EXPERIMENT, 2, user.username)

        if could_upsell and hasattr(request, 'session') and MOBILE_UPSELL_EXPERIMENT not in request.session:
            properties = {
                'site': request.site.domain,
                'app_label': 'experiments',
                'bucket': bucket,
                'experiment': 'REV-934',
            }
            segment.track(
                user_id=user.id,
                event_name='edx.bi.experiment.user.bucketed',
                properties=properties,
            )

            # Mark that we've recorded this bucketing, so that we don't do it again this session
            request.session[MOBILE_UPSELL_EXPERIMENT] = True

        show_upsell = bool(bucket != 0 and could_upsell)
        if show_upsell:
            return Response({
                'show_upsell': show_upsell,
                'price': upgrade_price,
                'basket_url': basket_link,
            })
        else:
            return Response({
                'show_upsell': show_upsell,
                'upsell_flag': MOBILE_UPSELL_FLAG.is_enabled(),
                'experiment_bucket': bucket,
                'user_upsell': user_upsell,
                'basket_link': basket_link,
            })
