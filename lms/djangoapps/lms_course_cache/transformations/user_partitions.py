"""
...
"""
from courseware.access import _has_access_to_course
from openedx.core.lib.course_cache.transformation import CourseStructureTransformation
from .helpers import get_user_partition_groups


class MergedGroupAccess(object):
    """
    ...
    """

    # TODO 8874: Make it so LmsBlockMixin.merged_group_access use MergedGroupAccess

    def __init__(self, user_partitions, xblock, merged_parent_access_list):
        """
        Arguments:
            user_partitions (list[UserPartition])
            xblock (XBlock)
            merged_parent_access_list (list[MergedGroupAccess])
        """

        # How group access restrictions are represented within an XBlock:
        #   - group_access not defined                           => No group access restrictions.
        #   - For each partition:
        #       - partition.id not in group_access               => All groups have access for this partition
        #       - group_access[partition_id] is None             => All groups have access for this partition
        #       - group_access[partition_id] == []               => All groups have access for this partition
        #       - group_access[partition_id] == [group1..groupN] => groups 1..N have access for this partition
        #
        # We internally represent the restrictions in a simplified way:
        #   - self._access == {}                                 => No group access restrictions.
        #   - For each partition:
        #       - partition.id not in _access                    => All groups have access for this partition
        #       - _access[partition_id] == set()                 => No groups have access for this partition
        #       - _access[partition_id] == set(group1..groupN)   => groups 1..N have access for this partition
        #
        # Note that a user must have access to all partitions in group_access
        # or _access in order to access a block.

        block_group_access = getattr(xblock, 'group_access', {})
        self._access = {}  # { partition.id: set(IDs of groups that can access partition }

        for partition in user_partitions:

            # Within this loop, None <=> Universe set <=> "No access restriction"

            block_group_ids = set(block_group_access.get(partition.id, [])) or None
            parents_group_ids = [
                merged_parent_access._access[partition.id]
                for merged_parent_access in merged_parent_access_list
                if partition.id in merged_parent_access._access
            ]
            merged_parent_group_ids = (
                set().union(*parents_group_ids) if parents_group_ids != []
                else None
            )
            merged_group_ids = MergedGroupAccess._intersection(block_group_ids, merged_parent_group_ids)
            if merged_group_ids is not None:
                self._access[partition.id] = merged_group_ids

    @staticmethod
    def _intersection(*sets):
        """
        Compute an intersection of sets, interpreting None as the Universe set.

        This makes __init__ a bit more elegant.

        Arguments:
            sets (list[set or None]), where None represents the Universe set.

        Returns:
            set or None, where None represents the Universe set.
        """
        non_universe_sets = [set_ for set_ in sets if set_ is not None]
        if non_universe_sets:
            first, rest = non_universe_sets[0], non_universe_sets[1:]
            return first.intersection(*rest)
        else:
            return None

    def check_group_access(self, user_groups):
        """
        Arguments:
            dict[int: Group]: Given a user, a mapping from user partition IDs
                to the group to which the user belongs in each partition.

        Returns:
            bool: Whether said user has group access.
        """
        for partition_id, allowed_group_ids in self._access.iteritems():

            # If the user is not assigned to a group for this partition, deny access.
            # TODO 8874: Ensure that denying access to users who aren't in a group is the correct action.
            if partition_id not in user_groups:
                return False

            # If the user belongs to one of the allowed groups for this partition,
            # then move and and check the next partition.
            elif user_groups[partition_id].id in allowed_group_ids:
                continue

            # Else, deny access.
            else:
                return False

        # If the user has access for every partition, grant access.
        else:
            return True

class UserPartitionTransformation(CourseStructureTransformation):
    """
    ...
    """

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

        # TODO 8874: Make it so user_partitions is stored with the entire course, not just the root block, because this will break if we request a subtree.
        # Because user partitions are course-wide, only store data for them on
        # the root block.
        xblock = xblock_dict[block_structure.root_block_key]
        user_partitions = getattr(xblock, 'user_partitions', []) or []
        result_dict[block_structure.root_block_key]['user_partitions'] = user_partitions

        # If there are no user partitions, this transformation is a no-op,
        # so there is nothing to collect.
        if not user_partitions:
            return result_dict

        # For each block, compute merged group access. Because this is a
        # topological sort, we know a block's parents are guaranteed to
        # already have merged group access computed before the block itself.
        for block_key in block_structure.topological_traversal():
            xblock = xblock_dict[block_key]
            parent_keys = block_structure.get_parents(block_key)
            parent_access = [result_dict[parent_key]['merged_group_access'] for parent_key in parent_keys]
            merged_group_access = MergedGroupAccess(user_partitions, xblock, parent_access)
            result_dict[block_key]['merged_group_access'] = merged_group_access

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
        # TODO 8874: Factor out functionality of UserPartitionTransformation.apply and access._has_group_access into a common utility function.
        # TODO 8874: Make it so user_partitions is stored with the entire course, not just the root block, because this will break if we request a subtree.
        user_partitions = block_data[block_structure.root_block_key].get_transformation_data(
            self, 'user_partitions'
        )

        # If there are no user partitions, this transformation is a no-op,
        # so there is nothing to apply.
        if not user_partitions:
            return

        user_groups = get_user_partition_groups(
            course_key, user_partitions, user
        )
        if not _has_access_to_course(user, 'staff', course_key):
            block_structure.remove_block_if(
                lambda block_key: not block_data[block_key].get_transformation_data(
                    self, 'merged_group_access'
                ).check_group_access(user_groups),
                remove_orphans
            )


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

        xblock = xblock_dict[block_structure.root_block_key]

        # For each block, compute merged group access. Because this is a
        # topological sort, we know a block's parents are guaranteed to
        # already have merged group access computed before the block itself.
        for block_key in block_structure.topological_traversal():
            xblock = xblock_dict[block_key]
            result_dict[block_key]['content_library_children'] = []
            if getattr(xblock, 'display_name', None):
                if getattr(xblock, 'display_name') == u'Library':
                    children = [child.location for child in xblock_dict[xblock.children[0]].get_children()]
                    result_dict[block_key]['content_library_children'] =  children


        return result_dict

    def apply(self, user, course_key, block_structure, block_data, remove_orphans):
        print user
        print 'apply'
        """
        Mutates block_structure and block_data based on the given user_info.

        Arguments:
            user (User)
            course_key (CourseKey)
            block_structure (CourseBlockStructure)
            block_data (dict[UsageKey: CourseBlockData]).
            remove_orphans (bool)
        """
    #    print block_data
        for block_key, block_value in block_data.iteritems():
            children = block_data[block_key].get_transformation_data(self, 'content_library_children')
#            print block_structure.get_children(block_key)
            xblock = block_data[block_key]
            print children
            if children:
                library = block_structure.get_children(block_key)
                for lib in library:
                    print lib
                for child in children:
                    print '--------child-----------'
                    print dir(child)



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
