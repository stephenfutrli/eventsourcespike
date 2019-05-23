from eventsourcing.domain.model.aggregate import AggregateRoot
from eventsourcing.domain.model.decorators import attribute
from eventsourcing.application.sqlalchemy import SQLAlchemyApplication
from eventsourcing.exceptions import ConcurrencyError

import os

os.environ['CIPHER_KEY'] = ''
os.environ['DB_URI'] = 'sqlite:////tmp/foo.db'

class Play(AggregateRoot):

    def __init__(self, **kwargs):
        super(Play, self).__init__(**kwargs)
        self.name = 'wonder'

    def rename(self, newname):
        self.__trigger_event__(Play.PlayRenamed, name=newname)

    class PlayRenamed(AggregateRoot.Event):
        def mutate(self, aggregate):
            aggregate.name = self.name


with SQLAlchemyApplication(persist_event_type=Play.Event) as app:

    world = Play.__create__()

    version = world.__version__
    # Aggregate not yet in repository.
    assert world.id not in app.repository

    # Execute commands.
    world.rename('dinosaurs')
    world.rename('trucks')
    world.rename('internet')

    world.__save__()
    assert world.id in app.repository
    copy = app.repository[world.id]

    # View retrieved aggregate.

    # Verify retrieved state (cryptographically).
    assert copy.__head__ == world.__head__

    # Delete aggregate.
    world.__discard__()
    world.__save__()

    # Discarded aggregate not found.
    assert world.id not in app.repository
    try:
        # Repository raises key error.
        app.repository[world.id]
    except KeyError:
        pass
    else:
        raise Exception("Shouldn't get here")

    # Get historical state (at version from above).
    old = app.repository.get_entity(world.id, at=version)

    # Optimistic concurrency control (no branches).

    old.rename('future')
    try:
        old.__save__()
    except ConcurrencyError:
        pass
    else:
        raise Exception("Shouldn't get here")

    # Check domain event data integrity (happens also during replay).
    events = app.event_store.get_domain_events(world.id)
    last_hash = ''

    for event in events:
        event.__check_hash__()
        assert event.__previous_hash__ == last_hash
        last_hash = event.__event_hash__

    # Verify stored sequence of events against known value.
    assert last_hash == world.__head__

    # Project application event notifications.
    from eventsourcing.interface.notificationlog import NotificationLogReader
    reader = NotificationLogReader(app.notification_log)
    for read in reader.read():
        print(read)

    # - create two more aggregates
    world = Play.__create__()
    world.__save__()

    world = Play.__create__()
    world.__save__()

    # - get the new event notifications from the reader
    notification_ids = [n['id'] for n in reader.read()]
    #assert notification_ids == [6, 7]
