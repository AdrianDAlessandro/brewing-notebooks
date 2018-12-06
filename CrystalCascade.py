import math

def make_widget(value, description):
    style = {'description_width' : '50%'}
    return widgets.FloatText(value=value, description=description, style=style)

# Create widgets
batch_size_box = make_widget(4.25, 'Batch Size (L) =')
grain_mass_box = make_widget(1.25, 'Total Grain Mass (kg) =')
trub_loss_box = make_widget(0.6, 'Trub Loss (L) =')
kettle_loss_box = make_widget(0.4, 'Kettle Loss (L) =')
boil_time_box = make_widget(1, 'Boil Time (hr) =')
bottle_size_box = make_widget(450, 'Bottle Size (mL) =')

# Create boxes to display widgets
left_box = widgets.VBox([batch_size_box,
                         grain_mass_box])
mid_box = widgets.VBox([trub_loss_box,
                        kettle_loss_box])
right_box = widgets.VBox([boil_time_box,
                          bottle_size_box])
widgets.HBox([left_box, mid_box, right_box])

# Set values
batch_size = batch_size_box.value
grain_mass = grain_mass_box.value
trub_loss = trub_loss_box.value
kettle_loss = kettle_loss_box.value
boil_time = boil_time_box.value
bottle_size = int(bottle_size_box.value)

print(batch_size, 'L')
print(grain_mass, 'kg')
print(trub_loss, 'L')
print(kettle_loss, 'L')
print(boil_time, 'hr')
print(bottle_size, 'mL')


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


# This will be a module (file)
class constants(object):
    # Approximate rate of evaporation at boil (L/hr)
    evap_rate = 3
    # Approximate loss of volume due to grain absorption (L/kg)
    grain_abs_rate = 1
    # Efficiency of getting sugars from malt
#     eff = ?????????

# Calculte Water Volumes
fermenter_vol = batch_size + trub_loss
post_boil_vol = fermenter_vol + kettle_loss
pre_boil_vol = post_boil_vol + constants.evap_rate * boil_time

strike_water = 3 * grain_mass
grain_absorption = constants.grain_abs_rate * grain_mass
first_runnings = strike_water - grain_absorption

sparge_water = pre_boil_vol - first_runnings


print('Strike Water = ', strike_water)
print('Grain Absorption = ', grain_absorption)
print('First Runnings = ', first_runnings)

print('Sparge Water = ', sparge_water)

print('Pre-boil Volume = ', pre_boil_vol)
print('Post-boil Volume = ', post_boil_vol)
print('Fermenter volume = ', fermenter_vol)


# ### Calculate Expected Original Gravity

print(batch_size, 'L;', grain_mass, 'kg')


# Mash Efficiency - from https://aussiehomebrewer.com/threads/working-out-mash-efficiency-in-metric.35490/
# 
# How it works is all malts and adjuncts etc give a different gravity. 
# The specs are all written as H.W.E which is hot water extract with sugar being the highest at 386 so everything else is given as a % of that. ie, pale malt is around 81% which gives you around 309. this is the total gravity you can get with 1 kilo in 1 litre but it is impossible to get this, this is 100% effeincy.
# the same goes for american calcs but its in P.P.G which is the gravity of 1 pound in 1 gallon. The same specs are used ie. 81% for pale malt gives you 37 points of gravity.
# 
# So a simple example to work out total potential for 5 kg of pale malt in 23 litres is
# 5 x 309 / 23 = 67 (1.067)
# 
# now to work out your effiency you divide the gravity you got with this brew. Say you got 1.050 so 50/67 =.74 you got 74% effiency.
# Then next time when you do the calc. 5 x 309 /23 =you simply times this by .74 .
# This gives you your expected gravity, 
# 
# For your first batches i would stick to using 60-65%.
# So do the 5 x 309/ 23 = 67.
# then times 67 by .65 = 43(1.043)
# 
# p.s the hwe numbers are all on the malt craft site other malts like crystal malt are around 75% some malts can be lower and some higher.
# to get the number times 386 by the percent as a decimal point ie pale malt at 81% gives you 386 x .81 =312 
# 
# Ale -------81% X 386 = 312
# Pilsner----------------81%
# Hoepfner Munich----80% 308
# Melanoiden--------- -80%
# Caramalt pils---------79% 305
# Crystal---------------- 75%
# 
# Well, it's the method you will see in Australia. 
# 
# Say the HWE is 308 litre degrees per kilogram for a malt. 
# That means 5kg in 20L will give you : (308 x 5)/20 = 77. i.e. 1.077 SG at 100% efficiency. Multiply that by your efficiency (eg. 75%) gives you 77 x 0.75 = 57.75 or close enough to 1.058.


# Swapped strike and sparge waters
malt = {
    '2-Row' : 1.015,
    'Crystal' : 250
}
hops = {
    '60m' : 6,
    '30m' : 6,
    '5m' : 6,
    'Dry' : 4
}

water_gravity = 1.003
original_gravity = 1.056
final_gravity = 1.01

prc_vol = (original_gravity - final_gravity) * 131.25
std_drinks = bottle_size * (prc_vol/100) / 12.5

print(f"Final alcohol percentage = {prc_vol:.2}% ABV")
print(f"{std_drinks:.2} Standard Drinks per {bottle_size}mL bottle")


# ### Calculate IBU
# http://www.backtoschoolbrewing.com/blog/2016/9/5/how-to-calculate-ibus
# http://www.realbeer.com/hops/research.html
# 
# To calculate IBUs, the formula is simple:
# `IBUs = decimal alpha acid utilization * mg/l of added alpha acids`
# `mg/l of added alpha acids = decimal AA rating * grams hops * 1000 / volume of finished beer in liters`
# `decimal alpha acid utilization = Bigness factor * Boil Time factor`
# `Bigness factor = 1.65 * 0.000125^(wort gravity - 1)`
# `Boil Time factor = (1 - e^(-0.04 * time in mins) ) / 4.15`

def ibu(mass_hops, batch_size, aa_rating, boil_gravity=original_gravity, boil_time=60):
    boil_time_factor = (1 - math.exp(-0.04 * boil_time)) / 4.15
    
    bigness_factor = 1.65 * 0.000125**(boil_gravity - 1)
    
    aa_utilization = bigness_factor * boil_time_factor
    
    aa_concentration = aa_rating / 100 * mass_hops * 1000 / batch_size
        
    return aa_utilization * aa_concentration

ibu(6, 4, 5.5, boil_time=60) + ibu(6, 4, 5.5, boil_time=30) + ibu(6, 4, 5.5, boil_time=5)


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

def ebc(grain_mass, malt_colour, batch_size):
    return 1.97 * (1.4922 * ((grain_mass*2.2*malt_colour/1.97)/(batch_size*0.264172))**0.6859)

ebc(0.51, 3.5, 4) + ebc(0.505, 6, 4) + ebc(0.250, 50, 4)

