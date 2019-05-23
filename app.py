from eventsourcing.domain.model.aggregate import AggregateRoot
from eventsourcing.domain.model.decorators import attribute
from eventsourcing.application.sqlalchemy import SQLAlchemyApplication
from eventsourcing.exceptions import ConcurrencyError

import os

os.environ['CIPHER_KEY'] = ''
os.environ['DB_URI'] = 'sqlite:////tmp/foo.db'

class Play(AggregateRoot):

    def __init__(self, name, **kwargs):
        super(Play, self).__init__(**kwargs)
        self.name = name


    def rename(self, newname):
        self.__trigger_event__(Play.PlayRenamed, name=newname)

    class PlayRenamed(AggregateRoot.Event):
        def mutate(self, aggregate):
            aggregate.name = self.name


with SQLAlchemyApplication(persist_event_type=Play.Event) as app:

    #play = Play.__create__()
    play = Play(name='swm') 

    version = play.__version__
    # Aggregate not yet in repository.
    assert play.id not in app.repository

    # Execute commands.
    play.rename('play_1')
    play.rename('play_the_second')
    play.rename('blue sky')

    play.__save__()
    assert play.id in app.repository
    copy = app.repository[play.id]

    # View retrieved aggregate.

    # Verify retrieved state (cryptographically).
    assert copy.__head__ == play.__head__

    # Delete aggregate.
    play.__discard__()
    play.__save__()

    # Discarded aggregate not found.
    assert play.id not in app.repository
    try:
        # Repository raises key error.
        app.repository[play.id]
    except KeyError:
        pass
    else:
        raise Exception("Shouldn't get here")

    # Get historical state (at version from above).
    old = app.repository.get_entity(play.id, at=version)

    # Optimistic concurrency control (no branches).

    old.rename('future')
    try:
        old.__save__()
    except ConcurrencyError:
        pass
    else:
        raise Exception("Shouldn't get here")

    # Check domain event data integrity (happens also during replay).
    events = app.event_store.get_domain_events(play.id)
    last_hash = ''

    for event in events:
        event.__check_hash__()
        assert event.__previous_hash__ == last_hash
        last_hash = event.__event_hash__

    # Verify stored sequence of events against known value.
    assert last_hash == play.__head__

    # Project application event notifications.
    from eventsourcing.interface.notificationlog import NotificationLogReader
    reader = NotificationLogReader(app.notification_log)

    #TODO: summfin cool?
