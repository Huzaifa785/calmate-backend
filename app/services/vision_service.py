# app/services/vision_service.py
from openai import OpenAI
from typing import Dict, Any, Optional
from fastapi import HTTPException
import json
from app.config import settings
from app.models.food_log import FoodLog
import base64
import requests


class VisionService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    async def analyze_food(self, image_url: str) -> Dict[str, Any]:
        try:
            print(f"Downloading image from: {image_url}")
            
            # Download image with auth header
            response = requests.get(
                image_url,
                headers={
                    "X-Appwrite-Project": settings.APPWRITE_PROJECT_ID,
                    "X-Appwrite-Key": settings.APPWRITE_API_KEY
                }
            )
            response.raise_for_status()
            
            print("Image downloaded successfully")
            base64_image = base64.b64encode(response.content).decode('utf-8')
            print("Image encoded to base64")

            try:
                openai_response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text",
                            "text": """Analyze this food and provide nutrition information in exactly this JSON format:
                            {
                                "food_name": "name of the food",
                                "portion_size": number_in_grams,
                                "calories": number,
                                "macronutrients": {
                                    "protein": number_in_grams,
                                    "carbs": number_in_grams,
                                    "fats": number_in_grams
                                }
                            }
                            Just return the JSON, no additional text."""},
                            {"type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }}
                        ]
                    }],
                    max_tokens=300
                )
                print("Raw OpenAI response:", openai_response)
                
                content = openai_response.choices[0].message.content
                print("Content from OpenAI:", content)
                
                parsed_result = self._parse_response(content)
                print("Parsed result:", parsed_result)
                
                return parsed_result
                    
            except Exception as openai_error:
                print(f"OpenAI API error: {str(openai_error)}")
                raise

        except requests.exceptions.RequestException as e:
            print(f"Download error: {str(e)}")
            raise HTTPException(status_code=500, detail="Error downloading image")
        except Exception as e:
            print(f"Vision Analysis Error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    def _parse_response(self, content: str) -> Dict[str, Any]:
        """
        Parses the OpenAI response into structured data.
        """
        try:
            # Remove markdown code block indicators
            clean_content = content.replace('```json', '').replace('```', '').strip()
            
            # Parse JSON
            data = json.loads(clean_content)
            
            # No need to modify the data as it's already in our format
            result = {
                "food_name": data["food_name"],
                "portion_size": float(data["portion_size"]),
                "calories": float(data["calories"]),
                "macronutrients": {
                    "protein": float(data["macronutrients"]["protein"]),
                    "carbs": float(data["macronutrients"]["carbs"]),
                    "fats": float(data["macronutrients"]["fats"])
                }
            }
            
            print("Parsed data:", result)
            return result
                
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {str(e)}")
            print("Content that failed to parse:", content)
            raise HTTPException(
                status_code=500,
                detail=f"Error parsing nutrition data: {str(e)}"
            )
        except Exception as e:
            print(f"Unexpected parsing error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error processing response: {str(e)}"
            )

    def validate_image(self, image_url: str) -> bool:
        """
        Validates if the image is appropriate for food analysis.
        """
        # Add image validation logic here
        return True

    async def get_nutrition_recommendations(self, food_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Provides nutrition recommendations based on analyzed food.
        """
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "user",
                        "content": f"Given this food: {food_data['food_name']} "
                        f"with {food_data['calories']} calories, "
                        "provide brief nutrition recommendations."
                    }
                ]
            )
            return {
                "recommendations": response.choices[0].message.content,
                "healthiness_score": self._calculate_health_score(food_data)
            }
        except Exception as e:
            return {"recommendations": "Unable to generate recommendations."}

    def _calculate_health_score(self, food_data: Dict[str, Any]) -> float:
        """
        Calculates a health score based on macronutrients.
        """
        try:
            protein = food_data["macronutrients"]["protein"]
            carbs = food_data["macronutrients"]["carbs"]
            fats = food_data["macronutrients"]["fats"]

            # Simple scoring based on macro ratios
            total = protein + carbs + fats
            if total == 0:
                return 0

            protein_ratio = protein / total
            score = (
                (protein_ratio * 40) +  # Protein is weighted more
                ((1 - abs(carbs/total - 0.4)) * 30) +  # Carbs should be around 40%
                ((1 - abs(fats/total - 0.3)) * 30)     # Fats should be around 30%
            )

            return min(max(score, 0), 100)  # Normalize between 0-100
        except:
            return 0
