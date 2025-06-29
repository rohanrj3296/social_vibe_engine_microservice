# 📘 API Documentation

---

## 📌 Routes

---

### 🔹 `/generate-social-nudges`

#### ✅ Method: `POST`

#### 🛠️ What It Does:

It passes buddy data to `process_buddies()` and user social metrics to `generate_compliment()`, then combines the outputs to return nudges for buddies and an anonymous compliment for the user. Compliments and nudges are randomly selected from template sets to keep responses varied and engaging for the user.

---

#### 🌐 URL:

```json
   http://localhost:8000/generate-social-nudges
```

#### 📥 Sample Input (Request Body):

```json
{
    "user_id": "stu_8901",
    "buddies": [
        {
            "buddy_id": "stu_7093",
            "last_interaction_days": 12,
            "messages_sent": 2,
            "karma_change_7d": -13,
            "quizzes_attempted": 1
        },
        {
            "buddy_id": "stu_7220",
            "last_interaction_days": 5,
            "messages_sent": 5,
            "karma_change_7d": 20,
            "quizzes_attempted": 2
        }
    ],
    "social_metrics": {
        "karma_growth": 35,
        "helpful_answers": 4,
        "tags_followed": ["python","internship"],
        "quizzes_attempted":2,
        "upvotes": 26,
        "consecutive_active_days":6,
        "profile_completeness": 75,
        "previous_profile_completeness": 68
    },
    "history": {
        "last_compliment_generated": "2025-05-15",
        "last_buddy_nudge": "2025-05-27"
    }
}
```

#### 📤 Sample Output (Response Body):

```json
{
    "user_id": "stu_8901",
    "buddy_nudges": [
        {
            "buddy_id": "stu_7093",
            "reason": "last_interaction_days, karma_drop",
            "message": "Haven’t heard much from stu_7093 recently. Want to check in and say hi?",
            "priority": "moderate",
            "inactivity_score": 6.5
        }
    ],
    "compliment": {
        "message": "Your answers in internship tag are genuinely helping people  🤝",
        "reason": "helpful_answers + tag match",
        "priority": "emotional"
    },
    "status": "generated"
}
```

### 🔹 `/update-popular-tags`

#### ✅ Method: `POST`

#### 🛠️ What It Does:

This route receives a list of popular tags with weights and updates them in the config.json file. It returns the previous and updated tag lists for confirmation.These updated popular tags are later used in the /generate-social-nudges route to match against the tags_followed field in the request data, helping determine whether a compliment triggered by helpful_answers should include tag-specific context or not.

---

#### 🌐 URL:

```json
   http://localhost:8000/update-popular-tags
```

#### 📥 Sample Input (Request Body):

```json
{
  "popular_tags": {
    "internship": 10,
    "ml": 8,
    "python": 7,
    "hackathon": 5,
    "opencv": 4,
    "AR VR": 2
  }
}
```

#### 📤 Sample Output (Response Body):

```json
{
  "status": "updated",
  "previous_popular_tags": {
    "Scikit-Learn": 12,
    "HR-Round": 6
  },
  "updated_popular_tags": {
    "internship": 10,
    "ml": 8,
    "python": 7,
    "hackathon": 5,
    "opencv": 4,
    "AR VR": 2
  }
}
```

### 🔹 `/health`

#### ✅ Method: `GET`

#### 🛠️ What It Does:

This route performs internal health checks by validating the config file, ML model, and template accessibility. It also runs sample logic for compliment and nudge generation to ensure core functionalities work correctly.

---

#### 🌐 URL:

```json
   http://localhost:8000/health
```

#### 📤 Sample Output (Response Body):

```json
{
  "status": "ok",
  "checks": {
    "config": "loaded",
    "model": "loaded",
    "templates": "loaded",
    "complimenting_logic": "works",
    "nudging_logic": "works"
  }
}
```

### 🔹 `/version`

#### ✅ Method: `GET`

#### 🛠️ What It Does:

This route returns the current version of the Social Vibe Engine. It helps verify which version is deployed.

---

#### 🌐 URL:

```json
   http://localhost:8000/version
```

#### 📤 Sample Output (Response Body):

```json
{
  "model_version": "1.0.0"
}
```

---

---

# ⚙️ Configuration Guide

The `config.json` file contains customizable parameters that control how the Social Vibe Engine generates nudges and compliments. These configurations allow developers to tune the system’s behavior offline without changing code.

---

### 🛠️ Config Keys & Descriptions

#### Averages:

These averages are used to compare user activity values (e.g., upvotes, karma, quizzes) against predefined platform averages to determine if a feature stands out. This comparison helps in identifying which feature to complimented and is also used with high/low mark multipliers to override model predictions and ensure meaningful, personalized compliments.
**NOTE**: THESE AVERAGE VALUES ARE **NOT** THE EXACT AVERAGE VALUES OF DATA USED FOR TRAINING THE MODEL , THESE VALUES ARE ADJUSTED BY TRAIL AND ERROR METHOD TO ACHIEVE BEHAVIOUR/RESULSTS MENTIONED IN THE INSTRUCTIONS.

```json
    "average_upvotes": 60,
    "average_helpful_answers": 8,
    "average_quizzes_attempted": 8,
    "average_karma": 67,
    "average_challenges_attempted": 4,
    "average_consecutive_active_days": 10,
```

**The above average values are used in identify_compliment_feature(),override_prediction_if_important_feature_high(),etc in compliment_generator.py**

---

#### High Marks:

These high\_\*\_mark values act as multipliers to identify exceptional user activity. If a user’s metric like helpful_answers exceeds the average by a specified high mark (e.g., 1.5×), the system may override the model and generate a compliment. This ensures standout efforts are always recognized.

```json
    "high_karma_mark": 1.5,
    "high_helpful_answers_mark": 1.5,
    "high_quiz_mark": 2.5,
    "high_challenge_mark": 3,
    "high_upvotes_mark": 1.7,
    "high_consecutive_days_mark": 1.5,
```

**The above high mark values are used in override_prediction_if_important_feature_high() in compliment_generator.py**

---

#### Feature Base Factors & Feature Importances:

These values are used in the mathematical logic of determinig the metric to be complimented like karma_growth,helpful_answers.

```json
"feature_base_factors": {
      "_comment1":"These feature_base_factors represent the approximate peak values each feature can reach ",
      "_comment2":"for example, the highest observed karma_growth is around 480.",
      "_comment3":"While these values aren’t the actual maximums, they’ve been fine-tuned through trial and error to produce the desired behavior as outlined in the project instructions. ",
      "_comment4":"They are used in the scoring logic to help identify which feature should be complimented.",
      "karma_growth": 480,
      "helpful_answers": 20,
      "quizzes_attempted": 30,
      "upvotes": 300,
      "consecutive_active_days": 30
    },
"feature_importances": {
        "_comment1":"These feature_importances indicate the relative importance of each feature in determining which one should be complimented.",
        "_comment2":"For example, if karma_growth is 55 and helpful_answers is 6, the system may choose to compliment helpful_answers.",
        "_comment3":"These importances work in conjunction with feature_averages and feature_base_factors, and by adjusting them, we can fine-tune how the system identifies the most deserving feature for a compliment.",
        "karma_growth": 5,
        "helpful_answers": 1,
        "quizzes_attempted": 2,
        "upvotes": 4,
        "consecutive_active_days": 3
    }
```

**NOTE:The above values are finalised by trial and testing to achieve the Behaviour/Results similar to what is mentioned in the instructions**

```python
        z_score = (user_value - avg) / base_factor  if base_factor != 0 else 0
        score = z_score * feature_importances.get(feature, 0)
```

Based on above mathematical logic the score for each metric is calculated and the metric having highest sccore is complimented

```python
#Score looks like:
{'karma_growth': -0.0019125, 'helpful_answers': -0.000625, 'quizzes_attempted': -0.001008, 'upvotes': -0.0008870967741935483, 'consecutive_active_days': -0.03312}
```
---

#### Popular Tags:

The popular_tags contains topic tags with associated weights indicating their relevance on the platform. These tags are matched against the tags_followed list from user input during compliment generation.If a user is complimented for helpful_answers, the most popular tag they follow is highlighted in the compliment, making it more personalized and meaningful. This ensures recognition is not just for activity but also for impact in trending areas.

```json
"popular_tags": {
        "internship": 10,
        "ml": 8,
        "python": 7,
        "hackathon": 5,
        "opencv": 4,
        "AR VR": 2
    },
```

**NOTE:The popular_tags should be updated regularly using the /update-popular-tags endpoint to reflect current platform trends and maintain the relevance of compliments.**

---

#### Low Marks:

Low marks are used to suppress undeserving compliments. If the model predicts a compliment but the user’s metric falls below average × low_mark, the feature is considered too weak, and the prediction is overridden—preventing repetitive or undeserved compliments that might frustrate the user over time

```json
"feature_low_marks": {
        "karma_growth": 0.4,
        "helpful_answers": 0.4,
        "quizzes_attempted": 0.4,
        "upvotes": 0.14,
        "consecutive_active_days": 0.3
    }
```

**The above low marks are used in identify_compliment_feature() in compliment_generator.py**

---

#### Buddy Metric Weights:

These weights are used to calculate inactivity score for each buddy. If the number of inactive buddies exceeds max_nudges_per_user, the system nudges the top most inactive ones—based on the inactivity score.

```json
    "last_interaction_days_weight_for_inactivity": 1.5,
    "score_weight_for_inactivity": 1.5,
    "karma_weight_for_inactivity": 1
```

```python
idle_days_weight=config["last_interaction_days_weight_for_inactivity"]
score_weight=config["score_weight_for_inactivity"]
karma_weight=config["karma_weight_for_inactivity"]

inactivity_score = (
                (last_interaction_days * idle_days_weight) +
                (karma_change_7d * karma_weight) +
                (buddy_score * score_weight)
              )
```

---

#### compliment_cooldown_days:

If the user was last complimented less than compliment_cooldown_days days then the compliment will be supressed.

---

#### buddy_nudge_idle_days:

If the buddy's last_interaction_days are greater than buddy_nudge_idle_days then the buddy is nudged for this

---

#### karma_drop_threshold:

If buddy's karma_change_7d is less than the karma_drop_threshold then the buddy is nudged for karma drop

---

#### max_nudges_per_user:

The user will be sent only max_nudges_per_user number nudges from his inactive buddies. If 5 buddies of a user are inactive and max_nudges_per_user is 2 then the user will only recieve the nudges for 2 most inactive buddies

---

#### buddy_score_threshold:

If the Score of a buddy is less than the buddy_score_threshold then he will be considered as an inactive buddy.

```python
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

```

---

#### quizzes_attempted_threshold:

If number of quizzes attempted by buddy are less than the quizzes_attempted_threshold then buddy will be nudged for this.

---

#### nudge_cooldown_days:

If user was sent nudges for his inactive buddies less than nudge_cooldown_days then he will not be sent the nudges of his inactive buddies.

---

---

# 5 Test Users With Their Buddies:

## stu_8901:

```json
{
    "user_id": "stu_8901",
    "buddies": [
        {
            "buddy_id": "stu_7093",
            "last_interaction_days": 12,
            "messages_sent": 2,
            "karma_change_7d": -13,
            "quizzes_attempted": 1
        },
        {
            "buddy_id": "stu_7220",
            "last_interaction_days": 20,
            "messages_sent": 5,
            "karma_change_7d": -20,
            "quizzes_attempted": 2
        },
        {
            "buddy_id": "stu_7001",
            "last_interaction_days": 20,
            "messages_sent": 5,
            "karma_change_7d": -20,
            "quizzes_attempted": 2
        }
    ],
    "social_metrics": {
        "karma_growth": 35,
        "helpful_answers": 4,
        "tags_followed": ["python","internship"],
        "quizzes_attempted":2,
        "upvotes": 26,
        "consecutive_active_days":6,
        "profile_completeness": 75,
        "previous_profile_completeness": 68
    },
    "history": {
        "last_compliment_generated": "2025-05-15",
        "last_buddy_nudge": "2025-05-27"
    }
}
```

## stu_8902:

```json
{
    "user_id": "stu_8901",
    "buddies": [
        {
            "buddy_id": "stu_7093",
            "last_interaction_days": 12,
            "messages_sent": 2,
            "karma_change_7d": -7,
            "quizzes_attempted": 1
        },
        {
            "buddy_id": "stu_7220",
            "last_interaction_days": 20,
            "messages_sent": 5,
            "karma_change_7d": -20,
            "quizzes_attempted": 2
        }
    ],
    "social_metrics": {
        "karma_growth": 78,
        "helpful_answers": 6,
        "tags_followed": ["python","internship"],
        "quizzes_attempted":7,
        "upvotes": 32,
        "consecutive_active_days":8,
        "profile_completeness": 84,
        "previous_profile_completeness": 75
    },
    "history": {
        "last_compliment_generated": "2025-05-15",
        "last_buddy_nudge": "2025-05-27"
    }
}
```

## stu_8903:

```json
{
    "user_id": "stu_8901",
    "buddies": [
        {
            "buddy_id": "stu_7093",
            "last_interaction_days": 2,
            "messages_sent": 2,
            "karma_change_7d": 7,
            "quizzes_attempted": 
        },
        }
    ],
    "social_metrics": {
        "karma_growth":108,
        "helpful_answers": 13,
        "tags_followed": ["python","internship"],
        "quizzes_attempted":9,
        "upvotes": 39,
        "consecutive_active_days":8,
        "profile_completeness": 84,
        "previous_profile_completeness": 75
    },
    "history": {
        "last_compliment_generated": "2025-05-15",
        "last_buddy_nudge": "2025-05-27"
    }
}
```

## stu_8904:

```json
{
  "user_id": "stu_8904",
  "buddies": [
    {
      "buddy_id": "stu_6093",
      "last_interaction_days": 2,
      "messages_sent": 2,
      "karma_change_7d": -3,
      "quizzes_attempted": 1
    },
    {
      "buddy_id": "stu_6220",
      "last_interaction_days": 1,
      "messages_sent": 4,
      "karma_change_7d": -12,
      "quizzes_attempted": 2
    }
  ],
  "social_metrics": {
    "karma_growth": 70,
    "helpful_answers": 9,
    "tags_followed": ["python", "internship", "AR-VR"],
    "quizzes_attempted": 9,
    "upvotes": 22,
    "consecutive_active_days": 9,
    "profile_completeness": 85,
    "previous_profile_completeness": 27
  },
  "history": {
    "last_compliment_generated": "2025-06-15",
    "last_buddy_nudge": "2025-06-14"
  }
}
```

## stu_8905:

```json
{
  "user_id": "stu_8905",
  "buddies": [
    {
      "buddy_id": "stu_7093",
      "last_interaction_days": 12,
      "messages_sent": 2,
      "karma_change_7d": 4,
      "quizzes_attempted": 1
    },
    {
      "buddy_id": "stu_7220",
      "last_interaction_days": 1,
      "messages_sent": 4,
      "karma_change_7d": 4,
      "quizzes_attempted": 2
    }
  ],
  "social_metrics": {
    "karma_growth": 246,
    "helpful_answers": 41,
    "tags_followed": ["python", "internship", "AR-VR"],
    "quizzes_attempted": 44,
    "upvotes": 98,
    "consecutive_active_days": 11,
    "profile_completeness": 85,
    "previous_profile_completeness": 78
  },
  "history": {
    "last_compliment_generated": "2025-06-15",
    "last_buddy_nudge": "2025-06-14"
  }
}
```

# Testing Guide:

Unit tests for the compliment_generator.py and nudge_engine.py are in tests folder.

## Command To Run Unit Tests:

```json
 python -m pytest -v

 OR

pytest -v
```
---

# Deployment:

## This microservice is dockerised and deployed by the following commands:
```json
docker build -t social-vibe-engine .
docker tag social-vibe-engine rohan/social-vibe-engine:v1.0.1
docker push rohan3296/social-vibe-engine:v1.0.1

```
## To pull the image and run:
```json
docker pull rohan3296/social-vibe-engine:v1.0.1
docker run -d -p 8000:8000 rohan3296/social-vibe-engine:v1.0.1
http://localhost:8000/docs



```