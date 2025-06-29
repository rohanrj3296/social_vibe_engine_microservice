import json
import pickle
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from nudge_engine import process_buddies,load_config
from nudge_engine import BuddyPayload
from compliment_generator import update_tags,generate_compliment
from compliment_generator import SocialNudgeRequest,TagUpdate

MODEL_VERSION="1.0.0"

app = FastAPI()

@app.post("/generate-social-nudges")
def generateSocialNudges(request_data: SocialNudgeRequest):
    compliment_output = generate_compliment(request_data)

    # Converting each buddy to a dictionary
    buddies_dicts = [buddy.model_dump() for buddy in request_data.buddies]
    
    # Converting history to dictionary
    history_dict = request_data.history.model_dump()

    # Constructing BuddyPayload with plain dicts
    buddy_payload = BuddyPayload(
        user_id=request_data.user_id,
        buddies=buddies_dicts,
        history=history_dict
    )

    user_id, processed_buddies= process_buddies(buddy_payload)
    return {
        "user_id": request_data.user_id,
        "buddy_nudges": processed_buddies,
        "compliment": compliment_output.get("compliment", {}),
        "status": "generated"
    }


#@app.post("/generate-social-nudges")
#def generateSocialNudges(request_data: SocialNudgeRequest):
    #return generate_compliment(request_data)

#@app.post("/nudges")
#def generateNudge(payload:BuddyPayload):
    #return process_buddies(payload)

@app.post("/update-popular-tags")
def updateTags(data: TagUpdate):
    return update_tags(data)


@app.get("/health")
def health_check():
    health_status = {"status": "ok", "checks": {}}
    try:
        config = load_config()
        if not config:
            raise ValueError("Config file is empty or missing critical keys")
        health_status["checks"]["config"] = "loaded"
    except Exception as e:
        health_status["status"] = "fail"
        health_status["checks"]["config"] = f"error: {str(e)}"

    try:
        with open("compliment_model.pkl", "rb") as f:
            pickle.load(f)
        health_status["checks"]["model"] = "loaded"
    except Exception as e:
        health_status["status"] = "fail"
        health_status["checks"]["model"] = f"error: {str(e)}"

    try:
        template_path = Path(__file__).parent / "templates.json"
        with open(template_path, "r", encoding="utf-8") as f:
            json.load(f)
        health_status["checks"]["templates"] = "loaded"
    except Exception as e:
        health_status["status"] = "fail"
        health_status["checks"]["templates"] = f"error: {str(e)}"
    
    try:
        payload = {
        "user_id": "stu_8901",
        "buddies": [
            {
                "buddy_id": "stu_7093",
                "last_interaction_days": 7,
                "messages_sent": 1,
                "karma_change_7d": -10,
                "quizzes_attempted": 0
            },
            {
                "buddy_id": "stu_7220",
                "last_interaction_days": 1,
                "messages_sent": 4,
                "karma_change_7d": 25,
                "quizzes_attempted": 2
            }
        ],
        "social_metrics": {
            "karma_growth": 1666,
            "profile_completeness": 85,
            "previous_profile_completeness": 88,
            "helpful_answers": 20888,
            "tag_match": [],
            "consecutive_active_days": 12,
            "quizzes_attempted": 4,
            "challenges_attempted": 4,
            "upvotes": 121
        },
        "history": {
            "last_compliment_generated": "2025-05-15",
            "last_buddy_nudge": "2024-07-14"
        }
        }
        request_model = SocialNudgeRequest(**payload)
        result = generate_compliment(request_model)
        health_status["checks"]["complimenting_logic"] = "works"
    except Exception as e:
        health_status["status"] = "fail"
        health_status["checks"]["compliment generation in compliment_generator.py"] = f"error: {str(e)}"
    
    try:
        payload = {
        "user_id": "stu_8901",
        "buddies": [
            {
                "buddy_id": "stu_7093",
                "last_interaction_days": 7,
                "messages_sent": 1,
                "karma_change_7d": -10,
                "quizzes_attempted": 0
            },
            {
                "buddy_id": "stu_7220",
                "last_interaction_days": 1,
                "messages_sent": 4,
                "karma_change_7d": 25,
                "quizzes_attempted": 2
            }
        ],
        "social_metrics": {
            "karma_growth": 1666,
            "profile_completeness": 85,
            "previous_profile_completeness": 88,
            "helpful_answers": 20888,
            "tag_match": [],
            "consecutive_active_days": 12,
            "quizzes_attempted": 4,
            "challenges_attempted": 4,
            "upvotes": 121
        },
        "history": {
            "last_compliment_generated": "2025-05-15",
            "last_buddy_nudge": "2024-07-14"
        }
        }
        request_model=BuddyPayload(**payload)
        res=process_buddies(request_model)
        health_status["checks"]["nudging_logic"] = "works"
    except Exception as e:
        health_status["status"] = "fail"
        health_status["checks"]["nudge generation in nudge_engine.py"] = f"error: {str(e)}"
        

    status_code = 200 if health_status["status"] == "ok" else 503
    return JSONResponse(content=health_status, status_code=status_code)

@app.get("/version")
def get_version():
    return{
        "model_version":MODEL_VERSION
    }
