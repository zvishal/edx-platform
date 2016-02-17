"""
General class for Test migrations.For more information visit at
https://www.caktusgroup.com/blog/2016/02/02/writing-unit-tests-django-migrations/
"""
# pylint: disable=redefined-outer-name

from django.test import TransactionTestCase
from django.db.migrations.executor import MigrationExecutor
from django.db import connection


class TestMigrationsForward(TransactionTestCase):
    """ Base class for testing forward migrations. """
    migrate_from = None
    migrate_to = None
    app = None

    def setUp(self, execute_forward=True):
        super(TestMigrationsForward, self).setUp()
        if execute_forward:
            self.checkData(self.migrate_from)
            self.execute_migration(self.migrate_from, self.migrate_to)

    def execute_migration(self, previous, next):
        """
        Execute migration from state to another.
        """
        # Reverse to the original migration
        executor.migrate(previous)

        self.setUpBeforeMigration(old_apps)

        # Run the migration to test
        executor.migrate(next)

        self.apps = executor.loader.project_state(next).apps

    def checkData(self, migration_state):
        """
        Migrate_from, migrate_to and app variables must be define first.
        """
        assert self.migrate_from and self.migrate_to, \
            "TestCase '{}' must define migrate_from and migrate_from properties".format(type(self).__name__)
        assert self.app, "app must be define in the TestCase"
        self.migrate_from = [(self.app, self.migrate_from)]
        self.migrate_to = [(self.app, self.migrate_to)]
        executor = MigrationExecutor(connection)
        old_apps = executor.loader.project_state(migration_state).apps

    def setUpBeforeMigration(self, apps):  # pylint: disable=invalid-name
        """
        Will run before befor migration using config field migrate_from.
        Implemented in derived class.
        """
        pass


class TestMigrationsBackward(TestMigrationsForward):
    """ Base class for testing backward migrations. """

    def setUp(self):
        super(TestMigrationsBackward, self).setUp(execute_forward=False)
        self.checkData(self.migrate_to)
        self.execute_migration(self.migrate_to, self.migrate_from)

