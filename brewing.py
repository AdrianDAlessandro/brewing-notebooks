import json
import math

class BeerRecipe(object):
    def __init__(self, name="", batch_size=20, grain_mass=5, trub_loss=None,
                 kettle_loss=None, boil_time=60, bottle_size=450):
        
        # Define some constants
        self.constants = {
            "Evaporation Rate" : 3, # During boil (L/hr)
            "Grain Absorption Rate" : 1, # Volume loss from grain (L/kg)
            "Efficiency" : 0.6, # Efficiency of getting sugars from malt (%)
            "Fermentability" : 0.75
        }
        
        # Set the variable as properties, so when the value of ones is changed
        # the impacts of that are filtered through
        if name == "":
            self.__builder()
        else:
            self.name = name
            self.batch_size = batch_size
            self.grain_mass = grain_mass
        
        if trub_loss is None:
            self.trub_loss = 0.05 * self.batch_size
        else:
            self.trub_loss = trub_loss
        
        if trub_loss is None:
            self.kettle_loss = 0.10 * self.batch_size
        else:
            self.kettle_loss = kettle_loss
        
        self.boil_time = boil_time
        self.bottle_size = bottle_size

    def __builder(self):
        self.name = input("What is your beer called? ")
        self.batch_size = float(input("What is your batch size (L)? "))
        self.grain_mass = float(input("Grain mass (kg)? "))
    
    # Define adjustable properties:
#     @property
#     def tester(self):
#         return self.__tester
#     @tester.setter
#     def tester(self, tester):
#         self.__tester = tester
    
    
    # Define read_only (dynamically allocated) properties:
    @property
    def fermenter_vol(self):
        return self.batch_size + self.trub_loss
    @property
    def post_boil_vol(self):
        return self.fermenter_vol + self.kettle_loss
    @property
    def pre_boil_vol(self):
        return (
            self.post_boil_vol
            + self.constants["Evaporation Rate"]
            * self.boil_time
        )
    @property
    def strike_water(self):
        return 3 * self.grain_mass
    @property
    def grain_absorption(self):
        return self.constants["Grain Absorption Rate"] * self.grain_mass
    @property
    def first_runnings(self):
        return self.strike_water - self.grain_absorption
    @property
    def sparge_water(self):
        return self.pre_boil_vol - self.first_runnings
    @property
    def original_gravity(self):
        return self.hwe2gravity(
            self.expected_original_hwe(self.grain_mass, 0.8)
        )
    @property
    def final_gravity(self):
        return (
            self.original_gravity
            - (self.original_gravity - 1)
            * self.constants["Fermentability"]
        )
    @property
    def alcohol_percentage(self):
        return (self.original_gravity - self.final_gravity) * 131.25
    @property
    def standard_drinks(self):
        return round(
            self.bottle_size * (self.alcohol_percentage / 100) / 12.5, 2
        )
    
    
    # Define more complex methods
    def expected_original_hwe(self, grain_mass, malt_hwe):
        """
        Calculate Expected Original Gravity

        Mash Efficiency - Calculations from:
        https://aussiehomebrewer.com/threads/working-out-mash-efficiency-in-metric.35490/
        
        The H.W.E (hot water extract) value for the malt is the amount of
        sugar in the wort 386 is the maximum (pure sugar) so every malt is
        given as a % of that
        """
        potential_hwe = grain_mass * 386 * malt_hwe / self.post_boil_vol

        original_hwe = self.constants["Efficiency"] * potential_hwe

        return original_hwe

    def hwe2gravity(self, hwe):
        try:
            total_hwe = 0
            for val in hwe:
                total_hwe += val
        except:
            total_hwe = hwe

        gravity = round(total_hwe / 1000 + 1.0, 3)

        return gravity

    def calculate_ibu(self, mass_hops, batch_size, aa_rating,
            boil_gravity=None, boil_time=60):
        """
        Calculate IBU
        http://www.backtoschoolbrewing.com/blog/2016/9/5/how-to-calculate-ibus
        http://www.realbeer.com/hops/research.html
        
        To calculate IBUs, the formula is:
        `IBUs = decimal alpha acid utilization * mg/l of added alpha acids`
        `mg/l of added alpha acids = decimal AA rating * grams hops * 1000
                                     / volume of finished beer in liters`
        `decimal alpha acid utilization = Bigness factor * Boil Time factor`
        `Bigness factor = 1.65 * 0.000125^(wort gravity - 1)`
        `Boil Time factor = (1 - e^(-0.04 * time in mins) ) / 4.15`
        """
        if boil_gravity is None:
            boil_gravity = self.original_gravity
        
        boil_time_factor = (1 - math.exp(-0.04 * boil_time)) / 4.15
        
        bigness_factor = 1.65 * 0.000125**(boil_gravity - 1)

        aa_utilization = bigness_factor * boil_time_factor

        aa_concentration = aa_rating / 100 * mass_hops * 1000 / batch_size
        
        return aa_utilization * aa_concentration

    def ebc(self, grain_mass, malt_colour, batch_size):
        """
        Calculate EBC
        http://beersmith.com/blog/2008/04/29/beer-color-understanding-srm-lovibond-and-ebc/
        http://homebrewtechniques.com/mashing/how-do-you-calculate-beer-colour/
        
        The calculation we use to work out the colour value for our beer is:
        MCU = weight of malt (in lbs) * malt colour (lovibond)
              / volume (in gallons)
        
        (lovibond = SRM)
        To convert our recipe from kg and litres into US gallons and lbs we
        use the following conversion factors:
        
        1 litre = 0.264172 US gallons
        1 kg = 2.20462 lbs.
        SRM = 1.4922 * MCU^0.6859
        EBC = 1.97 * SRM 
        """
        mcu = (grain_mass * 2.2 * malt_colour / 1.97) / (batch_size * 0.264172)
        
        srm = 1.4922 * mcu**0.6859
        
        return 1.97 * srm
    
    def calculate_priming_sugar(self, target_co2=2.2, current_co2=0.85):
        """
        Equation from here: https://www.brewcabin.com/priming-sugar/
        """
        priming_sugar = 2 * self.fermenter_vol * (target_co2 - current_co2)
        return priming_sugar
    
    def read_recipe(self, recipe_file=None):
        if recipe_file is None:
            recipe_file = self.name + ".json"
        with open(recipe_file) as f:
            self.json = json.load(f)
        return self.json
    
    def save_recipe(self, recipe_file=None):
        if recipe_file is None:
            recipe_file = self.name + ".json"
        with open(recipe_file, 'w') as f:
            json.dump(self.json, f, indent=4)
            
