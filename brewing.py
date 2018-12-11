import json
import math

class BeerRecipe(object):
    def __init__(self, batch_size, grain_mass, trub_loss, kettle_loss, boil_time, bottle_size):
        
        # Define some constants
        constants = {
            "Evaporation Rate" : 3, # Approximate rate of evaporation at boil (L/hr)
            "Grain Absorption Rate" : 1, # Approximate loss of volume due to grain absorption (L/kg)
            "Efficiency" : 0.5 # Efficiency of getting sugars from malt
        }
        
        # ### Calculate Water amounts
        # Need functions to take in batch size and work out the amounts all the way to strike water, inculding assumptions for losses etc.
        # Calculations and definitions from [Mash Hacks](https://mashhacks.com/how-to-calculate-water-volumes-for-brewing/):
        # 
        # - **Strike Water** - The starting amount of hot water (usually between 60C and 80C) that is used for the mash (adding grain to water).
        # - **Grain Absorption** - The amount of water absorbed by the grain.
        # - **First Runnings** - The amount of wort (sugary water) that is collected from the mash tun after your mash has finished.
        # - **Sparge Water** - Water that is added to the mash tun after mashing to rinse the grain of any left over sugars.
        # - **Pre-Boil Volume** - The amount of wort (sugary water) that is in your kettle before you start your boil.
        # - **Evaporation Rate** - The amount of water that is boiled off. Usually in Litres per Hour (or Gal/hr).
        # - **Post-Boil Volume** - The amount of wort left after you finish the boil.
        # - **Kettle Loss** - The amount of wort (if any) left at the bottom of the kettle that was not transferred to the fermenter.
        # - **Fermenter Volume** - The amount of wort you were able to get out of the kettle and put into the fermenter.
        # - **Trub Loss** aka *Fermenter loss* - The amount of beer (if any) at the bottom of the fermenter that was not transferred into bottles or kegs.
        # - **Batch Size** - The amount of beer that you were able to get out of the fermenter and put into bottles or kegs.

        # Calculte Water Volumes
        fermenter_vol = batch_size + trub_loss
        post_boil_vol = fermenter_vol + kettle_loss
        pre_boil_vol = post_boil_vol + constants["Evaporation Rate"] * boil_time

        strike_water = 3 * grain_mass
        grain_absorption = constants["Grain Absorption Rate"] * grain_mass
        first_runnings = strike_water - grain_absorption

        sparge_water = pre_boil_vol - first_runnings

        
        self.original_gravity = 1.044
        self.final_gravity = 1.01

        prc_vol = self.alcohol_percentage(self.original_gravity, self.final_gravity)
        std_drinks = self.standard_drinks(bottle_size, prc_vol)

        print(f"Final alcohol percentage = {prc_vol:.2}% ABV")
        print(f"{std_drinks:.2} Standard Drinks per {bottle_size}mL bottle")
        
    def alcohol_percentage(self, original_gravity, final_gravity):
        return (original_gravity - final_gravity) * 131.25

    def standard_drinks(self, bottle_size, prc_vol):
        return bottle_size * (prc_vol/100) / 12.5
    
    def expected_original_hwe(self, grain_mass, malt_hwe):
        """
        # ### Calculate Expected Original Gravity

        # Mash Efficiency - from https://aussiehomebrewer.com/threads/working-out-mash-efficiency-in-metric.35490/
        # The H.W.E (hot water extract) value for the malt is the amount of sugar in the wort
        # 386 is the maximum (pure sugar) so every malt is given as a % of that
        """
        potential_hwe = grain_mass * 386 * malt_hwe / batch_size

        original_hwe = 0.5 * potential_hwe

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

    def ibu(self, mass_hops, batch_size, aa_rating, boil_gravity=None, boil_time=60):
        """
        # ### Calculate IBU
        # http://www.backtoschoolbrewing.com/blog/2016/9/5/how-to-calculate-ibus
        # http://www.realbeer.com/hops/research.html
        # 
        # To calculate IBUs, the formula is:
        # `IBUs = decimal alpha acid utilization * mg/l of added alpha acids`
        # `mg/l of added alpha acids = decimal AA rating * grams hops * 1000 / volume of finished beer in liters`
        # `decimal alpha acid utilization = Bigness factor * Boil Time factor`
        # `Bigness factor = 1.65 * 0.000125^(wort gravity - 1)`
        # `Boil Time factor = (1 - e^(-0.04 * time in mins) ) / 4.15`
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
        # ### Calculate EBC
        # http://beersmith.com/blog/2008/04/29/beer-color-understanding-srm-lovibond-and-ebc/
        # http://homebrewtechniques.com/mashing/how-do-you-calculate-beer-colour/
        # 
        # The calculation we use to work out the colour value for our beer is:
        # MCU = weight of malt (in lbs) x malt colour (in lovibond) / volume (in gallons)
        # (lovibond = SRM)
        # To convert our recipe from kg and litres into US gallons and lbs we use the following conversion factors:
        # 1 litre = 0.264172 US gallons
        # 1 kg = 2.20462 lbs.
        # SRM = 1.4922 * MCU^0.6859
        # EBC = 1.97 * SRM 
        """
        return 1.97 * (1.4922 * ((grain_mass*2.2*malt_colour/1.97)/(batch_size*0.264172))**0.6859)
    
    def read_recipe(self, recipe_file):
        with open(recipe_file) as f:
            self.json = json.load(f)
        return self.json
    
    def write_recipe(self, recipe_file):
        with open(recipe_file, 'w') as f:
            json.dump(self.json, f, indent=4)
