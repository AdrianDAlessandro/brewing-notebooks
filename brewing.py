import json
import math
import random
import string

class BeerRecipe(object):
    # Define some constants
    EVAPORATION_RATE = 3 # During boil (L/hr)
    GRAIN_ABSORPTION_RATE = 1 # Volume loss from grain (L/kg)
    EFFICIENCY = 0.6 # Efficiency of getting sugars from malt (%)
    FERMENTABILITY = 0.75 # Proportion of sugars that are fermentable in wort
    
    def __init__(self, name="", batch_size=20, boil_time=60, bottle_size=450, malt={},
                 hops={}, yeast="NA", recipe_file=None, commandline_build=False):
        
        # Set the variable as properties, so when the value of one is changed
        # the impacts of that are filtered through
        if name == "":
            CONSONANTS = "".join(set(string.ascii_lowercase) - set("aeiou"))
            self.name = ""
            for i in range(random.randint(3,6)):
                if i % 2 == 0:
                    self.name += random.choice(CONSONANTS)
                else:
                    self.name += random.choice("aeiou")
        else:
            self.name = name
        
        self.batch_size = batch_size
        self.malt = malt
        self.hops = hops
        self.yeast = yeast
        self.boil_time = boil_time
        self.bottle_size = bottle_size
        
        # Malt and Hops recipe specifics
        if recipe_file:
            self.read_recipe(recipe_file)
        elif commandline_build:
            self.__builder()
            
        

    def __builder(self):
        number_of_malts = int(input("How many malt varieties do you have? "))
        number_of_hops = int(input("How many hops varieties do you have? "))
        
        for n in range(number_of_malts):
            variety = input(f"Name of malt variety {n + 1}: ")
            mass = float(input(f"Mass of {variety} (kg): "))
            hwe = float(input(f"HWE of {variety}: "))
            ebc = float(input(f"EBC of {variety}: "))
            
            self.add_malt(variety, mass, hwe, ebc)
            
        for n in range(number_of_hops):
            variety = input(f"Name of hops variety {n + 1}: ")
            alpha_acids = float(input(f"Alpha Acids of {variety} (%): "))
            additions = int(input(f"How many additions of {variety}? "))
            
            times = []
            masses = []
            for m in range(additions):
                times.append(float(input(f"Time of addition {m + 1} (min): ")))
                masses.append(float(input(f"Mass of addition {m + 1} (g): ")))
            
            self.add_hops(variety, alpha_acids, masses, times)
            
    # Define read_only (dynamically allocated) properties:
    @property
    def grain_mass(self):
        return sum([v['Mass'] for v in self.malt.values()])
    @property
    def trub_loss(self):
        return 0.05 * self.batch_size
    @property
    def kettle_loss(self):
        return 0.10 * self.batch_size
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
            + self.EVAPORATION_RATE
            * (self.boil_time / 60)
        )
    @property
    def strike_water(self):
        return 3 * self.grain_mass
    @property
    def grain_absorption(self):
        return self.GRAIN_ABSORPTION_RATE * self.grain_mass
    @property
    def first_runnings(self):
        return self.strike_water - self.grain_absorption
    @property
    def sparge_water(self):
        return self.pre_boil_vol - self.first_runnings
    @property
    def alcohol_percentage(self):
        return (self.original_gravity - self.final_gravity) * 131.25
    @property
    def standard_drinks(self):
        return round(
            self.bottle_size * (self.alcohol_percentage / 100) / 12.5, 2
        )
    @property
    def priming_sugar(self):
        """
        Equation from here: https://www.brewcabin.com/priming-sugar/
        
        `Cbeer = Cflat-beer + 0.5 * mtable-sugar / Vbeer`
        Aim for: Cbeer = 2.2
        Assume Cflat-beer = 0.85 (20 degrees C)
        """
        target_co2 = 2.2
        current_co2 = 0.85
        
        return 2 * self.fermenter_vol * (target_co2 - current_co2)
    @property
    def ibu(self):
        ibu = 0
        for v in self.hops.values():
            for mass, time in zip(v['Masses'], v['Times']):
                ibu += self.calculate_ibu(mass, self.batch_size,
                                          v['Alpha Acids'],
                                          boil_time=time)
        return ibu
    @property
    def ebc(self):
        ebc = 0
        for v in self.malt.values():
            ebc += self.calculate_ebc(v['Mass'], v['EBC'], self.batch_size)
            
        return ebc
    @property
    def potential_hwe(self):
        """
        Calculate Expected Original Gravity

        Mash Efficiency - Calculations from:
        https://aussiehomebrewer.com/threads/working-out-mash-efficiency-in-metric.35490/
        
        The H.W.E (hot water extract) value for the malt is the amount of
        sugar in the wort 386 is the maximum (pure sugar) so every malt is
        given as a % of that
        """
        if not self.malt:
            return None

        hwe_list = []
        for v in self.malt.values():
            tmp_hwe = v['Mass'] * 386 * v['HWE'] / self.post_boil_vol
            hwe_list.append(tmp_hwe)
        
        return sum(hwe_list)
    
    # Define adjustable properties:
    @property
    def original_gravity(self):
        try:
            return self.__original_gravity
        except AttributeError:
            hwe = self.EFFICIENCY * self.potential_hwe
            return hwe / 1000 + 1.0
    @original_gravity.setter
    def original_gravity(self, original_gravity):
        self.__original_gravity = original_gravity
        
        # Adjust self.EFFICIENCY to match real original_gravity
        hwe = 1000 * (original_gravity - 1)
        self.EFFICIENCY = hwe / self.potential_hwe
        print(
            "The mash efficiency was {0:.0f}%".format(
                100 * self.EFFICIENCY
            )
        )
    
    @property
    def final_gravity(self):
        try:
            return self.__final_gravity
        except AttributeError:
            return (
                self.original_gravity
                - (self.original_gravity - 1)
                * self.FERMENTABILITY
            )
    @final_gravity.setter
    def final_gravity(self, final_gravity):
        self.__final_gravity = final_gravity
        
        # Adjust self.FERMENTABILITY to match real final_gravity
        self.FERMENTABILITY = (
            (final_gravity - self.original_gravity)
            / (1- self.original_gravity)
        )
        print(
            "The wort fermentability was {0:.0f}%".format(
                100 * self.FERMENTABILITY
            )
        )
    
    # Define more complex methods
    def add_malt(self, variety, mass, hwe, ebc):
        self.malt[variety] = {
            'Mass' : mass,
            'HWE' : hwe,
            'EBC' : ebc
        }
        
    def add_hops(self, variety, alpha_acids, masses, times):
        for i, time in enumerate(times):
            if 'dry' in str(time).lower():
                times[i] = -1
        
        self.hops[variety] = {
            "Alpha Acids" : alpha_acids,
            "Masses" : masses,
            "Times" : times
        }
        try:
            self.boil_time = max(self.boil_time, times)
        except TypeError:
            self.boil_time = max(self.boil_time, *times)
            
    def scale_brew(self, batch_size):
        scaling = batch_size/self.batch_size
        
        self.batch_size = batch_size
        
        for variety in self.malt:
            self.malt[variety]['Mass'] *= scaling
        
        for variety in self.hops:
            self.hops[variety]['Masses'] = [mass * scaling for mass in self.hops[variety]['Masses']]
        
        return {
            "Malt" : self.malt,
            "Hops" : self.hops,
            "Strike Water" : self.strike_water,
            "Sparge Water" : self.sparge_water,
            "Priming Sugar" : self.priming_sugar,
            "Batch Size" : self.batch_size
        }
    
    def calculate_ibu(self, mass_hops, batch_size, aa_rating, boil_time,
            boil_gravity=None):
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
            if not boil_gravity:
                raise AttributeError("Cannot calculate IBU without malt")
        
        # Account for dry hopping (flagged as negative boil time)
        boil_time = max(0, boil_time)
        
        boil_time_factor = (1 - math.exp(-0.04 * boil_time)) / 4.15
        
        bigness_factor = 1.65 * 0.000125**(boil_gravity - 1)

        aa_utilization = bigness_factor * boil_time_factor

        aa_concentration = aa_rating / 100 * mass_hops * 1000 / batch_size
        
        return aa_utilization * aa_concentration

    def calculate_ebc(self, grain_mass, malt_colour, batch_size):
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
    
    # Output methods
    def __str__(self):
        description = "{0} Brewing Instructions\n\nMalt Bill:\n".format(
            self.name.title()
        )
        
        malt_list = []
        for k, v in self.malt.items():
            malt_list.append(
                "\t{0:.3f}kg of {1} ({2}HWE and {3}EBC)\n".format(
                    v['Mass'], k, v['HWE'], v['EBC']
                )
            )

        description += "".join(malt_list) + "Hops:\n"
        
        hops_list = []
        for k, v in self.hops.items():
            hops_list.append(
                "\t{0} ({1}% AA):\n".format(
                    k, v['Alpha Acids']
                )
            )
            for mass, time in zip(v['Masses'], v['Times']):
                hops_list.append(
                    "\t\t{0:.0f}g at {1:2d} minutes\n".format(
                        mass, time
                    )
                )

        description += "".join(hops_list)
        
        description += "Yeast:\n\t{0}\n".format(self.yeast)
        
        description += "Properties:\n"
        description += "\tAlcohol: {0:.1f}%\n\tIBU: {1:.0f}\n\tEBC: {2:.0f}\n".format(
            self.alcohol_percentage, self.ibu, self.ebc
        )
        
        description += "Water:\n"
        description += "\tStrike Water: {0:.1f}L\n\tSparge Water: {1:.1f}L\n\tBatch Size: {2:.1f}L\n".format(
            self.strike_water, self.sparge_water, self.batch_size
        )
        
        description += "Priming Sugar: {0:.0f}g".format(self.priming_sugar)
        
        return description
    
    def check_recipe_file(self, recipe_file):
        if recipe_file:
            self.recipe_file = recipe_file
        else:
            self.recipe_file = "".join(self.name.split()) + ".json"
    
    def read_recipe(self, recipe_file):
        self.check_recipe_file(recipe_file)
        
        with open(self.recipe_file) as f:
            recipe = json.load(f)
        
        self.malt = recipe["Malt"]
        self.hops = recipe["Hops"]
        self.yeast = recipe["Yeast"]
        self.batch_size = recipe["Batch Size"]
        self.boil_time = recipe["Boil Time"]
                             
        return recipe
    
    def save_recipe(self, recipe_file):
        self.check_recipe_file(recipe_file)
        
        recipe = {
            "Malt" : self.malt,
            "Hops" : self.hops,
            "Yeast" : self.yeast,
            "Strike Water" : self.strike_water,
            "Sparge Water" : self.sparge_water,
            "Original Gravity" : self.original_gravity,
            "Final Gravity" : self.final_gravity,
            "Priming Sugar" : self.priming_sugar,
            "Batch Size" : self.batch_size,
            "Boil Time" : self.boil_time,
            "IBU" : self.ibu,
            "EBC" : self.ebc
        }
        with open(self.recipe_file, 'w') as f:
            json.dump(recipe, f, indent=4)
            
if __name__ == '__main__':
    BeerRecipe(commandline_build=True).save_recipe(None)
    
