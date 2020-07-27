############################           PUBS AND TUBES          ############################


#this is version 3 of the pubs and tubes script


import pandas as pd
import numpy as np
import math
import pickle
from geopy.geocoders import Nominatim
import streamlit as st

#read in the pubs dataset already processed with distance to their nearest tube line attached
#easiest thing is probably to start adding total travel time to nearest node point of a different line
#again can cover that later, for now just take the closest one
#orrrr just treat them as independant pubs and double the length of your data, it wouldn't add much processing time

def main():


    # get the user input
    def get_coords_for_address(numentries):
        geolocator = Nominatim(user_agent= "GoogleV3")
        d= {}
        # z = 1
        # while z <= numentries:
        for z in range(numentries):
            result = None
            while result is None:
                # convert to streamlit
                unique_key = 'address_input' + str(z)
                user_input = st.text_input("What's your address? ", "Charing Cross, London", key = unique_key)
                d["user_input{0}".format(z)] = user_input #input("What's your address? ")
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


    # define and get all input data 
    @st.cache(suppress_st_warning=True)
    def get_pubs_data():
        url = 'https://github.com/gbiggs31/halfway2/blob/master/pubswithdist.csv'
        # pubswithdist = pd.read_csv('.\\pubswithdist.csv',index_col=0)
        pubswithdist = pd.read_csv(url)
        #read in the already calculated tube network travel time data set
        return pubswithdist

    @st.cache(suppress_st_warning=True)
    def get_tube_travel():
        # data_tubetravel = pd.read_csv('.\\data_tubetravel.csv',index_col=0)
        url = 'https://github.com/gbiggs31/halfway2/data_tubetravel.csv'
        # pubswithdist = pd.read_csv('.\\pubswithdist.csv',index_col=0)
        data_tubetravel = pd.read_csv(url)
        return data_tubetravel

    @st.cache(suppress_st_warning=True)
    def get_station_data():
        # data_stations = pd.read_csv('.\\stations.csv')
        url = 'https://github.com/gbiggs31/halfway2/stations.csv'
        data_stations = pd.read_csv(url)
        return data_stations

    @st.cache(suppress_st_warning=True)
    def get_travel_data():
        #now grab the all important travel times
        # data_travel = pd.read_csv('.\\travel_times.csv')
        url = 'https://github.com/gbiggs31/halfway2/data_travel.csv'
        data_travel = pd.read_csv(url)
        return data_travel

    @st.cache(suppress_st_warning=True)
    def get_tube_to_tube_data():
        # get simply the travel time all tubes to all tubes
        # station_to_station_time = pd.read_csv('.\\station_to_station_time.csv')
        url = 'https://github.com/gbiggs31/halfway2/station_to_station_time.csv'
        station_to_station_time = pd.read_csv(url)

        return station_to_station_time

    @st.cache(suppress_st_warning=True)
    def get_pub_to_station_data():
        # get the precomputed walking time from each pub to each station
        # pub_to_station_data = pd.read_csv(r'./pub_time_to_stations.csv')
        url = 'https://github.com/gbiggs31/halfway2/pub_to_station_data.csv'
        pub_to_station_data = pd.read_csv(url)
        return pub_to_station_data


    # def get_all_data():
    #     pubswithdist = get_pubs_data()
    #     data_tubetravel = get_tube_travel()
    #     data_sations = get_station_data()
    #     data_travel = get_travel_data()
    #     station_to_station_time = get_tube_to_tube_data()
    #     pub_to_station_data = get_pub_to_station_data()
    #     return pubswithdist, data_tubetravel, data_sations, data_travel, station_to_station_time, pub_to_station_data 

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

    # could optimise but time is so fast probably not worth it
    # dont care about the explicit closest station if we're checking all of them!
    def compute_station_distance_from_user(input_lat, input_long, data_stations):
        person_tube = []

        for tube in data_stations.itertuples():

            #get distance between input coords and all tubes
            current_time = coords_to_distance(getattr(tube,'latitude'),input_lat,getattr(tube,'longitude'),input_long)
            current_time = current_time / 0.084
            # response is in km so convert to minutes

            person_tube.append(current_time)
        person_tube = pd.DataFrame(person_tube)
        return person_tube        



    # so at this point should have both matrices and a person vector, just put them together

    def combine_person_and_station_travel(person_tube, tube_to_tube_data):
        # if we treat this as the columns are the FROM stations and the rows are the TO stations then it works!
        user_and_tube = tube_to_tube_data + person_tube.values
        user_and_tube = pd.DataFrame(user_and_tube.min(axis=1))
        #this produces a dataframe with the combined travel time to have the user walk to the tube, then take it to every other station
        # currently the columns are the FROM stations and the rows are the TO stations
        return user_and_tube


    def combine_person_and_pub_travel(user_and_tube, pub_to_station):
        total_travel = user_and_tube.values + pub_to_station
        total_travel = pd.DataFrame(total_travel.min())

        # this should return the total time it take a person to get to each pub in question
        # just need to compute walking time and check it isn't faster
        return total_travel

    def compute_all_pubs(latitude, longitude):
        data_stations = get_station_data()
        
        person_tube = compute_station_distance_from_user(latitude, longitude, data_stations)
        
        tube_to_tube_data = get_tube_to_tube_data()
        user_and_tube = combine_person_and_station_travel(person_tube, tube_to_tube_data)
        
        pub_to_station = get_pub_to_station_data()
        total_travel = combine_person_and_pub_travel(user_and_tube, pub_to_station)
        return total_travel


    def compute_best_pubs(combined_user_times):
        combined_user_times['all_combined_time'] = combined_user_times.sum(axis=1)
        combined_user_times.sort_values(by = 'all_combined_time', inplace = True)
        return combined_user_times

    def run_script():    
        # specify the streamlit scaffolding
        st.title('Halfway')
        st.title('Because beer is about compromise \n')


        # numentries = int(input("How many addresses?"))

        # Add a slider to the sidebar:
        numentries = st.sidebar.slider(
            'Select a number of addresses to minimise',
            1, 15, (1),  key="address_number"
        )

        location_entry = get_coords_for_address(numentries)
        
        combined_user_times = []
        for user in range(numentries):
            latitude = location_entry['user_input_latitude' + str(user)]
            longitude = location_entry['user_input_longitude' + str(user)]
            total_user_times = compute_all_pubs(latitude, longitude)
            if user == 0:
                combined_user_times = pd.DataFrame(total_user_times)
            else:
                combined_user_times[user] = total_user_times[0]

        sorted_user_times = compute_best_pubs(combined_user_times)   

        #ditch any nans
        sorted_user_times = sorted_user_times.dropna()
        orig_columns = sorted_user_times.columns
        
        col_list = []
        for column in orig_columns:
            new_column = 'User ' + str(column) + ' Travel Time'
            col_list.append(new_column)

        sorted_user_times.columns = col_list
        # sorted_user_times = np.round(sorted_user_times,2)
        return sorted_user_times

    answer = run_script()
    st.write(answer)
    # print(answer)

    # pubswithdist = get_pubs_data()
    # st.write(pubswithdist[['1','2','3','8']])




if __name__ == "__main__":
    main()







