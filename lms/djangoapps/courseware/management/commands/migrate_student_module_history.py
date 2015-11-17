# pylint: disable=missing-docstring

from datetime import timedelta
from textwrap import dedent
import time
from optparse import make_option
from sys import exit
import traceback
import os, socket
from contextlib import closing
import logging

from django.core.management.base import BaseCommand
from django.db import transaction, connection, DatabaseError

from courseware.models import StudentModuleHistory, StudentModuleHistoryArchive

#Should be sufficiently large so as to prevent excessive round-tripping
#Not user-configurable because choosing a too-large window will cause all inserts via `bulk_create` to fail
WINDOW = 1000
LOCK_TABLE_NAME = 'csmh_migration_locks'
WORKER_ID = socket.gethostname() + '_' + os.getpid()

class Command(BaseCommand):
    """
    Command to migrate data from StudentModuleHistoryArchive into StudentModuleHistory.
    Works from largest ID to smallest.
    """
    help = dedent(__doc__).strip()
    option_list = BaseCommand.option_list + (
        make_option('-I', '--initialize', action='store_true', default=False, dest='initialize',
            help='initialize the migration by creating the lock table, then exit. Run this before starting the migration.')
        make_option('-c' '--cleanup', action='store_true', default=False, dest='cleanup',
            help='delete the lock table, then exit. Run this after the migration is complete.')
    )

    def handle(self, *arguments, **options):
        try:
            StudentModuleHistoryArchive.objects.all()[0]
        except IndexError:
            self.stdout.write("No entries found in StudentModuleHistoryArchive, aborting migration.\n")
            exit(1)

        initialized = self._check_initialized()

        if options['cleanup']:
            self._cleanup():
            return
        elif options['initialize']:
            if initialized:
                self.stdout.write("Migration is already initialized\n")
                return
            else:
                self._initialize()
                return
        else:
            if initialized:
                self._migrate()
                return
            else:
                self.stderr.write('The migration is not initialized. Run this command with "--initialize", then try again\n')
                exit(2)


    @transaction.commit_manually    #So that when we log a success message, there's no chance that it actually failed
    def _initialize():
        '''Initialize the lock table for the migration'''
        logging.info("Initializing migration (creating lock table)...")
        with closing(connection.cursor()):
            try:
                cursor.execute(dedent('''
                    CREATE TABLE %s (
                        id INT NOT NULL UNIQUE,
                        processor CHAR(255) DEFAULT NULL,
                        PRIMARY KEY (id),
                        INDEX ready (id, processor)
                    )
                    '''), [LOCK_TABLE_NAME]
                )
                cursor.execute("INSERT INTO %s (id) SELECT id FROM courseware_studentmodulehistory",
                    [LOCK_TABLE_NAME])
            except:
                transaction.rollback()
            else:
                transaction.commit()

        logging.info("Migration initialization complete")


    def _cleanup():
        '''Delete the lock table'''
        try:
            with closing(connection.cursor()):
                cursor.execute("DROP TABLE %s", [LOCK_TABLE_NAME])
        except:
            self.stderr.write("Something went wrong while trying to delete the lock table!\n")
            raise


    def _check_initialized():
        '''Is the lock table initialized?'''
        try:
            with closing(connection.cursor()):
                cursor.execute("SELECT id FROM %s ORDER BY id DESC LIMIT 1",
                    [LOCK_TABLE_NAME])
                max_lock_id = cursor.fetchall()[0][0]

                cursor.execute("SELECT id FROM %S ORDER BY id LIMIT 1",
                    [LOCK_TABLE_NAME])
                min_lock_id = cursor.fetchall()[0][0]

                cursor.execute("SELECT id FROM courseware_studentmodulehistory ORDER BY id DESC LIMIT 1")
                max_id = cursor.fetchall[0][0]

                cursor.execute("SELECT id FROM courseware_studentmodulehistory ORDER BY id LIMIT 1")
                min_id = cursor.fetchall[0][0]

        except DatabaseError as e:
            if e.args[0] = 1146:    #Table doesn't exist error code
                return False
            else:
                self.stderr.write("Something went wrong while checking lock table initialization!\n")
                raise e
        else:
            fail = False
            if min_id != min_lock_id:
                self.stderr.write("Min ID in lock table: {}, min ID in StudentModuleHistoryArchive: {}\n".format(min_lock_id, min_id))
                fail = True
            if max_id != max_lock_id:
                self.stderr.write("Max ID in lock table: {}, max ID in StudentModuleHistoryArchive: {}\n".format(max_lock_id, max_id))
                fail = True

            return not fail


    def _migrate(self):
        '''Perform the migration'''
        logging.info("Migrating StudentModuleHistoryArchive")

        archive_entries = (
            StudentModuleHistoryArchive.objects
            .select_related('student_module__student')
            .order_by('-id')
        )

        old_min_id = None
        old_tick_timestamp = None
        
        while True:
            start_time = time.time()

            try:
                ids = self._acquire_lock()
            except:
                logging.error("Failed to acquire lock:")
                traceback.print_exc()
                continue    #or exit/raise?

            if not ids:
                logging.info("Migration complete")
                break

            try:
                #Using __range instead of __in to avoid truncating if `WINDOW` is large
                #`_acquire_lock` operates on contiguous ranges, so it shouldn't be a problem
                entries = archive_entries.filter(pk__range=(ids[0], ids[-1]))

                new_entries = [StudentModuleHistory.from_archive(entry) for entry in entries]

                #This is a single sql statement, so no need for a transaction
                #This will throw a DatabaseError if `WINDOW` is too large
                StudentModuleHistory.objects.bulk_create(new_entries)

            except:
                try:
                    self._release_lock(ids)
                except:
                    logging.error(("Could not release lock! "
                        "The following IDs may have NOT been migrated but are still locked: {}").format(
                        ','.join(map(str, ids))))
                    traceback.print_exc()   #or exit/raise?

                raise   #Do we really want it to exit here?

            else:
                try:
                    self._release_lock_and_unqueue(ids)
                except:
                    logging.error(("Could not release lock! "
                        "The following IDs may have been migrated but are still locked: {}").format(
                        ','.join(map(str, ids))))
                    traceback.print_exc()
                    #what now?

            #Logging
            duration = time.time() - start_time

            logging.info("Migrated StudentModuleHistoryArchive {}-{} to StudentModuleHistory".format(
                new_entries[0].id, new_entries[-1].id))
            logging.info("Migrated {} entries in {} seconds, {} entries per second".format(
                count, duration, count / duration))

            #Fancy math for remaining prediction
            new_tick_timestamp = time.time()
            if old_min_id is not None:
                num_just_migrated = new_entries[0].id - new_entries[-1].id
                num_migrated_by_others = old_min_id - new_entries[0].id
                total_migrated_this_cycle = num_just_migrated + num_migrated_by_others
                cycles_remaining = new_entries[-1].id / total_migrated_this_cycle

                time_since_last_tick = new_tick_timestamp - old_tick_timestamp

                logging.info("{} seconds remaining...".format(
                    timedelta(seconds=cycles_remaining / time_since_last_tick)))

            old_min_id = new_entries[0].id
            old_tick_timestamp = new_tick_timestamp


    @transaction.commit_on_success
    def _acquire_lock():
        '''Acquire a lock on `WINDOW` newest CSMHA entries and return a sorted list of their IDs (highest first)'''
        with closing(connection.cursor()) as cursor:
            cursor.execute("SELECT id FROM %s WHERE processor IS NULL ORDER BY id DESC LIMIT %d FOR UPDATE;",
                [LOCK_TABLE_NAME, WINDOW])
            ids = cursor.fetchall()

            cursor.execute("UPDATE %s SET processor = %s WHERE id <= %d AND id >= %d",
                [LOCK_TABLE_NAME, WORKER_ID, ids[0], ids[-1]]
            )

        return [i[0] for i in ids]

    @transaction.commit_on_success
    def _release_lock(ids):
        '''Release my lock on `ids`'''
        with closing(connection.cursor()) as cursor:
            self._check_lock(cursor, ids)
            cursor.execute("UPDATE %s SET processor = NULL WHERE id <= %d AND id >= %d",
                [LOCK_TABLE_NAME, ids[0], ids[-1]]
            )

    @transaction.commit_on_success
    def _release_lock_and_unqueue(ids):
        '''Delete `ids` from the lock table'''
        with closing(connection.cursor()) as cursor:
            self._check_lock(cursor, ids)
            cursor.execute("DELETE FROM %s WHERE id <= %d AND id >= %d",
                [LOCK_TABLE_NAME, ids[0], ids[-1]]
            )

    def _check_lock(cursor, ids):
        '''
        Verify supposed invariants:
            - That all the rows we thought were locked are still locked by us
            - That our ID range contains the same IDs as when we acquired the lock
        '''
        cursor.execute("SELECT * FROM %s WHERE id <= %d AND id >= %d FOR UPDATE",
            [LOCK_TABLE_NAME, ids[0], ids[-1]]
        )

        found_rows = cursor.fetchall()
        not_locked = [i[1] != WORKER_ID for i in found_ids]
        found_ids = [i[0] for i in found_ids]

        if not_locked:
            raise Exception("Some rows I thought I had locked are no longer locked by me!: Lock IDs: [{}]".format(
                ','.join(map(str, not_locked))))
        if ids != found_ids:
            raise Exception("Lock rows do not match expected IDs! IDs: [{}] Lock ids: [{}]".format(
                ','.join(map(str, ids)), ','.join(map(str, found_ids))))
