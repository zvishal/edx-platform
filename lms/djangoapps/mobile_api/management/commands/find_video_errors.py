"""
Command to find video pipeline/migration/etc errors.
"""
from collections import defaultdict
import logging

from django.core.management.base import BaseCommand, CommandError
from edxval.api import get_videos_for_course
from lms.djangoapps.course_api.blocks.transformers.student_view import StudentViewTransformer
from lms.djangoapps.course_blocks.api import get_course_in_cache
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.django import modulestore


log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Example usage:
        $ ./manage.py lms find_video_errors --all --settings=devstack
        $ ./manage.py lms find_video_errors 'edX/DemoX/Demo_Course' --settings=devstack
    """
    args = '<course_id course_id ...>'
    help = 'Find and reports video-related errors in one or more courses.'

    def add_arguments(self, parser):
        """
        Entry point for subclassed commands to add custom arguments.
        """
        parser.add_argument(
            '--all',
            help='Find video-related errors for all courses.',
            action='store_true',
            default=False,
        )
        parser.add_argument(
            '--verbose',
            help='Enable verbose logging.',
            action='store_true',
            default=False,
        )
        parser.add_argument(
            '--start',
            help='Starting index of course.',
            default=0,
            type=int,
        )
        parser.add_argument(
            '--end',
            help='Ending index of course.',
            default=0,
            type=int,
        )

    def handle(self, *args, **options):

        if options.get('all'):
            course_keys = [course.id for course in modulestore().get_course_summaries()]
            if options.get('start'):
                end = options.get('end') or len(course_keys)
                course_keys = course_keys[options['start']:end]
        else:
            if len(args) < 1:
                raise CommandError('At least one course or --all must be specified.')
            try:
                course_keys = [CourseKey.from_string(arg) for arg in args]
            except InvalidKeyError:
                raise CommandError('Invalid key specified.')

        log.info('Reporting on video errors for %d courses.', len(course_keys))

        if options.get('verbose'):
            log.setLevel(logging.DEBUG)
        else:
            log.setLevel(logging.CRITICAL)

        video_error_stats = _VideoErrorStats()
        for course_key in course_keys:
            try:
                self._report_video_errors_in_course(course_key, video_error_stats)

            except Exception as ex:  # pylint: disable=broad-except
                log.exception(
                    'An error occurred while reporting video-related errors in course %s: %s',
                    unicode(course_key),
                    ex.message,
                )

        log.info('Finished reporting on video errors.')
        log.critical('Video Error data: %s', unicode(video_error_stats))

    def _report_video_errors_in_course(self, course_key, video_error_stats):
        """
        Reports on video errors in the given course.
        """
        log.info('Video error check starting for course %s.', unicode(course_key))

        block_structure = get_course_in_cache(course_key)
        edx_video_ids_in_val = self._get_edx_video_ids_bound_to_course(course_key)

        for block_key in block_structure.get_block_keys():
            if block_key.category != 'video':
                continue
            edx_video_id = self._get_edx_video_id(block_structure, block_key)
            if not edx_video_id:
                video_error_stats.on_no_edx_video_id(course_key, block_key)
            if edx_video_id not in edx_video_ids_in_val:
                video_error_stats.on_course_not_bound_to_video(course_key, block_key)

        log.info('Video error check complete for course %s.', unicode(course_key))

    def _get_edx_video_id(self, block_structure, block_key):
        """
        Returns the edx_video_id for the given block.
        """
        return block_structure.get_transformer_block_field(
            block_key,
            StudentViewTransformer,
            StudentViewTransformer.STUDENT_VIEW_DATA,
        )

    def _get_edx_video_ids_bound_to_course(self, course_key):
        """
        Returns the list of edx_video_ids bound to the given course in VAL.
        """
        return [video['edx_video_id'] for video in get_videos_for_course(course_key)]


class PrettyDefaultDict(defaultdict):
    """
    Wraps defaultdict to provide a better string representation.
    """
    __repr__ = dict.__repr__


class _CourseErrorStats(object):
    """
    Class for aggregated DAG data for a specific course run.
    """
    def __init__(self):
        self.num_of_videos_without_edx_video_id = 0
        self.num_of_videos_without_bound_course = 0
        self.videos_without_edx_video_id = []
        self.videos_without_bound_course = []

    def __repr__(self):
        return repr(vars(self))

    def on_no_edx_video_id(self, block_key):
        """
        Updates error data for the given block.
        """
        self.num_of_videos_without_edx_video_id += 1
        # self.videos_without_edx_video_id.append(unicode(block_key))

    def on_course_not_bound_to_video(self, block_key):
        """
        Updates error data for the given block.
        """
        self.num_of_videos_without_bound_course += 1
        # self.videos_without_bound_course.append(unicode(block_key))


class _VideoErrorStats(object):
    """
    Class for aggregated Video Error data.
    """
    def __init__(self):
        self.total_num_of_courses_with_errors = 0
        self.total_num_of_videos_without_edx_video_id = 0
        self.total_num_of_videos_without_bound_course = 0

        self.stats_by_course = PrettyDefaultDict(_CourseErrorStats)

    def __repr__(self):
        return repr(vars(self))

    def on_no_edx_video_id(self, course_key, block_key):
        """
        Updates error data for the given block.
        """
        self.total_num_of_videos_without_edx_video_id += 1
        if course_key not in self.stats_by_course:
            self.total_num_of_courses_with_errors += 1
        self.stats_by_course[unicode(course_key)].on_no_edx_video_id(block_key)

    def on_course_not_bound_to_video(self, course_key, block_key):
        """
        Updates error data for the given block.
        """
        self.total_num_of_videos_without_bound_course += 1
        if course_key not in self.stats_by_course:
            self.total_num_of_courses_with_errors += 1
        self.stats_by_course[unicode(course_key)].on_course_not_bound_to_video(block_key)
