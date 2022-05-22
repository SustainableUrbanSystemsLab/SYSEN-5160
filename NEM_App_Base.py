from collections import namedtuple
import altair as alt
#from tkinter import Image
import math
import streamlit as st
import numpy as np
import time 
import pandas as pd
from geopy.geocoders import Nominatim 
import requests 
import json
from pvlib import location as loc
from pvlib import irradiance
import pandas as pd
from matplotlib import pyplot as plt
from plot_ghi_transposition import get_irradiance
from timezonefinder import TimezoneFinder 


st.title("NEM Pricing Calculator")


#pv_size = st.text_input('Area of PV Array (ft^2)', '250')
#pv_area = float(pv_size) * 0.09290304
#st.write('The current array size is', pv_area, 'm^2') 

st.header('Location')
st.subheader('From your location information we will be able to calculate the average amount of sunlight you would receive as well as the residential electricity prices.')


state = st.text_input('State of Residency', 'NY')
city= st.text_input('City of Residency', 'Ithaca')

zipcode = st.text_input('Zipcode', '14850')

place = state + ' ' + city + ' ' + zipcode
st.write('The location being queried is', place) 

geolocator = Nominatim(user_agent="geoapiExercises")

location = geolocator.geocode(place) 
coords = [str(location.latitude), str(location.longitude)]
lat = float(coords[0])
lon = float(coords[1])
st.write('Your Latitude and Longitude is: (' + coords[0]+ ', ' +coords[1] + ')') 

st.header('Solar Array')
st.subheader('The specifications of your solar system will determine its performance and how much you may potentially save.')
sys_cap = float(st.text_input('Capacity of Solar Array (kW)', '10'))
c = np.array([206.14285714, 2426.14285714,  -38.32142857])

install_cost = c[2]*sys_cap**2 +  sys_cap* c[1] + c[0]

st.write('Estimated installation cost for Array Size %3.2f kW before tax credits is $ %5.2f' %tuple([sys_cap, install_cost]))

#Selecting Type of Module Used in Array
mod_options = ['Standard', 'Premium', 'Thin film'] 

module = st.selectbox('What type of modules are you using?', mod_options, index = 0)
st.write('You selected',module)
mod_df =pd.DataFrame({'Standard': [0], 'Premium': [1], 'Thin film': [2]})

module_type = mod_df[module][0]

#Tilt of the Soalr Cells relatie to horizontal
tilt = st.slider('Angle of Roof/Solar Array', min_value= 0, max_value = 45, value = 30 ,step = 1)

#Selecting The Proper Array Arrangement
arr_options = ['Fixed - Open Rack', 'Fixed - Roof Mounted', '1-Axis', '1-Axis Backtracking', '2-Axis']
arr_df = pd.DataFrame({'Fixed - Open Rack':[0], 'Fixed - Roof Mounted':[1], '1-Axis':[2] \
,'1-Axis Backtracking':[3], '2-Axis':[4]})

array = st.selectbox('What type of array are you using?', arr_options, index = 1)
st.write('You selected',array)
array_type = arr_df[array][0]


#Azimuth angle
azi_options = ['S','SSW', 'SW','WSW','W','WNW', 'NW','NNW', 'N' ,'NNE','NE', 'ENE', 'E', 'ESE', 'SE','SSE']
azi_df = pd.DataFrame({'S':[0], 'SSW':[22.5], 'SW':[45],'WSW':[67.5],'W':[90],'WNW':[112.5], 'NW':[135],'NNW':[157.5],\
     'N':[180],'NNE':[202.5],'NE':[225], 'ENE':[247.5], 'E':[270], 'ESE':[297.5], 'SE':[315],'SSE':[337.5]}) 
azi = st.selectbox('What direction is your house/array facing approximately?', azi_options, index = 0)

azimuth = azi_df[azi][0]

# Now Add the losses your system will experience 
losses = st.slider('What percent of power do you expect your system to lose?', min_value = -5, max_value= 99, value = 15)

# Now Use the Latitude and Longitude Given to doan API pull of the utility rates from NREL 
price_pull = 'https://developer.nrel.gov/api/utility_rates/v3.json?lat=' + coords[0]+ '&lon='+ coords[1] +'&api_key=90IdyNRwQOO0iv3PXV6wPAbfHl8dKrBFXWDWBadf'

response_API = requests.get(price_pull) 
# utility pricing data is in $/kWh 
Pdata =response_API.text
Pdict = json.loads(Pdata) 
Pd2 = Pdict['outputs'] 
price_df = pd.DataFrame.from_dict(Pd2) 
res_price = float(price_df.residential)

e_bill = float(st.text_input('What is your average electricity bill ($)?', '100'))
st.write('Price of electricity for a residential consumer in your area is $ %2.3f/kWh' %res_price)


e_load = e_bill/res_price


st.header('Results')

# Now Use the Latitude and Longitude Given to doan API pull of the solar data from NREL 
api_pull = 'https://developer.nrel.gov/api/pvwatts/v6.json?lat=' + coords[0]+ '&lon='+ coords[1]\
 + '&module_type=' + str(module_type) + '&system_capacity=' + str(sys_cap) + '&tilt=' + str(tilt) + '&array_type='\
    + str(array_type) + '&azimuth=' + str(azimuth) +'&losses=' + str(losses)\
         +'&api_key=90IdyNRwQOO0iv3PXV6wPAbfHl8dKrBFXWDWBadf'



response_API = requests.get(api_pull) 
# ghi data is in kWh/m2/day
data =response_API.text
dict = json.loads(data) 
d2 = dict['outputs'] 

## Need to figure out how to access ghi data specifically by month 
solar_df = pd.DataFrame.from_dict(d2)

#st.dataframe(solar_df)





NEM = 'NEM 2.0'

cost = np.zeros(13)
solar_prod = np.zeros(13) 
savings = np.zeros(13)
if NEM == 'NEM 2.0':
#NEM 2.0 
     
     solar_prod[:12] = solar_df.ac_monthly
     solar_prod[12] = np.sum(solar_prod[:12])
     demand = e_load
     for i in range(0,12): 
          
          if e_load >= solar_prod[i]:
               Ppi = res_price
               savings[i] = Ppi * solar_prod[i]
               cost[i] = Ppi * demand - savings[i]
               
          else: 
               Ppi = res_price -0.03
               savings[i] = Ppi * solar_prod[i]
               cost[i] = Ppi * demand - savings[i]
elif NEM == 'NEM 1.0':
     #NEM 1.0 
     for i in range(0,12): 
          
          if e_load >= solar_prod[i]:
               Ppi = res_price
               cost = Ppi * (demand[i] - solar_prod[i])
          else: 
               Ppi = res_price
               cost = Ppi * (demand[i] -solar_prod[i]) 

cost[12] = np.sum(cost[:12])
savings[12] = np.sum(savings)
Months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Tot']
fd = pd.DataFrame({'Month': Months, 'Solar Production (kWh)': solar_prod, 'Bill After Solar NEM ($)': cost, 'Savings ($)': savings})


st.dataframe(fd)


payback = install_cost/savings[12]

fig,axs = plt.subplots(1,1, figsize =(8,6))

axs.plot(Months[:12], cost[:12], '-')
axs.set_xlabel('Month')
axs.set_ylabel('Bill ($)')
axs.set_title('Bill vs. Month')
plt.rcParams['font.size'] = 13
st.pyplot(fig)

#If Smart Home we can caculate power over smaller timescales 

obj = TimezoneFinder()
tz = obj.timezone_at(lng = lon, lat = lat) 
site_location = loc.Location(lat, lon, tz=tz)

dates= ['01-01-2019', '01-01-2021']
days = [31, 28, 31, 30, 31, 30, 31,31, 30, 31, 30, 31] 

dy_irad = np.zeros([2,8760,2])
#for i in range(0,len(dates)):
#dy_irad[i,:,:] = get_irradiance(site_location, dates[i], tilt, azimuth)
     
   
#for h in range(0,len(days)): 
#avg_irad = (dy_irad[0,:,:] + dy_irad[1,:,:])/2 


#for j in range(0, len(days)):