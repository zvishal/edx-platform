"""
...
"""
import json
from courseware.access import _has_access_to_course
from courseware.models import StudentModule
from opaque_keys.edx.locator import BlockUsageLocator
from openedx.core.lib.course_cache.transformation import CourseStructureTransformation


class ContentLibraryTransformation(CourseStructureTransformation):

    def collect(self, course_key, block_structure, xblock_dict):
        """
        Computes any information for each XBlock that's necessary to execute
        this transformation's apply method.

        Arguments:
            course_key (CourseKey)
            block_structure (CourseBlockStructure)
            xblock_dict (dict[UsageKey: XBlock])

        Returns:
            dict[UsageKey: dict]
        """
        result_dict = {block_key: {} for block_key in block_structure.get_block_keys()}

        # For each block check if block is library_content. 
        # If library_content add children array to content_library_children field
        for block_key in block_structure.topological_traversal():
            xblock = xblock_dict[block_key]
            result_dict[block_key]['content_library_children'] = []
            if getattr(xblock, 'category', None) == 'library_content':
                result_dict[block_key]['content_library_children'] =  xblock.children

        return result_dict

    def apply(self, user, course_key, block_structure, block_data, remove_orphans):
        """
        Mutates block_structure and block_data based on the given user_info.

        Arguments:
            user (User)
            course_key (CourseKey)
            block_structure (CourseBlockStructure)
            block_data (dict[UsageKey: CourseBlockData]).
            remove_orphans (bool)
        """
        def check_child_removal(block_key):
            """
            Check if selected block should be removed. 
            Block is removed if it is part of library_content, but has not been selected 
            for current user.
            """
            if block_key not in children:
                return False
            if block_key in children and block_key in selected_children:
                return False
            return True

        children = []
        selected_children = []
        for block_key, block_value in block_data.iteritems():
            library_children = block_data[block_key].get_transformation_data(self, 'content_library_children')
            children.extend(library_children)
            if library_children:
                # Retrieve "selected" json from LMS MySQL database.
                modules = StudentModule.objects.filter(
                    student=user,
                    course_id=course_key,
                    module_state_key=block_key, 
                    state__contains='"selected": [['
                )
                for module in modules:
                    module_state = module.state
                    state_dict = json.loads(module_state)
                    # Check all selected entries for this user on selected library.
                    # Add all selected to selected_children list.
                    for state in state_dict['selected']:                        
                        usage_key = BlockUsageLocator(
                            course_key, block_type=state[0], block_id=state[1]
                        )
                        if usage_key in library_children:
                            selected_children.append(usage_key)

        # Check and remove all non-selected children from course structure.
        if not _has_access_to_course(user, 'staff', course_key):
            block_structure.remove_block_if(
                check_child_removal,
                remove_orphans
            )   
