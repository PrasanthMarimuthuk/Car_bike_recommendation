from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

# Load car and bike datasets
car_data = pd.read_csv('cars_dataset.csv')
bike_data = pd.read_csv('bikesCleaned.csv')

# Extract unique brand names from datasets
car_brands = car_data['Make'].unique().tolist()
bike_brands = bike_data['Brand'].unique().tolist()


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        choice = request.form.get('choice')
        brand_name = request.form.get('brand_name')
        price_range = request.form.get('price_range', '0,1000000').split(',')
        price_range = [int(x) for x in price_range if x.strip() != '']
        filter = request.form.get('filter')
        location = request.form.get('location')

        if len(price_range) < 2:
            price_range = [0, 1000000]  # Default price range

        if choice == 'car':
            recommended_cars = car_data[(car_data['Make'] == brand_name) & 
                                        (car_data['Price'] >= price_range[0]) & 
                                        (car_data['Price'] <= price_range[1])]
            recommended_cars = recommended_cars.dropna()  # Remove rows with NaN values
            if location != "All Locations":
                recommended_cars = recommended_cars[recommended_cars['Location'] == location]
            if filter == 'low_price':
                recommended_cars = recommended_cars.sort_values(by='Price')
            elif filter == 'high_mileage':
                recommended_cars = recommended_cars.sort_values(by='Kilometer', ascending=False)
            return render_template('results.html', results=recommended_cars.head(5).to_dict('records'), all_results=recommended_cars.to_dict('records'), type='cars')
        elif choice == 'bike':
            recommended_bikes = bike_data[(bike_data['Brand'] == brand_name) & 
                                          (bike_data['Price'] >= price_range[0]) & 
                                          (bike_data['Price'] <= price_range[1])]
            recommended_bikes = recommended_bikes.dropna()  # Remove rows with NaN values
            if location != "All Locations":
                recommended_bikes = recommended_bikes[recommended_bikes['Location'] == location]
            recommended_bikes = recommended_bikes[['Brand','Model','Price','Max power','Max torque','Cooling System', 'Transmission','Fuel Tank Capacity','Location','Mileage','Top speed','Kerb weight','Kilometer Driven']]
            if filter == 'low_price':
                recommended_bikes = recommended_bikes.sort_values(by='Price')
            elif filter == 'high_mileage':
                recommended_bikes = recommended_bikes.sort_values(by='Mileage', ascending=False)
            return render_template('results.html', results=recommended_bikes.head(5).to_dict('records'), all_results=recommended_bikes.to_dict('records'), type='bikes')
    return render_template('index.html', car_brands=car_brands, bike_brands=bike_brands)


if __name__ == '__main__':
    app.run(debug=True)