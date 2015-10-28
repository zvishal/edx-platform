"""
...
"""
from courseware.access import _has_access_to_course


class CourseUserInfo(object):
    '''
    A data structure representing a user's presence and role in a given course.
    '''
    def __init__(self, course_key, user):
        '''
        Arguments:
            course_key - TBD.
            user - A User object
        '''
        self.course_key = course_key
        self.user = user
        self._has_staff_access = None

    @property
    def has_staff_access(self):
        '''
        Indicates whether the user has staff access to the specified course
        Returns:
            bool
        '''
        if self._has_staff_access is None:
            self._has_staff_access = _has_access_to_course(self.user, 'staff', self.course_key)
        return self._has_staff_access
