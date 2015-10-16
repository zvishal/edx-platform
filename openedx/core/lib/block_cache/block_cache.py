"""
.
"""
from block_structure import BlockStructureFactory
from transformer import BlockStructureTransformers


def get_blocks(root_block_key, transformers, user_info):
    # Load the cached block structure. This will first try to find the exact
    # block in ephemeral storage, then fall back to the root course block it
    # belongs to in ephemeral storage, and then fall back to the root course
    # block stored in permanent storage.
    bcu = BlockCacheUnit.load(root_block_key, transformers)

    # Note that each transform may mutate the 
    for transformer in transformers:
        with bcu.collected_data_for(transformer) as collected_data:
            transformer.transform(user_info, collected_data)

    return bcu.structure



def get_blocks(cache, modulestore, user_info, root_block_key, transformers):
    unregistered_transformers = BlockStructureTransformers.find_unregistered(transformers)
    if unregistered_transformers:
        raise Exception(
            "The following requested transformers are not registered: {}".format(unregistered_transformers)
        )

    # Load the cached block structure.
    root_block_structure = BlockStructureFactory.create_from_cache(root_block_key, cache)

    if not root_block_structure:

        # Create the block structure from the modulestore
        root_block_structure = BlockStructureFactory.create_from_modulestore(root_block_key, modulestore)

        # Collect data from each registered transformer
        for transformer in BlockStructureTransformers.get_registered_transformers():
            root_block_structure.add_transformer(transformer)
            transformer.collect(root_block_structure)

        # Collect all fields that were requested by the transformers
        root_block_structure.collect_requested_xblock_fields()

        # Cache this information
        BlockStructureFactory.serialize_to_cache(root_block_structure, cache)

    # Execute requested transforms on block structure
    for transformer in transformers:
        transformer.transform(user_info, root_block_structure)

    # Prune block structure
    root_block_structure.prune()

    return root_block_structure


def clear_block_cache(cache, root_block_key):
    BlockStructureFactory.remove_from_cache(root_block_key, cache)
