import json
import random
import logging
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel
from typing import Optional,List

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def load_config(config_path="config.json"):
    try:
        with open(config_path, "r") as f:
            logger.info(f"Loading config from {config_path}")
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Config file not found: {config_path}")
        raise FileNotFoundError(f"Config file not found: {config_path}")
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON format in config file: {config_path}")
        raise ValueError(f"Invalid JSON format in config file: {config_path}")

_json_path = Path(__file__).parent / "templates.json"

with open(_json_path, "r", encoding="utf-8") as f:
    template_data = json.load(f) 
    logger.info(f"Loaded templates from {_json_path}")
    
config = load_config()

idle_days_threshold = config["buddy_nudge_idle_days"]
karma_drop_threshold = config["karma_drop_threshold"]
score_threshold = config["buddy_score_threshold"]
quizzes_threshold=config["quizzes_attempted_threshold"]
nudge_cooldown_days = config["nudge_cooldown_days"]
max_nudges=config["max_nudges_per_user"]

class Buddy(BaseModel):
    buddy_id: Optional[str]
    last_interaction_days: Optional[int]
    messages_sent: Optional[int]
    karma_change_7d: Optional[int]
    quizzes_attempted: Optional[int] = 0

class History(BaseModel):
    last_buddy_nudge: Optional[str]

class BuddyPayload(BaseModel):
    user_id: Optional[str]
    buddies: List[Buddy]
    history: Optional[History] = {}

def nudge_generator(reason: str, buddy_id: str = None) -> str:
    entry = next((item for item in template_data if item["trigger"] == reason), None)   
    if not entry:
        logger.warning(f"No template found for reason '{reason}' for buddy '{buddy_id}'")
        return f"Looks like {buddy_id} has been quiet. Maybe send them a quick message?"
    nudge = random.choice(entry.get("template", [f"Looks like {buddy_id} has been quiet. Maybe send them a quick message?"]))
    nudge= nudge.replace("{buddy_id}", buddy_id)
    logger.debug(f"Nudge generated for {buddy_id}: {nudge}")
    return nudge  

def determine_priority(reasons, buddy_score):
    if len(reasons) == 3 or ("score" in reasons and buddy_score < (score_threshold - 5)):
        return "urgent"
    elif len(reasons) == 2 or "karma_drop" in reasons:
        return "moderate"
    else:
        return "gentle"

idle_days_weight=config["last_interaction_days_weight_for_inactivity"]
score_weight=config["score_weight_for_inactivity"]
karma_weight=config["karma_weight_for_inactivity"]

def process_buddies(payload: BuddyPayload):
    user_id = payload.user_id
    buddies = payload.buddies
    last_nudge_str = payload.history.last_buddy_nudge if payload.history else None
    
    logger.info(f"Processing buddies for user: {user_id}")
    
    if last_nudge_str:
        try:
            last_nudge_date = datetime.strptime(last_nudge_str, "%Y-%m-%d")
            if (datetime.today() - last_nudge_date).days < nudge_cooldown_days:
                logger.info(f"Nudge cooldown active for user {user_id}. Skipping...")
                return user_id, []
        except ValueError:
            pass  
        
    processed_buddies = []

    for buddy in buddies:
        buddy_id = buddy.buddy_id
        last_interaction_days = buddy.last_interaction_days
        messages_sent = buddy.messages_sent
        karma_change_7d = buddy.karma_change_7d
        quizzes_attempted=buddy.quizzes_attempted
        buddy_score = karma_change_7d + messages_sent + last_interaction_days

        reasons = []
        
        if last_interaction_days > idle_days_threshold:
            reasons.append("last_interaction_days")
        if karma_change_7d < karma_drop_threshold:
            reasons.append("karma_drop")
        if buddy_score < score_threshold:

            reasons.append("score")
        if quizzes_attempted<quizzes_threshold:
            reasons.append("quizzes_attempted")

        if reasons:
            primary_reason = reasons[0]
            message = nudge_generator(primary_reason, buddy_id)
            priority = determine_priority(reasons, buddy_score)  # NEW
            inactivity_score = (
                (last_interaction_days * idle_days_weight) +
                (karma_change_7d * karma_weight) +
                (buddy_score * score_weight)
            )
            buddy_data = {
                "buddy_id": buddy_id,
                "reason": ", ".join(reasons),
                "message": message,
                "priority": priority,
                "inactivity_score":inactivity_score
            }
            processed_buddies.append(buddy_data)

    if processed_buddies and len(processed_buddies)<=max_nudges:
        return user_id,processed_buddies
    if len(processed_buddies)>max_nudges:
        sorted_buddies = sorted(processed_buddies, key=lambda x: x["inactivity_score"], reverse=True)
        top_buddies = sorted_buddies[::-1][:max_nudges]
        return user_id,top_buddies
    
    return user_id,processed_buddies