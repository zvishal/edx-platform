"""
General class for Test migrations.Based off an implementation provided at
https://www.caktusgroup.com/blog/2016/02/02/writing-unit-tests-django-migrations/
"""
# pylint: disable=redefined-outer-name

from django.test import TransactionTestCase
from django.db.migrations.executor import MigrationExecutor
from django.db import connection


class TestMigrations(TransactionTestCase):
    """ Base class for testing migrations. """
    migrate_from = None
    migrate_to = None
    app = None

    def setUp(self):
        super(TestMigrations, self).setUp()
        self.check_data()

    def execute_migration(self, previous, next):
        """
        Execute migration from state to another.
        """
        # Reverse to the original migration
        self.executor.migrate(previous)

        self.setUpBeforeMigration()

        # Run the migration to test
        self.executor.migrate(next)

    def check_data(self):
        """
        Migrate_from, migrate_to and app variables must be define first.
        """
        assert self.migrate_from and self.migrate_to, \
            "TestCase '{}' must define migrate_from and migrate_from properties".format(type(self).__name__)
        assert self.app, "app must be define in the TestCase"
        self.migrate_from = [(self.app, self.migrate_from)]
        self.migrate_to = [(self.app, self.migrate_to)]
        self.executor = MigrationExecutor(connection)

    def setUpBeforeMigration(self):  # pylint: disable=invalid-name
        """
        Will run before befor migration using config field migrate_from.
        Implemented in derived class.
        """
        pass

    def migrate_forwards(self):
        """ Execute migration to forward state. """
        self.execute_migration(self.migrate_from, self.migrate_to)

    def migrate_backwards(self):
        """ Execute migration to backward state. """
        self.execute_migration(self.migrate_to, self.migrate_from)

