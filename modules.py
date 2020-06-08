import psycopg2
import os
import pickle
from dotenv import load_dotenv
import pandas as pd
from fuzzywuzzy import fuzz, process
from joblib import load


load_dotenv()

#Load credentials from .env
name = os.environ["DB_NAME_AWS"]
password = os.environ["DB_PW_AWS"]
host = os.environ["DB_HOST_AWS"]
user = os.environ["DB_USER_AWS"]

pg_conn = psycopg2.connect(dbname=name,
                        user=user,
                        password=password,
                        host=host
                        )
## Curson is always open
pg_curs = pg_conn.cursor()

# Load in slimmed random forest pickled model
#test_model = pickle.load(open("random_forest_1.sav" , "rb"))
test_model = load("random_forest_2.joblib")

# Load the craigslist cleaned data
df_cl = pd.read_csv("data/model_and_image_url_lookup.csv")
# List of unique CL cars
cl_models = sorted(df_cl.model.unique())


class Pred:
    def __init__(
        self, 
        miles_per_year: int = 15000,
        num_years: int = 5,
        gas_cost: int = 3,
        electrical_cost: float = 0.12,
        maintenance_cost_per_year: int = 1000,
        make: str='Ford',
        model: str='F150 Pickup 4WD',
        year: int=2005):

        self.miles = miles_per_year
        self.years = num_years
        self.gas = gas_cost
        self.electrical = electrical_cost
        self.maint = maintenance_cost_per_year
        self.make = make
        self.model = model
        self.year = year
        self.manufacturer = make.lower()
        self.model_lower = model.lower()
        self.co2 = None

    def match_models(self):
        '''
        This function takes in a given model from the EPA dataset and
        uses the Fuzzy Wuzzy library to match the input string to the closest
        string in the Craigslist dataset.
        '''

        # Load the craigslist cleaned data
        df_cl = pd.read_csv("data/model_and_image_url_lookup.csv")
        # List of unique CL cars
        cl_models = sorted(df_cl.model.unique())

        model_ratios = []
        for car in cl_models:
            model_ratios.append(fuzz.ratio(self.model_lower, car))
        max_match = max(model_ratios)
        index_of_match = model_ratios.index(max_match)

        return cl_models[index_of_match]


    def get_car_pred(self):

        model_fz = self.match_models()

        input = pd.DataFrame({
        "year": [self.year],
        "manufacturer": [self.manufacturer],
        "model": [model_fz]
        })

        pred = test_model.predict(input)
        return pred[0]

    def get_comb_mpg(self):
        """Get the combined mpg"""
        pg_curs.execute(f"select AVG(comb08) FROM epa_vehicles_all WHERE make = '{self.make}' and model = '{self.model}' and year = '{self.year}';")
        return pg_curs.fetchall()[0][0]

    def get_comb_co2(self):
        """Get the combbined co2"""
        pg_curs.execute(f"SELECT AVG(co2tailpipegpm) FROM epa_vehicles_all WHERE make = '{self.make}' AND model = '{self.model}' AND year = {self.year};")
        return pg_curs.fetchall()[0][0]

    def co2_num_years(self):
        """CO2 over a X year period (Kg)"""
        self.co2 = self.get_comb_co2()
        total = self.co2 * self.miles * self.years/1000
        return total

    def get_fuel_cost(self):
        """5 year fuel cost"""
        return self.miles/ self.get_comb_mpg() * self.gas * self.years

    def cto(self):
        """Get 5 year cost to own"""
        cto = self.get_fuel_cost() + self.maint + self.get_car_pred()
        return cto

    def co2_offset(self):
        """How many trees to offset co2 emissions"""
        
        ## Number of kgs of CO2 absorbed by one tree per year
        tree_absorption = 21.7724
        return self.co2_num_years()/(tree_absorption * self.years)

    def fetch_img(self):
        """
        Get from sample input car to return the url. If none found,
        check next and previous year. If none available, give none found image
        """
        df_models = df_cl[df_cl['model'] == self.match_models()]
        df_models_at_year = df_models[df_models['year'] == self.year]
        index_of_model_year = df_models_at_year.index[0:10]

        list_urls = list(df_cl['image_url'][index_of_model_year])

        if len(index_of_model_year) < 1:
            df_models_at_year = df_models[df_models['year'] == (self.year + 1)]
            index_of_model_year = df_models_at_year.index[0:10]
            list_urls = list(df_cl['image_url'][index_of_model_year])

            if len(list_urls) == 0:
                df_models_at_year = df_models[df_models['year'] == (self.year - 1)]
                index_of_model_year = df_models_at_year.index[0:10]
                list_urls = list(df_cl['image_url'][index_of_model_year])
                #print('No cars in specified year, trying the previous year')  
                if len(list_urls) == 0:
                    return ['https://raw.githubusercontent.com/Lambda-School-Labs/street-smarts-ds/master/data/noImage_large.png']
                return list_urls  

            #print('No cars in specified year, trying the next year')
            return list_urls

        return list_urls

    




    

