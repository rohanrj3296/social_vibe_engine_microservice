import pytest
import pandas as pd
import datetime
from compliment_generator import SocialNudgeRequest, UserHistory, social_metrics
from compliment_generator import (
    calculate_priority,
    check_compliment_cooldown,
    compliment_generator,
    override_prediction_if_important_feature_high,
    identify_compliment_feature,
    load_config,
    generate_compliment,
    update_tags,
    CONFIG_PATH,
    social_metrics,
    TagUpdate
)

def test_load_config_file_exists():
    """Should successfully load config from a valid file.""" 
    config = load_config()
    
    assert "buddy_nudge_idle_days" in config
    
def test_calculate_priority_emotional():
    metrics = social_metrics(
        karma_growth=100,
        helpful_answers=20,
        tag_match=["python"],
        quizzes_attempted=5,
        upvotes=50,
        consecutive_active_days=10,
        profile_completeness=0,
        previous_profile_completeness=0
    )
    result = calculate_priority("helpful_answers", metrics, ["python"], 0)
    assert result == "emotional"


def test_calculate_priority_celebratory():
    metrics = social_metrics(
        karma_growth=500,
        helpful_answers=30,
        tag_match=["python"],
        quizzes_attempted=10,
        challenges_attempted=10,
        upvotes=100,
        consecutive_active_days=30,
        profile_completeness=100,
        previous_profile_completeness=0
    )
    result = calculate_priority("profile_completeness", metrics, [], 100)
    assert result == "celebratory"


def test_calculate_priority_gentle():
    metrics = social_metrics(
        karma_growth=100,
        helpful_answers=20,
        tag_match=["python"],
        quizzes_attempted=5,
        challenges_attempted=5,
        upvotes=50,
        consecutive_active_days=10,
        profile_completeness=30,
        previous_profile_completeness=10
    )
    result = calculate_priority("profile_completeness", metrics, [], 20)
    assert result == "gentle"


def test_check_compliment_cooldown():
    last = (datetime.datetime.today() - datetime.timedelta(days=10)).strftime("%Y-%m-%d")
    assert check_compliment_cooldown(last) == True
    last = datetime.datetime.today().strftime("%Y-%m-%d")
    assert check_compliment_cooldown(last) == False


def test_compliment_generator():
    result = compliment_generator("helpful_answers", "python")
    assert isinstance(result, str)
    assert "tag" in result


def test_override_prediction_if_important_feature():
    df = pd.DataFrame([{
        "karma_growth": 1000,
        "helpful_answers": 100,
        "quizzes_attempted": 50,
        "upvotes": 500,
        "consecutive_active_days": 30
    }])

    pred, feature = override_prediction_if_important_feature_high(
        df, 0
    )
    assert pred == 1
    assert isinstance(feature, str)


def test_identify_compliment_feature():
    df = pd.DataFrame([{
        "karma_growth": 1000,
        "helpful_answers": 100,
        "quizzes_attempted": 50,
        "upvotes": 500,
        "consecutive_active_days": 30
    }])


    averages = {
        "karma_growth": 100,
        "helpful_answers": 20,
        "quizzes_attempted": 5,
        "upvotes": 50,
        "consecutive_active_days": 10,
        "tag_match": 0,
    }
    std_devs = {
        "karma_growth": 50,
        "helpful_answers": 10,
        "quizzes_attempted": 2,
        "upvotes": 20,
        "consecutive_active_days": 5,
    }
    feature_importances = {
        "karma_growth": 0.5,
        "helpful_answers": 0.5,
        "quizzes_attempted": 0.5,
        "upvotes": 0.5,
        "consecutive_active_days": 0.5,
        "tag_match": 0
    }
    top_field = identify_compliment_feature(
        df, 
        averages, 
        std_devs, 
        feature_importances
    )
    assert isinstance(top_field, str)
    assert top_field in df.columns




def test_generate_compliment():
    """Simple test for generate_compliment with dummy data."""
    metrics = social_metrics(
        karma_growth=10,
        helpful_answers=5,
        quizzes_attempted=1,
        challenges_attempted=0,
        upvotes=20,
        consecutive_active_days=30,
        profile_completeness=90,
        previous_profile_completeness=80,
        tag_match=['python']
    )

    history = UserHistory(
        last_compliment_generated=None
    )

    request = SocialNudgeRequest(
        user_id='foo123',
        buddies=[],
        social_metrics=metrics,
        history=history
    )

    result = generate_compliment(request)
    assert "compliment" in result

#After running the test scripts the popular tags in config get updated by these tags so it is commented
'''def test_update_tags():
    """Simple test for update_tags with dummy data."""
    data = TagUpdate(popular_tags={"foo": 1, "bar": 2})

    response = update_tags(data)
    assert response['status'] == 'updated'

    assert response['previous_popular_tags'] is not None
    assert response['updated_popular_tags'] == {"python": 1, "internship": 2, "Machine Learning":3}
'''