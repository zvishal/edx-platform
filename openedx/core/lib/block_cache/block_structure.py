"""
...
"""
from collections import defaultdict
from graph_traversals import traverse_topologically, traverse_post_order
from logging import getLogger

from openedx.core.lib.cache_utils import zpickle, zunpickle
from transformer import BlockStructureTransformers


logger = getLogger(__name__)  # pylint: disable=C0103


class BlockRelations(object):
    def __init__(self):
        self.parents = []
        self.children = []


class BlockStructure(object):
    """
    A class to encapsulate a structure of blocks, a directed acyclic graph of blocks.
    """
    def __init__(self, root_block_key):
        self.root_block_key = root_block_key
        self._block_relations = defaultdict(BlockRelations)
        self._add_block(self._block_relations, root_block_key)

    def __iter__(self):
        return self.topological_traversal()

    def __contains__(self, usage_key):
        return usage_key in self._block_relations

    def add_relation(self, parent_key, child_key):
        self._add_relation(self._block_relations, parent_key, child_key)

    def get_parents(self, usage_key):
        return self._block_relations[usage_key].parents if self.has_block(usage_key) else []

    def get_children(self, usage_key):
        return self._block_relations[usage_key].children if self.has_block(usage_key) else []

    def has_block(self, usage_key):
        return usage_key in self._block_relations

    def get_block_keys(self):
        return self._block_relations.iterkeys()

    def topological_traversal(self, **kwargs):
        return traverse_topologically(
            start_node=self.root_block_key,
            get_parents=self.get_parents,
            get_children=self.get_children,
            **kwargs
        )

    def post_order_traversal(self, **kwargs):
        return traverse_post_order(
            start_node=self.root_block_key,
            get_children=self.get_children,
            **kwargs
        )

    def prune(self):
        # create a new block relations map with only those blocks that are still linked
        pruned_block_relations = defaultdict(BlockRelations)
        old_block_relations = self._block_relations

        def do_for_each_block(block_key):
            if block_key in old_block_relations:
                self._add_block(pruned_block_relations, block_key)

                for child in old_block_relations[block_key].children:
                    if child in pruned_block_relations:
                        self._add_relation(pruned_block_relations, block_key, child)

        list(self.post_order_traversal(get_result=do_for_each_block))
        self._block_relations = pruned_block_relations

    @classmethod
    def _add_relation(cls, block_relations, parent_key, child_key):
        block_relations[child_key].parents.append(parent_key)
        block_relations[parent_key].children.append(child_key)

    @classmethod
    def _add_block(cls, block_relations, block_key):
        _ = block_relations[block_key]


    def remove_block(self, usage_key, keep_descendants):
        children = self._block_relations[usage_key].children
        parents = self._block_relations[usage_key].parents

        # Remove block from its children.
        for child in children:
            self._block_relations[child].parents.remove(usage_key)

        # Remove block from its parents.
        for parent in parents:
            self._block_relations[parent].children.remove(usage_key)

        # Remove block.
        self._block_relations.pop(usage_key, None)
        self._block_data_map.pop(usage_key, None)

        # Recreate the graph connections if descendants are to be kept.
        if keep_descendants:
            [self.add_relation(parent, child) for child in children for parent in parents]

    def remove_block_if(self, removal_condition, keep_descendants=False, **kwargs):
        def predicate(block_key):
            if removal_condition(block_key):
                self.remove_block(block_key, keep_descendants)
                return False
            return True
        list(self.topological_traversal(predicate=predicate, **kwargs))

    @classmethod
    def load_from_xblock(cls, root_xblock):
        root_block_key = root_xblock.location
        block_structure = BlockStructure(root_block_key)
        blocks_visited = set()

        def build_block_structure(xblock):
            """
            Helper function to recursively walk block structure
            """
            if xblock.location in blocks_visited:
                return
            blocks_visited.add(xblock.location)
            block_structure.add_xblock(xblock)
            for child in xblock.get_children():
                block_structure.add_relation(xblock.location, child.location)
                build_block_structure(child)

        build_block_structure(root_xblock)

        return block_structure
