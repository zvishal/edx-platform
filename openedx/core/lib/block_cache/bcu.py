"""
This is the module that deals with the storage of data associated with the
Block Transforms framework.

# GOALS

A number of the classes in this module only make sense in the context of the
following goals:

1. Data gathered in the collect() phase should be stored by Transformer.

   Motivation:
   * Transformers can be used in various combinations for different end points.
     For example, in serving the course structure to something like Insights, 
     we need not apply any student-specific transforms like permissions or user
     partitions.
   * We expect to add new Transformers from time to time. When deploying a new
     Transformer, we should be able to run the collect() phase on all courses
     for just that one Transformer, rather than having to re-process every
     Transformer for every course.
   * We want to be able to track collected data size by Transformer.

2. Keep the stored data as small as possible.

   Motivation:
   * The large size of course structure documents in Split-Mongo has been a
     performance headache.
   * Many uses for this framework are "a mile wide, an inch deep" types of
     queries on the course, where we might need to hit thousands of XBlock
     nodes, but only want a small handful of fields.
   * We eventually want to be able to plug LMS FieldData to use this system,
     meaning that it has to be fast and light for serving single blocks.

3. Avoid modulestore access during the transform() phase.

   Motivation:
   * It's slow.
   * It's complex.
   * It makes it harder to test.
   * We want to kill it: https://openedx.atlassian.net/wiki/x/moKp

Storing things naively a per-block basis was prohibitively expensive in terms of
space consumption, resulting in about 1K/block uncompressed, and 250 bytes/block
compressed. On a 4K block course, that was 4MB of data -- and that's with a
limited number of transformers. In many cases, the block keys themselves were
larger than the data collected for them. Also, splitting things on a per-block
basis meant that compression was far less efficient, since the collected data
often has really low cardinality across blocks (e.g. due dates, boolean fields,
problem types).

# DATA OVERVIEW

Collected data often falls into one of handful of categories:

1. Present for all blocks, with different data
     - e.g. display_name
2. Present for all blocks, but limited to a narrow range of possible values
     - e.g. category
3. Only applicable to a small subset of blocks, and null everywhere else
     - e.g. weight, video-related fields, etc.


# HIGH LEVEL DESIGN

We start with a `BlockCacheUnit`. This repesents all the data that a given set
of Transformers need for a given set of blocks in the course. A `BlockCacheUnit`
has in it:

* block_structure (BlockStructure) - holds parent/child relations
* 

BlockCacheUnit:
* has the BlockStructure
* keeps track of BlockFieldValues
* bundles together a CollectedData for each Transformer as needed

CollectedData
* has a reference to the BCU's structure
* has an xblock_field_values (BlockFieldValues)
* has an transformer_field_values (BlockFieldValues)
* has free-form transformer_data

BlockFieldValues
* use a BlockIndexMapping
* stores many fields
* can't instantiate/serialize itself, BCU does it because it has the BIM

"""

import itertools

class BlockCacheUnit(object):
    """
    Responsibilities:

    1. Manage storage, retrieval, and caching of all Transform collected data.
    2. Assemble CollectedData for a given Transformer during transform()

    # And honestly, the storage part of #1 is probably going to get farmed off.

    A BCU has three parts:

    1. A BlockStructure (mutatable)
    3. 0-n CollectedData from Transformers (immutable)
    4. 0-n CollectedData that are XBlock fields (mutable)

    What you really want is to be able to give a packaged view for a particular
    Transformer who wants a certain set of things:

    structure
    collected data about my transform
    fields I requested

    When we're figuring out what BCU to instantiate, we need:

    root, depth
    list of transforms
    list of XB fields (combined from transforms)

    Am I allowed to ask for other transformer's data?


    Args:
    structure = BlockStructure
    xblock_values = BlockFieldValues
    transforms_to_block_values = {transform_id: BlockFieldValues}
    transforms_to_data = {transform_id: top level transform data}

    """
    def __init__(self, structure, xblock_field_values, transformers_to_field_values, transformers_to_data):
        # BlockStructure holding relations for all block keys in this
        # BlockCacheUnit. This will mutate between transforms.
        self._structure = structure
        self._mapping = BlockIndexMapping(structure.get_block_keys())

        # BlockFieldData with all XBlock fields we're aware of. This will mutate
        # between transforms.
        self._xblock_field_values = xblock_field_values

        # {transformer.name() -> BlockFieldValues}. Each entry is private to a
        # Transformer.
        self._transformers_to_field_values = transformers_to_field_values

        # Top level data for each transform. {transformer.name() -> data}
        self._transformers_to_data = transformers_to_data

    def data_for_transform(self, transformer):
        """
        Give a Transformer a CollectionData with just the information they're
        supposed to have access to during the transform phase.
        """
        return CollectedData(
            self._structure,
            self._xblock_field_values.slice(transformer.xblock_fields),
            self._transforms_to_field_values[transformer.name],
            self._transforms_to_data[transformer.name]
        )

    def data_for_collect(self, transformer):
        """

        """
        ro_structure = ReadOnlyWrapper(
            self._structure,
            ['add_relation', 'prune', 'remove_block', 'remove_block_if']
        )
        ro_xblock_field_values = ReadOnlyWrapper(
            self._xblock_field_values.slice(transformer.xblock_fields),
            ['set']
        )
        return CollectedData(
            ro_structure,
            ro_xblock_field_values,
            self._transforms_to_field_values[transformer.name],
            self._transforms_to_data[transformer.name]
        )

    def set_transformer_data(self, transformer, data):
        """What to do with the version information? We need it somewhere."""
        self._transformers_to_data[transformer.name] = data

    def init_field_values_for_transformer(self, transformer, fields):
        blank_field_values = BlockFieldValues.create_blank(self._mapping, fields)
        self._transformers_to_field_values[transformer.name] = blank_field_values
        return blank_field_values

    def subset(self, new_root_key):
        """
        Strategy for this:
            1. Ask the BlockStructure for sub_structure(new_root_key)
            2. Have it essentially create a new version of itself by copying
               all the relations as they exist, doing DFS with cycle guard
            3. Use that as the basis for a new set of block keys.
            4. Create a BlockFieldValues.slice_by_keys()
            5. Preserve the _transformers_to_data
        """
        pass

    @classmethod
    def load_from_modulestore(cls, modulestore, transformers, root_key, version):
        """
        Given a modulestore and a set of transformers, populate all the data
        needed to construct a BCU that we can then pass through various
        Transformer collect() methods.

        This method will completely initialize 
        """
        with modulestore.bulk_operations(root_key.course_key):
            # Initialize the structure
            root_xblock = modulestore.get_item(root_key, depth=None)
            structure = BlockStructure.load_from_xblock(root_xblock)

            # Now the XBlock Fields
            index_mapping = BlockIndexMapping(structure.get_block_keys())
            requested_xblock_fields = {
                itertools.chain(tfmr.xblock_fields for tfmr in transformers)
            }
            xblock_field_values = BlockFieldValues(
                index_mapping,
                {
                    field: [getattr(modulestore.get_item(block_key), field, None) for block_key in index_mapping]
                    for field in requested_xblock_fields
                }
            )

        return cls(structure, xblock_field_values)


class CollectionData(object):
    """
    This represents all the data that a Transformer will write out during its
    collect() phase and later read during its transform() phase. It essentially
    serves as a limited view of data residing in a BlockCacheUnit. Transformers
    should call `BlockCacheUnit.collected_data_for()` instead of instantiating
    this class directly.

    Because this class represents a Transformer's data usage, it gives us a
    good place to log how much data each Transformer is using and when it's
    asking for it.
    """
    def __init__(self, structure, xblock_field_values, field_values, data):
        """
        """
        self._structure = structure
        self._xblock_field_values = xblock_field_values
        self._field_values = field_values
        self._data = data

    @property
    def structure(self):
        return self._structure
    
    @property
    def xblock_field_values(self):
        return self._xblock_field_values
    
    @property
    def field_values(self):
        return self._field_values

    @property
    def data(self):
        return self._data


class WriteError(Exception):
    pass


class ReadOnlyWrapper(object):
    """
    Basically a proxy class that intercepts method calls that would alter state.
    """

    def __init__(self, real_obj, write_methods):
        self._real_obj = real_obj
        self._write_methods = set(write_methods)

    def __getattribute__(self, name):
        if name in self._write_methods:
            raise WriteError("Cannot use {} method during collect phase.")
        return getattr(self._real_obj, name)

    def __repr__(self):
        return "ReadOnlyWrapper({!r}, {!r})".format(self._real_obj, self._write_methods)

    def __unicode__(self):
        return u"ReadOnlyWrapper on {}".format(self._real_obj)


class BlockFieldValues(object):
    """

    """
    def __init__(self, block_index_mapping, fields_to_value_lists):
        self._block_index_mapping = block_index_mapping
        self._fields_to_value_lists = fields_to_value_lists

    @classmethod
    def create_blank(cls, block_index_mapping, fields):
        return cls(
            block_index_mapping,
            {
                field: [None for __ in xrange(len(block_index_mapping))]
                for field in fields
            }
        )

    @property
    def fields(self):
        """Sorted list of fields available in this BlockFieldValues."""
        return sorted(self._fields_to_value_lists.keys())

    def slice_by_fields(self, fields):
        """
        Return a cheaply sliced BlockFieldValues with a subset of the data.

        Note that a sliced BlockFieldValues still points to the same lists as
        the original it was taken from. This is mostly for helping folks to keep
        track of their real field dependencies explicitly -- so that we can give
        a Transformer precisely what it declared it needed, and error early if
        it tries to access something it hasn't asked for. It is *not* a way to
        make a safe copy.
        """
        return BlockFieldValues(
            self._block_index_mapping,
            {
                field: value_list
                for field, value_list in self._fields_to_value_lists.items()
                if field in fields
            }
        )

    def slice_by_keys(self, new_index_mapping):
        raise NotImplementedError
        return BlockFieldValues(
            new_index_mapping,
            {
                field: value_list
            }            
        )

    def get(self, field, block_key):
        index = self._block_index_mapping.index_for(block_key)
        value_list = self._value_list_for_field(field)
        return value_list[index]

    def set(self, field, block_key, value):
        index = self._block_index_mapping.index_for(block_key)
        value_list = self._value_list_for_field(field)
        value_list[index] = value

    def __getitem__(self, block_key):
        """Return a dict of field names to values."""
        index = self._block_index_mapping.index_for(block_key)
        return {
            field: value_list[index]
            for field, value_list
            in self._fields_to_value_lists.items()
        }

    def _value_list_for_field(self, field):
        try:
            return self._fields_to_value_lists[field]
        except KeyError:
            raise KeyError(
                "{} has no field '{}' (fields: {})".format(self, field, self.fields)
            )


class BlockIndexMapping(object):
    """
    Given a list of block_keys, this class will hold a mapping of
    block_key -> list index.

    It is expected that instances of this are shared among many objects, and you
    should *not* mutate any data structures after __init__().
    """
    def __init__(self, block_keys):
        self._ordered_block_keys = sorted(block_keys)
        counter = itertools.count(0)
        self._block_keys_to_indexes = {
            block_key: counter.next()
            for block_key in self._ordered_block_keys
        }

    def __iter__(self):
        return iter(self._ordered_block_keys)

    def index_for(self, key):
        try:
            return self._block_keys_to_indexes[key]
        except KeyError as key_err:
            raise KeyError("{} has no index mapping for key {}".format(self, key))
