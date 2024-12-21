from flask import Flask, render_template, request
import pandas as pd
import google.generativeai as genai

app = Flask(__name__)

# Load car and bike datasets
car_data = pd.read_csv('cars_dataset.csv')
bike_data = pd.read_csv('bikesCleaned.csv')

# Extract unique brand names from datasets
car_brands = car_data['Make'].unique().tolist()
bike_brands = bike_data['Brand'].unique().tolist()

# Configure Gemini AI API
genai.configure(api_key="AIzaSyB247i8r5oX120FrYYmhML15ZjvGiMxBRM")
model = genai.GenerativeModel("gemini-1.5-flash")

def get_relevant_documents(dataset, brand_name):
    """Retrieve relevant documents from the dataset for the given brand name."""
    relevant_docs = dataset[dataset['Brand' if 'Brand' in dataset.columns else 'Make'] == brand_name]
    return relevant_docs.to_dict('records') if not relevant_docs.empty else None

def generate_rag_response(choice, brand_name, retrieved_docs):
    """Combine retrieved documents with the AI model's generative capability."""
    try:
        # Combine retrieved documents into a single context string
        context = "\n".join([f"{key}: {value}" for doc in retrieved_docs for key, value in doc.items()])
        prompt = f"Based on the following details about {choice} brand {brand_name}, provide recommendations in point-wise format and ssuggest similiar brand's {choice}. Ensure the response is clear and free of JSON-like structures:\n\n{context}"
        
        # Generate response using Gemini AI
        response = model.generate_content(prompt)

        if response and response.text:
            # Clean the response to transform JSON-like structures into plain text
            recommendations = parse_json_to_points(response.text)

            # Process recommendations to replace ** with <b> and </b>
            processed_recommendations = [recommendation.replace("**", "<b>").replace("**", "</b>") for recommendation in recommendations]
            return processed_recommendations
        else:
            return ["No AI recommendations available."]
    except Exception as e:
        return [f"Error generating RAG response: {str(e)}"]

def parse_json_to_points(response_text):
    """Transform JSON-like response into a point-wise text format."""
    # Attempt to extract and clean JSON-like content
    import json

    try:
        # Extract JSON-like structure if present
        start = response_text.find("{[")
        end = response_text.rfind("]}")
        
        if start != -1 and end != -1:
            json_content = response_text[start + 2:end].strip()
            parsed_data = json.loads(f"[{json_content}]")  # Ensure valid JSON structure
            
            # Convert parsed JSON content into a point-wise text format
            points = []
            for item in parsed_data:
                for key, value in item.items():
                    points.append(f"- {key}: {value}")
            return points
        else:
            # Return the raw response text as-is in case JSON structure isn't found
            return [f"- {line.strip()}" for line in response_text.split("\n") if line.strip()]
    except Exception as e:
        # Fallback in case of parsing errors
        return [f"Error parsing response: {str(e)}", response_text]

@app.route('/', methods=['GET', 'POST'])
def index():
    previous_choice = 'car'  # Default to 'car'
    previous_brand = None

    if request.method == 'POST':
        choice = request.form.get('choice')
        brand_name = request.form.get('brand_name')
        price_range = request.form.get('price_range', '0,1000000').split(',')
        price_range = [int(x) for x in price_range if x.strip().isdigit()]
        price_range = price_range if len(price_range) == 2 else [0, 1000000]
        filter_by = request.form.get('filter')
        location = request.form.get('location', "All Locations")

        dataset = car_data if choice == 'car' else bike_data
        retrieved_docs = get_relevant_documents(dataset, brand_name)

        if not retrieved_docs:
            return render_template('error.html', message="No data found for the selected brand.")

        recommendations = generate_rag_response(choice, brand_name, retrieved_docs)

        filtered_data = filter_and_sort_data(dataset, brand_name, price_range, location, filter_by,
                                              'Kilometer Driven' if choice == 'car' else 'Mileage')
        return render_template('results.html',
                               results=filtered_data.head(5).fillna('-').to_dict('records'),
                               all_results=filtered_data.fillna('-').to_dict('records'),
                               type=choice,
                               ai_recommendations=recommendations)

    return render_template('index.html',
                           car_brands=car_brands,
                           bike_brands=bike_brands,
                           previous_choice=previous_choice,
                           previous_brand=previous_brand)

def filter_and_sort_data(data, brand_name, price_range, location, filter_by, mileage_col=None):
    filtered_data = data[(data['Brand' if 'Brand' in data.columns else 'Make'] == brand_name) &
                         (data['Price'] >= price_range[0]) &
                         (data['Price'] <= price_range[1])]

    if location != "All Locations":
        filtered_data = filtered_data[filtered_data['Location'] == location]

    if filter_by == 'low_price':
        filtered_data = filtered_data.sort_values(by='Price')
    elif filter_by == 'high_mileage' and mileage_col:
        filtered_data = filtered_data.sort_values(by=mileage_col, ascending=False)

    return filtered_data

if __name__ == '__main__':
    app.run(debug=True)
