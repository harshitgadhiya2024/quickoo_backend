import re, json, os
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from openai import OpenAI

os.environ["OPENAI_API_KEY"] = "sk-proj-4mfrOc29AjsBx1DzYmOmT3BlbkFJ84qcdYwaKQo7La0mC7Sp"
# model = ChatOpenAI(model="gpt-4")
model = ChatOpenAI(model_name="gpt-4o", temperature=0.7)

class AIintegration():

    def __int__(self):
        pass

    def clean_text(self, text):
        try:
            # Remove extra spaces and newlines
            text = re.sub(r'\n+', '\n', text)
            text = re.sub(r'\s+', ' ', text)
            symbol_pattern = r'[^\w\s.,]'

            # Use re.sub() to replace symbols with spaces
            cleaned_text = re.sub(symbol_pattern, ' ', text)

            return cleaned_text.strip()

        except Exception as e:
            print(f"{datetime.utcnow()}: Error in clean of any text: {e}")

    def extract_number(self, text):
        # This pattern matches integers or decimal numbers
        pattern = r'(\d+\.?\d*)'
        match = re.search(pattern, text)
        if match:
            # Convert to float for decimal values
            return float(match.group(1))
        else:
            return None

    def get_price_based_on_car_condition(self, car_model_name, how_old, kilometer, location):
        try:
            messages = [
                SystemMessage(
                    content="""
                    Could you please give me price per Kilometer based on only given car information like
                    car_model=car_model, how_much_old=how_much_old, on_road_kilometer=on_road_kilometer, location=location
                    Please Note: I did not have a another information of car so I want to make a price decision based on given car information also please give price between 5 to 12 INR per hour
                    Response format: {"price": "price"}
                    """),
                HumanMessage(content=f'car_model={car_model_name}, how_much_old={how_old}, on_road_kilometer={kilometer}, location={location}'),
            ]

            output = model.invoke(messages)
            get_content = json.loads(output.content)
            price = AIintegration().extract_number(get_content["price"])
            return price

        except Exception as e:
            print(f"{datetime.utcnow()}: Error in : {e}")

price = AIintegration().get_price_based_on_car_condition("Tata Punch", "2 year 5 month", "13467 KM", "india")
print(price)