import pytest
from datetime import datetime, timedelta
import nudge_engine
from nudge_engine import (
    load_config,
    nudge_generator,
    determine_priority,
    process_buddies,
    Buddy,
    BuddyPayload,
    History,
)

def test_load_config_file_exists():
    """Should successfully load config from a valid file.""" 
    config = load_config("config.json")
    assert "buddy_nudge_idle_days" in config

def test_load_config_file_not_found():
    """Should raise FileNotFoundError if config is missing.""" 
    with pytest.raises(FileNotFoundError):
        load_config("non-existing-config.json")

def test_nudge_generator_known_reason():
    """Should generate a nudge message for a known reason.""" 
    message = nudge_generator("last_interaction_days", buddy_id='stu_1000')
    assert "off the radar" in message

def test_nudge_generator_known_reason():
    """Should generate a nudge message for a known reason.""" 
    message = nudge_generator("last_interaction_days", buddy_id='stu_1000')
    assert "stu_1000" in message  # Buddy's id should be in the message
    # Or you can assert it's a non-empty string
    assert message

def test_determine_priority_urgent():
    """Should identify urgency when multiple issues present.""" 
    priority = determine_priority(['last_interaction_days', 'karma_drop', 'score'], 20)
    assert priority == "urgent"

def test_determine_priority_moderate():
    """Should identify medium urgency when two issues present.""" 
    priority = determine_priority(['karma_drop', 'last_interaction_days'], 10)
    assert priority == "moderate"

def test_determine_priority_gentle():
    """Should identify gentle urgency when a single or less issue present.""" 
    priority = determine_priority(['last_interaction_days'], 10)
    assert priority == "gentle"

def test_process_buddies_cooldown():
    """Should return no buddy nudge due to cooldown.""" 
    last_nudge = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    history = History(last_buddy_nudge=last_nudge)
    buddy_payload = BuddyPayload(
        user_id='stu_1000',
        buddies=[
            Buddy(buddy_id='stu_2000', last_interaction_days=10, messages_sent=0, karma_change_7d=-15)
        ],
        history=history
    )
    user, processed = process_buddies(buddy_payload)
    assert processed == []

def test_process_buddies_should_nudge():
    """Should produce a nudge when criteria are met.""" 
    last_nudge = (datetime.today() - timedelta(days=10)).strftime("%Y-%m-%d")
    history = History(last_buddy_nudge=last_nudge)
    buddy_payload = BuddyPayload(
        user_id='stu_1000',
        buddies=[
            Buddy(buddy_id='stu_2000',
                   last_interaction_days=10,
                   messages_sent=0,
                   karma_change_7d=-15,
                   quizzes_attempted=0)
        ],
        history=history
    )

    user, processed = process_buddies(buddy_payload)
    assert len(processed) == 1
    assert processed[0]["buddy_id"] == "stu_2000"

def test_process_buddies_max_nudge():
    """Should not produce more than max_nudges per user.""" 
    buddies = [
        Buddy(
            buddy_id=f'stu_{i}',
            last_interaction_days=12,
            messages_sent=0,
            karma_change_7d=-20,
            quizzes_attempted=2
        )
        for i in range(100)
    ]

    buddy_payload = BuddyPayload(
        user_id='stu_1000',
        buddies=buddies,
        history=None
    )
    user, processed = process_buddies(buddy_payload)
    assert len(processed) <= nudge_engine.max_nudges

def test_process_buddies_invalid_history():
    """Should  handle invalid last buddy nudge format.""" 
    history = History(last_buddy_nudge='invalid-date')
    buddy_payload = BuddyPayload(
        user_id='stu_1000',
        buddies=[
            Buddy(buddy_id='stu_2000',
                   last_interaction_days=10,
                   messages_sent=0,
                   karma_change_7d=-15)
        ],
        history=history
    )

    user, processed = process_buddies(buddy_payload)
    assert len(processed) == 1

def test_process_buddies_no_reasons():
    """Should not produce a nudge when there are no issues with buddy.""" 
    buddy_payload = BuddyPayload(
        user_id='stu_1000',
        buddies=[
            Buddy(buddy_id='stu_2000',
                   last_interaction_days=0,
                   messages_sent=5,
                   karma_change_7d=20,
                   quizzes_attempted=2)
        ],
        history=None
    )
    user, processed = process_buddies(buddy_payload)
    assert processed == []
