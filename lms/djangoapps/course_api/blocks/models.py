"""

"""
import logging

from django.db import models, transaction, IntegrityError
from model_utils.models import TimeStampedModel
import django.core.cache

from opaque_keys.edx.keys import CourseKey

from openedx.core.lib.cache_utils import zpickle, zunpickle
from xmodule_django.models import CourseKeyField

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class CollectedContentDataCache(object):
    """
    This class presents a basic get/set cache interface for use by the block
    cache library. It has two layers, short term caching via memcached, and long
    term data storage using CollectedCourseData. If you are reading this
    information, you should generally do so from this class, and not
    CollectedCourseData.

    Because it is intended to eventually allow more granular access, this class
    thinks in term of usage block keys, not course keys.
    """
    def __init__(self, store=None, cache=None):
        self._store = store or modulestore()
        self._cache = cache or django.core.cache.cache  # short term cache

    def get(self, root_block_key, collector, version):
        """
        Return
        """
        # Just for now. Eventually, we'll understand other things.
        if root_block_key.block_type not in ['course', 'library']:
            raise KeyError(
                "We currently only support root blocks: {}".format(root_block_key)
            )

        # Now see if we've already pushed this into our ephemeral cache.
        cache_key = self._cache_key(collector, version, root_block_key)
        zp_collected_course_data = self._cache.get(cache_key)
        if zp_collected_course_data is not None:
            return zunpickle(zp_collected_course_data)

        # If we've reached this point, we're falling back to permanent storage.
        # Our permanent storage only stores things at the course_key level.
        course_key = root_block_key.course_key
        collected_course_data = CollectedCourseData.get_data_for_course(
           collector, collector_version, course_key
        )
        self._cache.set(cache_key, zpickle(collected_course_data))

        return collected_course_data

    def _cache_key(self, root_key, collector, version):
        return "CollectedCourseDataCache.{}.{}.{}".format(
            root_key, collector, version
        )


class CollectedCourseData(TimeStampedModel):
    """
    Every time a course is published, we update this model. Please use the
    class methods for queries and do not access the model directly. There are
    subtleties in terms of data integrity and mid-deploy/rollback states that
    are not immediately obvious, and that the methods on this class will try
    to insulate you from.

    We're storing the course data by course_id instead of by its root block.
    This is because:

      * All the more granular block-level caching is going to happen in
        memcached anyway.
      * From an admin/monitoring point of view, it makes things easier, since
        the IDs thrown around during publishing are CourseKeys.
      * When we have to rebuild data, it's going to almost always be at the
        course level.
    """
    course_id = CourseKeyField(max_length=255, db_index=True)

    # Unique identifier to differentiate published versions of content. In
    # practice, this would be `course.subtree_edited_on.isoformat()`, since
    # our Old Mongo storage doesn't support explicit versions like Split does.
    content_version = models.CharField(max_length=255, db_index=True)

    # ID of the thing doing collecting, which will may one day be mostly
    # transformers, but for now is a centralized entity. This thing "owns" the
    # data.
    collector = models.CharField(max_length=255)

    # The point of this is so that if there's a code change that alters the
    # serialization format in a backwards incompatible way, we can increment
    # this field. This also allows us to track in data which version created
    # what, and to clear out data for old versions
    collector_version = models.IntegerField()

    encoding_type = models.CharField(max_length=20)

    data = models.TextField()

    unique_together = (
        ("course_id", "collector", "collector_version"),
    )

    @classmethod
    def get_published_version(cls, course_id):
        """Return the version that"""
        pass


    @classmethod
    def get_data_for_course(cls, root_block_key):
        """
        Creates and returns a block structure from the modulestore
        starting at the given root_block_key.

        Arguments:
            root_block_key (UsageKey) - The usage_key for the root
                of the block structure that is to be created.

            modulestore (ModuleStoreRead) - The modulestore that
                contains the data for the xBlocks within the block
                structure starting at root_block_key.

        Returns:
            BlockStructureXBlockData - The created block structure
                with instantiated xBlocks from the given modulestore
                starting at root_block_key.
        """
        # Create block structure.
        block_structure = BlockStructureXBlockData(root_block_key)

        # Create internal set of blocks visited to use when recursing.
        blocks_visited = set()

        def build_block_structure(xblock):
            """
            Recursively update the block structure with the given xBlock
            and its descendants.
            """
            # Check if the xblock was already visited (can happen in
            # DAGs).
            if xblock.location in blocks_visited:
                return

            # Add the xBlock.
            blocks_visited.add(xblock.location)
            block_structure._add_xblock(xblock.location, xblock)

            # Add relations with its children and recurse.
            for child in xblock.get_children():
                block_structure._add_relation(xblock.location, child.location)
                build_block_structure(child)

        root_xblock = self._store.get_item(root_block_key, depth=None)
        build_block_structure(root_xblock)
        return block_structure



#   @classmethod
#   def get_data_for_course(cls, course_key, collector, collector_version):
#       """
#       Return data
#
#       """
#       # Get the most recently modified entry for this collector+version on
#       # this course. This will throw a DoesNotExist exception if it doesn't
#       # find any matching entries (the get() at the end).
#       collected_data = cls.objects.filter(
#           course_id=course_key, collector=collector, collector_version=collector_version
#       ).order_by('-modified')[:1].get()
#
#       return zunpickle(collected_data.data.decode('base64'))


    @classmethod
    def set_data_for_course(cls, course_key, content_version, collector, collector_version, data):
        """
        Set data for a particular collector for this course.

        The quirkiness of this function comes what happens in partially deployed
        states, where we have multiple active versions of the collector. For
        instance:

        1. Collector C1-v1 creates an entry. T1-v1 uses this to serve requests.
        2. We deploy C1-v2 to our worker machines.
        3. There is a course publish.
        4. But T1-v1 hasn't been cycled out of the web pool yet.

        That leaves us in a very strange place because we'd have web processes
        (T1-v1) that don't know how to read v2 yet, but we have worker machines
        that are no longer writing v1. While deploys are typically quick, it
        could also take hours if we're cautiously rolling out something big.
        Worse of all, if we rolled back at this point, there would be a lot of
        v2 data sitting around that v1 couldn't handle.

        So to prevent this situation, when setting collector data, we will do
        the following:

        1. All collectors will write both their current version as well as their
           previous version. E.g. C1 will write both v1 and v2 data.
        2. When this method cleans up old entries, it will only delete entries
           that are < (collector_version - 1).

        TODO: Create a "set_many" version when we actually have multiple
              collectors.
        """
        # See docstring above for why we're deleting just these entries.
        old_entries = cls.objects.filter(course_id=course_key, collector=collector)
        old_entries.filter(collector_version__lt=(collector_version - 1)).delete()

        # Add or update our new row of course data -- an update could mean a
        # code fix needs to be applied.
        try:
            # This kills me, but binary fields don't exist until Django 1.6
            encoded_data = zpickle(data).encode('base64')
            collector_data, _created = cls.objects.get_or_create(
                course_id=course_key,
                content_version=content_version,
                collector=collector,
                collector_version=collector_version,
                defaults={
                    'encoding_type': 'zpickle',
                    'data': encoded_data
                }
            )
            logger.info("argh")
        except IntegrityError as err:
            # Another process added this, but as long as the content_version is
            # the same, we're okay with that. Log, but move on.
            msg = (
                "IntegrityErrow when updating CollectedCourseData for "
                "course_key=%s, content_version=%s, collector=%s, collector_version=%s"
            )
            logger.warning(msg, course_key, content_version, collector, collector_version)
