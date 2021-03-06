############################           PUBS AND TUBES          ############################


#this is version 1 of the pubs and tubes script


import pandas as pd
import numpy as np
import math
# import missingno as mn
# import matplotlib.pyplot as plt
# import seaborn as sn
import pickle
from geopy.geocoders import Nominatim

#read in the pubs dataset already processed with distance to their nearest tube line attached
#easiest thing is probably to start adding total travel time to nearest node point of a different line
#again can cover that later, for now just take the closest one
#orrrr just treat them as independant pubs and double the length of your data, it wouldn't add much processing time


d= {}
geolocator = Nominatim(user_agent= "GoogleV3")
numentries = int(input("How many addresses?"))
z = 1
while z <= numentries:
    #user_input = input
    d["user_input{0}".format(z)] = input("What's your address? ")
    #type(name)
    #d["user_input{0}".format(z)]= "London"
    d["user_input_geocode{0}".format(z)]  = geolocator.geocode(d["user_input{0}".format(z)])
    try:
        d["user_input_latitude{0}".format(z)] = d["user_input_geocode{0}".format(z)].latitude
        d["user_input_longitude{0}".format(z)] = d["user_input_geocode{0}".format(z)].longitude
    except:
        print("This failed! Please try again.")
    z += 1


pubswithdist = pd.read_csv('.\\pubswithdist.csv',index_col=0)
#read in the already calculated tube network travel time data set

data_tubetravel = pd.read_csv('.\\data_tubetravel.csv',index_col=0)

# with open('.\\.pickle','rb') as f:
#     data_tubetravel = pickle.load(f,encoding="utf8")


data_stations = pd.read_csv(".\\stations_csv.sv.csv")
#now grab the all important travel times
data_travel = pd.read_csv(".\\travel_times.csv")


#need to assign every pub a nearest tube
#need to define a function for distance between coordinates
#use the haversine formula
#need the angle in radians

def coords_to_distance(x1,x2,y1,y2):
    x1 = x1 * math.pi / 180
    x2 = x2 * math.pi / 180
    y1 = y1 * math.pi / 180
    y2 = y2 * math.pi / 180
    dlat = x2 - x1
    dlon = y2 - y1
    a = (math.pow(math.sin(dlat/2),2)) + math.cos(x1) * math.cos(x2) * (math.pow(math.sin(dlon/2),2))
    c = 2 * math.atan2(math.sqrt(a),math.sqrt(1-a))
    d = c * 6373
    #this is in km
    return d

def find_second_station(previous_station):
    alreadycheckedlines= []
    for line in data_travel[data_travel['station1'] == previous_station].iterrows():
        #print(line)
        alreadycheckedlines.append(line[1]['line'])
        datatravel_temp = data_travel[~data_travel['line'].isin(alreadycheckedlines)]
        data_filtered = data_stations[data_stations['id'].isin(datatravel_temp['station1'])]
    return data_filtered


#need this to be self contained, and output an identifiable dataset ready for further processing
def distance_to_pubs(input_lat,input_long,user_num,data_stations):
    min_distance = 1000
    closest_tube_id = []
    closest_tube = []
    for tube in data_stations.itertuples():
        #get distance between input coords and all tubes
        current_dist = coords_to_distance(getattr(tube,'latitude'),input_lat,getattr(tube,'longitude'),input_long)
        if current_dist < min_distance:
            min_distance = current_dist
            closest_tube_id = getattr(tube,'id')
            #closest_line = getattr(line, '')
            #this will return the closest tube station id to the input coords
            #could potentially be optimised further but not worth it because of how quick it currently is
            
    #this loop returns the closest tube station to the input coords
    #then the below works out the travel time to all the things from that
    #data tubetravel contains travel time from each tube station to every other tube station
    #so just filter to the nearest tube station and check time to the rest of the network
    #need to check each line as well
    
    x= 1
    person_travel = []
    tube_id = []
    tube_results = []
    for line in data_tubetravel[data_tubetravel['id'] == closest_tube_id]['travel_times']:
        while x < len(data_stations):
            person_travel.append(line[x]['time']) 
            tube_id.append(x)
            x += 1

    #the above returns the travel time to all stations from the nearest station
    user_num = str(user_num)    
    person_travel = pd.DataFrame(person_travel)
    tube_id = pd.DataFrame(tube_id)
    individ_tube = pd.merge(tube_id,person_travel,left_index = True, right_index = True)
    individ_tube.columns = ['tube_id','travel_time_to_tube'+user_num]
    
    
    full_travel = pd.merge(pubs_with_dist_filt,individ_tube, how = 'left',left_on = '0_y',right_on = 'tube_id')
    min_distance_time = min_distance / 0.084
    full_travel['total time' + user_num] = full_travel['traveltime_totube_pub'] + full_travel['travel_time_to_tube'+str(user_num)] + min_distance_time
    return full_travel,closest_tube_id




#could be worth filtering pubs with dist to only a couple of columns so that it's neater?
#could be worth filtering pubs with dist to only a couple of columns so that it's neater?
pubs_with_dist_filt = pubswithdist[['0_y','index','traveltime_totube_pub']]
numpeeps = 2
i = 1
while i <= numpeeps:
    full_travel_i_1, i_closest_tube_id = distance_to_pubs(d["user_input_latitude{0}".format(i)],d["user_input_longitude{0}".format(i)],i,data_stations)
    full_travel_i_2, i_second_closest_tube = distance_to_pubs(d["user_input_latitude{0}".format(i)],d["user_input_longitude{0}".format(i)],i,find_second_station(i_closest_tube_id))
    full_travel_i = pd.merge(full_travel_i_1,full_travel_i_2, left_index=True,right_index=True)
    #full_travel_i['True_shortest' + str(i)] = min(full_travel_i['total time' + str(i) + '_x'], full_travel_i['total time' + str(i) + '_y'])
    full_travel_i['true_shortest' + str(i)] = full_travel_i[['total time' + str(i) + '_x', 'total time' + str(i) + '_y']].min(axis=1)
    full_travel_i_final = full_travel_i[['true_shortest' + str(i)]]
    if i > 1:
        full_current = pd.merge(full_travel_i_final,full_current,left_index=True,right_index=True)
    else:
        full_current = full_travel_i_final
    i += 1
#test_fulltravel,test_closest_tube_id = distance_to_pubs(51.5020275,-0.0267862,2,data_stations)
#this works fine, worth in your loop goingn twice for each person and checking the other nearest tube
#then combine those datasets, take only the shortest travel time to each pub and move on
#ok so once that works what needs to happen?

cols_to_use = ['true_shortest' + str(p+1) for p in range(numpeeps)]
#full_current['Total'] = full_current.loc[:, cols_to_use].sum(axis=1)
full_current['Total'] = full_current[cols_to_use].sum(axis =1 )
full_current = pd.merge(full_current,pubswithdist,left_index= True,right_index=True)
full_current = full_current[full_current['Total'] != 0]


finalfinal = full_current.sort_values('Total')
finalfinal_top = finalfinal.head(10)
finalfinal_top = finalfinal_top[['Total','2','8']]
print(finalfinal_top)