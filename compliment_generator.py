import json
import random
import logging
import pickle
import pandas as pd
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from fastapi import  HTTPException
from datetime import datetime

# Constants
CONFIG_PATH = "config.json"

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# Load compliment and nudge templates
_json_path = Path(__file__).parent / "templates.json"

with open(_json_path, "r", encoding="utf-8") as f:
    _compliment_data = json.load(f)
    logger.info(f"Loaded compliment templates from {_json_path}")
    
# Load the compliment prediction model
try:
    with open("model.pkl", "rb") as file:
        loaded_model = pickle.load(file)
        logger.info("Compliment model loaded successfully.")
except FileNotFoundError:
    logger.error("Model file not found: compliment_model.pkl")
    raise RuntimeError("Model file not found: compliment_model.pkl")
except pickle.UnpicklingError:
    logger.error("Error unpickling model file")
    raise RuntimeError("Error unpickling model file")
except Exception as e:
    logger.exception("Unexpected error loading model")
    raise RuntimeError(f"Unexpected error loading model: {e}")

#load the config.json to access all the configuration properties
def load_config():
    try:
        with open(CONFIG_PATH, "r") as f:
            logger.info(f"Loading config from {CONFIG_PATH}")
            return json.load(f)
    except FileNotFoundError:
        logging.warning("Config file not found!")
        return {}
    
#save changes to config.json (used to save most popular tags recieved through json)
def save_config(config_data):
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(config_data, f, indent=4)
            logger.info(f"Saved config to {CONFIG_PATH}")
    except Exception as e:
        logger.error(f"Failed to save config: {e}")

config = load_config()

# Feature statistics
feature_averages = {
    "average_upvotes": config["average_upvotes"],
    "average_helpful_answers": config["average_helpful_answers"],
    "average_quizzes_attempted": config["average_quizzes_attempted"],
    "average_karma_growth": config["average_karma"],
    "average_consecutive_active_days": config["average_consecutive_active_days"],
}

feature_high_marks = {
    "karma": config["high_karma_mark"],
    "helpful_answers": config["high_helpful_answers_mark"],
    "quizzes": config["high_quiz_mark"],
    "upvotes": config["high_upvotes_mark"],
    "consecutive_days": config["high_consecutive_days_mark"],
}

feature_low_marks=config["feature_low_marks"]

feature_base_factors = config["feature_base_factors"]

feature_importances = config["feature_importances"]

compliment_cooldown_days=config["compliment_cooldown_days"]

popular_tags = config.get("popular_tags", {})

# Pydantic models for validation
class social_metrics(BaseModel):
    karma_growth: Optional[int] = 0
    helpful_answers: Optional[int] = 0
    tags_followed: List[str] = Field(default_factory=list)
    quizzes_attempted: Optional[int] = 0
    upvotes: Optional[int] = 0
    consecutive_active_days: Optional[int] = 0
    profile_completeness:Optional[int]=0
    previous_profile_completeness:Optional[int] = 0
    
class TagUpdate(BaseModel):
    popular_tags: Dict[str, int]
    
class BuddyMetrics(BaseModel):
    buddy_id: str
    last_interaction_days: int
    messages_sent: int
    karma_change_7d: int
    quizzes_attempted: int

class UserHistory(BaseModel):
    last_compliment_generated: Optional[str] = None
    last_buddy_nudge: Optional[str] = None

class SocialNudgeRequest(BaseModel): 
    user_id: str
    buddies: List[BuddyMetrics]
    social_metrics: social_metrics 
    history: UserHistory

class OutputCompliment(BaseModel):
    message:str=None
    reason:str=None
    priority:str=None

# Determine priority level for compliments
def calculate_priority(feature: str, metrics: social_metrics, matched_tags: List[str], profile_improvement: int) -> str:
    if feature in {"helpful_answers", "upvotes"} and matched_tags:
        return "emotional"
    if feature == "profile_completeness" and profile_improvement > 25:
        return "celebratory"
    if feature == "profile_completeness" and profile_improvement > 15:
        return "gentle"
    
    strong_features = 0
    
    if metrics.karma_growth > feature_averages["average_karma_growth"] * 1.2:
        strong_features += 1
    if metrics.upvotes > feature_averages["average_upvotes"] * 1.2:
        strong_features += 1
    if metrics.consecutive_active_days > feature_averages["average_consecutive_active_days"] * 1.2:
        strong_features += 1
    if metrics.quizzes_attempted > feature_averages["average_quizzes_attempted"] * 1.2:
        strong_features += 1
    if strong_features >= 3:
        return "celebratory"
    return "gentle"

# Check cooldown before issuing another compliment
def check_compliment_cooldown(last_compliment_generated: str) -> bool:
    if last_compliment_generated:
        try:
            last_compliment_date = datetime.strptime(last_compliment_generated, "%Y-%m-%d")
            return (datetime.today() - last_compliment_date).days >= compliment_cooldown_days
        except ValueError:
            logger.warning("Invalid date format for last_compliment_generated")
            return False  
    return True  

# Generate compliment message using template
def compliment_generator(feature: str, tag: str = None) -> str:
    entry = next((item for item in _compliment_data if item["trigger"] == feature), None)
    if not entry:
        logger.warning(f"No compliment template found for feature: {feature}")
        return "Great job! Keep contributing."
    compliment = random.choice(entry.get("template", ["Great job! Keep contributing."]))
    if feature == "helpful_answers":
        if tag:
            compliment = compliment.replace("{tag}", tag)
        else:
            compliment = compliment.replace("{tag}", "this space") 
    emoji = random.choice(entry.get("emojis", ["✨"]))
    return f"{compliment} {emoji}" 

# Override model prediction if high individual feature      
def override_prediction_if_important_feature_high(df, prediction):
    if int(prediction) == 0:
        high_features = {}
        if int(df["karma_growth"].iloc[0]) >= feature_averages["average_karma_growth"] * feature_high_marks["karma"]:
            high_features["karma_growth"] = int(df["karma_growth"].iloc[0])
        if int(df["helpful_answers"].iloc[0]) >= feature_averages["average_helpful_answers"] * feature_high_marks["helpful_answers"]:
            high_features["helpful_answers"] = int(df["helpful_answers"].iloc[0])
        if int(df["quizzes_attempted"].iloc[0]) >= feature_averages["average_quizzes_attempted"] * feature_high_marks["quizzes"]:
            high_features["quizzes_attempted"] = int(df["quizzes_attempted"].iloc[0])
        if int(df["upvotes"].iloc[0]) >= feature_averages["average_upvotes"] * feature_high_marks["upvotes"]:
            high_features["upvotes"] = int(df["upvotes"].iloc[0])
        if int(df["consecutive_active_days"].iloc[0]) >= feature_averages["average_consecutive_active_days"] * feature_high_marks["consecutive_days"]:
            high_features["consecutive_active_days"] = int(df["consecutive_active_days"].iloc[0])
        if high_features:        
            filtered_df = pd.DataFrame([high_features])
            for col in df.columns:
                if col not in filtered_df.columns:
                    filtered_df[col] = 0
            complimented_feature = identify_compliment_feature(
                user_df=filtered_df,
                averages={
                    "karma_growth": feature_averages["average_karma_growth"],
                    "helpful_answers": feature_averages["average_helpful_answers"],
                    "quizzes_attempted": feature_averages["average_quizzes_attempted"],
                    "upvotes": feature_averages["average_upvotes"],
                    "consecutive_active_days": feature_averages["average_consecutive_active_days"],
                    "tag_match": 0,
                },
                base_factors=feature_base_factors ,
                feature_importances=feature_importances,
            )
            return 1, complimented_feature
        
    return prediction, None

# Determine top feature based on z-score and importance
def identify_compliment_feature(user_df, averages, base_factors , feature_importances):
    scores = {}
    for feature in user_df.columns:
        user_value = user_df[feature].values[0]
        if user_value < feature_averages[f"average_{feature}"] * feature_low_marks[feature] :
            continue
        avg = averages.get(feature, 1)
        base_factor = base_factors.get(feature, 1)
        z_score = (user_value - avg) / base_factor  if base_factor != 0 else 0
        score = z_score * feature_importances.get(feature, 0)       
        scores[feature] = score
    if scores:
        #print(scores)
        top_feature = max(scores, key=scores.get)
        return top_feature
    else:
        logger.warning("No significant feature found for compliment generation.")
        return None

# Main compliment generator logic
def generate_compliment(request_data:SocialNudgeRequest):
    metrics = request_data.social_metrics
    last_compliment_generated = request_data.history.last_compliment_generated
    social_metrics_received = [[
        metrics.karma_growth,
        metrics.helpful_answers,
        metrics.quizzes_attempted,
        metrics.upvotes,
        metrics.consecutive_active_days,
    ]]
    df = pd.DataFrame(social_metrics_received, columns=[
        "karma_growth",
        "helpful_answers",
        "quizzes_attempted",
        "upvotes",
        "consecutive_active_days",
    ])
    
    filtered_df = df[loaded_model.feature_names_in_]
    prediction = loaded_model.predict(filtered_df)[0]
    complimented_feature = None
    high_feature = None
    profile_improvement = metrics.profile_completeness - metrics.previous_profile_completeness
    matched_tags = [tag for tag in metrics.tags_followed if tag in popular_tags]
    compliment=OutputCompliment()

    if prediction == 0:
        prediction, high_feature = override_prediction_if_important_feature_high(df, prediction)      
        if prediction==1 and not check_compliment_cooldown(last_compliment_generated):
            return{
                "compliment":{
                    "message":compliment.message,
                    "reason":compliment.reason,
                    "priority":compliment.priority
                }
            }
        elif prediction==1 and check_compliment_cooldown(last_compliment_generated):
            compliment.message=compliment_generator(high_feature)
            compliment.reason=high_feature
            compliment.priority=calculate_priority(high_feature,metrics,matched_tags,profile_improvement)
            return {
                "compliment": {
                    "message":compliment.message, 
                    "reason": compliment.reason,
                    "priority": compliment.priority 
                }
            }
        elif prediction==0 and  profile_improvement > 10:
            if check_compliment_cooldown(last_compliment_generated):
                compliment.message=compliment_generator("profile_completeness")
                compliment.reason="profile improvement"
                compliment.priority = calculate_priority("profile_completeness", metrics, matched_tags, profile_improvement)
                return {
                    "compliment": {
                        "message": compliment.message,
                        "reason": compliment.reason,
                        "priority":compliment.priority
                    }
                }
            elif not check_compliment_cooldown(last_compliment_generated):
                return{
                "compliment":{
                    "message":compliment.message,
                    "reason":compliment.reason,
                    "priority":compliment.priority
                }
            }
        else:
            return{
                "compliment":{
                    "message":compliment.message,
                    "reason":compliment.reason,
                    "priority":compliment.priority
                }
            }
                          
    if prediction == 1:
        low_features=0
        if int(df["karma_growth"][0]) < feature_averages["average_karma_growth"] * 0.4 :
            low_features+=1
        if int(df["helpful_answers"][0]) < feature_averages["average_helpful_answers"] * 0.4:
            low_features+=1
        if int(df["quizzes_attempted"][0]) < feature_averages["average_quizzes_attempted"] * 0.4 :
            low_features+=1
        if int(df["upvotes"][0]) < feature_averages["average_upvotes"] * 0.14 :
            low_features+=1
        if int(df["consecutive_active_days"][0]) < feature_averages["average_consecutive_active_days"] * 0.3:
            low_features+=1
        if low_features>=3:
            if profile_improvement>10 and check_compliment_cooldown(last_compliment_generated):
                compliment.message=compliment_generator("profile_completeness")
                compliment.reason="Profile improvement"
                compliment.priority=calculate_priority("profile_completeness", metrics, matched_tags, profile_improvement)
                return {
                "compliment": {
                    "message": compliment.message,
                    "reason": compliment.reason,
                    "priority": compliment.priority
                }
            }
            else:
                
                return  {
                        "compliment":{
                            "message":compliment.message,
                            "reason":compliment.reason,
                            "priority":compliment.priority
                            }
                    }
            
          
        complimented_feature= identify_compliment_feature(
            user_df=df,
            averages={
                "karma_growth": feature_averages["average_karma_growth"],
                "helpful_answers": feature_averages["average_helpful_answers"],
                "quizzes_attempted": feature_averages["average_quizzes_attempted"],
                "upvotes": feature_averages["average_upvotes"],
                "consecutive_active_days": feature_averages["average_consecutive_active_days"],
                "tag_match": 0,
            },
            base_factors =feature_base_factors ,
            feature_importances=feature_importances,
        )
        if profile_improvement > 40 :
            complimented_feature = "profile_completeness"
            compliment.message=compliment_generator(complimented_feature)
            compliment.reason="Profile improvement",
            compliment.priority= calculate_priority(complimented_feature, metrics, matched_tags, profile_improvement)
        result = {
                "compliment": {
                    "message": compliment.message,
                    "reason": compliment.reason,
                    "priority": compliment.priority
                }
            }
        if complimented_feature:
            if complimented_feature == "helpful_answers" and metrics.tags_followed:
                matched_tags = [tag for tag in metrics.tags_followed if tag in popular_tags]
                if matched_tags:
                    top_tag = max(matched_tags, key=lambda t: popular_tags[t])
                    compliment.message=compliment_generator(complimented_feature, tag=top_tag)
                    compliment.reason=f"{complimented_feature} + tag match"
                    compliment.priority=calculate_priority(complimented_feature, metrics, matched_tags, profile_improvement)
                    result["compliment"] = {
                        "message": compliment.message,
                        "reason": compliment.reason ,
                        "priority": compliment.priority
                    }
                else:
                    compliment.message=compliment_generator("helpful_answers_but_no_tag_match")
                    compliment.reason=complimented_feature
                    compliment.priority=calculate_priority(complimented_feature, metrics, matched_tags, profile_improvement)
                    result["compliment"]={
                        
                        "message":compliment.message,
                        "reason":compliment.reason,
                        "priority":compliment.priority
                    }
                    
            else:
                compliment_features = {
                    "karma_growth",
                    "consecutive_active_days",
                    "quizzes_attempted",
                    "upvotes",
                    "profile_completeness"
                }
                if complimented_feature in compliment_features:
                    compliment.message=compliment_generator(complimented_feature)
                    compliment.reason=complimented_feature
                    compliment.priority=calculate_priority(complimented_feature, metrics, matched_tags, profile_improvement)
                    result["compliment"] = {
                        "message": compliment.message,
                        "reason": compliment.reason,
                        "priority": compliment.priority
                    }
                

            return result if check_compliment_cooldown(last_compliment_generated) else  {"compliment":{"message":None,"reason":None,"priority":None}}
        return {
            "compliment":{
                "message":compliment.message,
                "reason":compliment.reason,
                "priority":compliment.priority
            }
        }
        
# Update tags in config
def update_tags(data: TagUpdate):
    global popular_tags, config
    try:
        logger.debug(f"Received request to update tags: {data.popular_tags}")
        previous_popular_tags = popular_tags.copy()
        popular_tags = data.popular_tags
        config["popular_tags"] = popular_tags
        save_config(config)
        logger.info("Popular tags updated and saved to config.json.")
        return {
            "status": "updated",
            "previous_popular_tags": previous_popular_tags,
            "updated_popular_tags": popular_tags,
        }
    except Exception as e:
        logging.error(f"Error while updating popular tags: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update popular tags due to internal error.")
