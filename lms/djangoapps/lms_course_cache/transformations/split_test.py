"""
.
"""
from courseware.access import _has_access_to_course
from openedx.core.lib.course_cache.transformation import CourseStructureTransformation
from .helpers import get_user_partition_groups


class SplitTestTransformation(CourseStructureTransformation):

    @staticmethod
    def check_split_access(split_test_groups, user_groups):
        """
        Check that user has access to specific split test group.
        
        Arguments: 
            split_test_groups (list)
            user_groups (dict[Partition Id: Group])

        Returns:
            bool
        """
        if split_test_groups:
            for partition, group in user_groups.iteritems():
                if group.id in split_test_groups:
                    return True
            return False
        return True

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

        # Check potential previously set values for user_partitions and split_test_partitions
        xblock = xblock_dict[block_structure.root_block_key]
        user_partitions = getattr(xblock, 'user_partitions', [])
        split_test_partitions = getattr(xblock, 'split_test_partition', []) or []
        result_dict[block_structure.root_block_key]['split_test_partition'] = split_test_partitions
        # For each block, check if there is an split_test block. 
        # If split_test is found, check it's user_partition value and get children. 
        # Set split_test_group on each of the children for fast retrival in apply phase. 
        # Add same group to childrens children, because due to structure restrictions first level 
        # children are verticals.
        for block_key in block_structure.topological_traversal():
            xblock = xblock_dict[block_key]
            category = getattr(xblock, 'category', None)
            if category == 'split_test':
                for user_partition in user_partitions: 
                    if user_partition.id == xblock.user_partition_id: 
                        if user_partition not in split_test_partitions:
                            split_test_partitions.append(user_partition)
                        for child in xblock.children:
                            for group in user_partition.groups:
                                child_location = xblock.group_id_to_child.get(unicode(group.id), None)
                                if child_location == child:
                                    result_dict[child]['split_test_groups'] = [group.id]
                                    for component in xblock_dict[child].children:
                                        result_dict[component]['split_test_groups'] = [group.id]
                result_dict[block_structure.root_block_key]['split_test_partition'] = split_test_partitions

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
        user_partitions = block_data[block_structure.root_block_key].get_transformation_data(
            self, 'split_test_partition'
        )
        # If there are no split test user partitions, this transformation is a no-op,
        # so there is nothing to apply.
        if not user_partitions:
            return

        user_groups = get_user_partition_groups(
            course_key, user_partitions, user
        )

        if not _has_access_to_course(user, 'staff', course_key):
            block_structure.remove_block_if(
                lambda block_key: not SplitTestTransformation.check_split_access(
                    block_data[block_key].get_transformation_data(
                        self, 'split_test_groups', default=[]
                    ), user_groups),
                remove_orphans
            )
