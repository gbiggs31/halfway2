############################           PUBS AND TUBES          ############################


#this is version 1 of the pubs and tubes script


import pandas as pd
import numpy as np
import math
import pickle
from geopy.geocoders import Nominatim

#read in the pubs dataset already processed with distance to their nearest tube line attached
#easiest thing is probably to start adding total travel time to nearest node point of a different line
#again can cover that later, for now just take the closest one
#orrrr just treat them as independant pubs and double the length of your data, it wouldn't add much processing time


# get the user input
def get_coords_for_address(numentries):
    d= {}
    # z = 1
    # while z <= numentries:
    for z in range(numentries):
        result = None
        while result is None:
            d["user_input{0}".format(z)] = input("What's your address? ")
            #type(name)
            #d["user_input{0}".format(z)]= "London"
            d["user_input_geocode{0}".format(z)]  = geolocator.geocode(d["user_input{0}".format(z)])
            result = d["user_input_geocode{0}".format(z)]

            try:
                d["user_input_latitude{0}".format(z)] = d["user_input_geocode{0}".format(z)].latitude
                d["user_input_longitude{0}".format(z)] = d["user_input_geocode{0}".format(z)].longitude
            except:
                print("Google can't locate that address! Please try again.")
            z += 1
    return d
geolocator = Nominatim(user_agent= "GoogleV3")
numentries = int(input("How many addresses?"))
location_entry = get_coords_for_address(numentries)


# define and get all input data 
def get_pubs_data():
    pubswithdist = pd.read_csv('.\\pubswithdist.csv',index_col=0)
    #read in the already calculated tube network travel time data set
    return pubswithdist

def get_tube_travel():
    data_tubetravel = pd.read_csv('.\\data_tubetravel.csv',index_col=0)
    return data_tubetravel

def get_station_data():
    data_stations = pd.read_csv(".\\stations_csv.sv.csv")
    return data_stations

def get_travel_data():
    #now grab the all important travel times
    data_travel = pd.read_csv(".\\travel_times.csv")
    return data_travel

def get_tube_to_tube_data():
    # get simply the travel time all tubes to all tubes
    station_to_station_time = pd.read_csv(".\\station_to_station_time.csv")
    return station_to_station_time


def get_all_data():
    pubswithdist = get_pubs_data()
    data_tubetravel = get_tube_travel()
    data_sations = get_station_data()
    data_travel = get_travel_data()
    station_to_station_time = get_tube_to_tube_data()
    return pubswithdist, data_tubetravel, data_sations, data_travel, station_to_station_time 

#need to assign every pub a nearest tube
# this should be cached appropriately
#need to define a function for distance between coordinates
#use the haversine formula
#need the angle in radians

#potential cython candidate
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

# try and set it up to do the two matrix and a vector methodology

# matrix 1, tube to tube, precomputed, stored and in get data

# person to tube vector

# need matrix 2, should also precompute

# could optimise but time is so fast probably not worth it
# dont care about the explicit closest station if we're checking all of them!
def compute_station_distance_from_user(input_lat, input_long, data_stations):
    # min_distance = 1000
    person_tube = []
    # closest_tube = []
    for tube in data_stations.itertuples():
        #get distance between input coords and all tubes
        current_time = coords_to_distance(getattr(tube,'latitude'),input_lat,getattr(tube,'longitude'),input_long)
        current_time = current_time / 0.084
        # response is in km so convert to minutes

        person_tube.append(current_time)


        # if current_dist < min_distance:
        #     min_distance = current_dist
        #     closest_tube_id = getattr(tube,'id')
    return person_tube        






def nearest_station_to_rest(closest_tube_id):
    person_travel = []
    tube_id = []
    tube_results = []
    
    from ast import literal_eval
    test_dict = literal_eval(data_tubetravel[data_tubetravel['id'] == closest_tube_id]['travel_times'][closest_tube_id - 1])
    
    for destination in test_dict:
        person_travel.append(test_dict[destination]['time'])
        tube_id.append(destination)
    return person_travel, tube_id



# all code after this could be cleaned up and improved
# think we can remove the explicited second station and even nearest tube calculation

# def find_second_station(previous_station):
#     alreadycheckedlines= []
#     for line in data_travel[data_travel['station1'] == previous_station].iterrows():
#         #print(line)
#         alreadycheckedlines.append(line[1]['line'])
#         datatravel_temp = data_travel[~data_travel['line'].isin(alreadycheckedlines)]
#         data_filtered = data_stations[data_stations['id'].isin(datatravel_temp['station1'])]
#     return data_filtered


#need this to be self contained, and output an identifiable dataset ready for further processing
def distance_to_pubs(input_lat,input_long,user_num,data_stations):
    closest_tube_id = find_nearest_station(input_lat,input_long,user_num,data_stations)            
    #this loop returns the closest tube station to the input coords
    #then the below works out the travel time to all the things from that
    #data tubetravel contains travel time from each tube station to every other tube station
    #so just filter to the nearest tube station and check time to the rest of the network
    #need to check each line as well

    person_travel, tube_id = nearest_station_to_rest(closest_tube_id)

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