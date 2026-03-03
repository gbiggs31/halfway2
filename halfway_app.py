############################           PUBS AND TUBES          ############################


#this is version 3 of the pubs and tubes script


import pandas as pd
import numpy as np
import math
import pickle
from geopy.geocoders import Nominatim
import streamlit as st
import pydeck as pdk

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
    @st.cache_data
    def get_pubs_data():
        url = 'https://raw.githubusercontent.com/gbiggs31/halfway2/master/pubswithdist.csv'
        # pubswithdist = pd.read_csv('.\\pubswithdist.csv',index_col=0)
        pubswithdist = pd.read_csv(url)
        pubswithdist['filter'] = pubswithdist['1'] + ', ' + pubswithdist['8']
        #read in the already calculated tube network travel time data set
        return pubswithdist

    @st.cache_data
    def get_tube_travel():
        # data_tubetravel = pd.read_csv('.\\data_tubetravel.csv',index_col=0)
        url = 'https://raw.githubusercontent.com/gbiggs31/halfway2/master/data_tubetravel.csv'
        data_tubetravel = pd.read_csv(url)
        return data_tubetravel

    @st.cache_data
    def get_station_data():
        # data_stations = pd.read_csv('.\\stations.csv')
        url = 'https://raw.githubusercontent.com/gbiggs31/halfway2/master/stations.csv'
        data_stations = pd.read_csv(url)
        return data_stations

    @st.cache_data
    def get_travel_data():
        #now grab the all important travel times
        # data_travel = pd.read_csv('.\\travel_times.csv')
        url = 'https://raw.githubusercontent.com/gbiggs31/halfway2/master/travel_times.csv'
        data_travel = pd.read_csv(url)
        return data_travel

    @st.cache_data
    def get_tube_to_tube_data():
        # get simply the travel time all tubes to all tubes
        # station_to_station_time = pd.read_csv('.\\station_to_station_time.csv')
        url = 'https://raw.githubusercontent.com/gbiggs31/halfway2/master/station_to_station_time.csv'
        station_to_station_time = pd.read_csv(url)

        return station_to_station_time

    @st.cache_data
    def get_pub_to_station_data():
        # get the precomputed walking time from each pub to each station
        # pub_to_station_data = pd.read_csv(r'./pub_time_to_stations.csv')
        url = 'https://raw.githubusercontent.com/gbiggs31/halfway2/master/pub_time_to_stations.csv'
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
        total_travel = np.round(combine_person_and_pub_travel(user_and_tube, pub_to_station),2)
        return total_travel


    def compute_best_pubs(combined_user_times):
        combined_user_times['all_combined_time'] = combined_user_times.sum(axis=1)
        combined_user_times.sort_values(by = 'all_combined_time', inplace = True)
        return combined_user_times


    def plot_best_pubs(orig_pubs, pubs_in_order, user_locations):
        import folium
        from streamlit_folium import st_folium

        top10_indices = pubs_in_order.head(10).index
        top10_pubs = orig_pubs[orig_pubs['filter'].isin(top10_indices)].copy()
        top10_pubs = top10_pubs.dropna(subset=['latitude', 'longitude'])

        top10_pubs['rank'] = top10_pubs['filter'].map(
            {idx: rank + 1 for rank, idx in enumerate(top10_indices)}
        )
        top10_pubs['avg_travel_time'] = top10_pubs['filter'].map(
            lambda idx: round(pubs_in_order.loc[idx, 'all_combined_time'] / len(user_locations), 1)
            if idx in pubs_in_order.index else None
        )
        top10_pubs['pub_name'] = top10_pubs['1']

        all_lats = list(top10_pubs['latitude']) + [u[0] for u in user_locations]
        all_lons = list(top10_pubs['longitude']) + [u[1] for u in user_locations]
        centre_lat = sum(all_lats) / len(all_lats)
        centre_lon = sum(all_lons) / len(all_lons)

        m = folium.Map(location=[centre_lat, centre_lon], zoom_start=12, tiles='CartoDB dark_matter')

        # pub pins
        for _, row in top10_pubs.iterrows():
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                tooltip=folium.Tooltip(
                    f"<b>{row['pub_name']}</b><br/>Rank #{int(row['rank'])} · ~{row['avg_travel_time']} min avg",
                    sticky=True
                ),
                icon=folium.DivIcon(html=f"""
                    <div style="
                        font-size: 24px;
                        text-align: center;
                        line-height: 1;
                        filter: drop-shadow(1px 1px 2px rgba(0,0,0,0.8));
                    ">🍺</div>
                """)
            ).add_to(m)

        # user pins
        for i, (lat, lon) in enumerate(user_locations):
            folium.Marker(
                location=[lat, lon],
                tooltip=f'Person {i + 1}',
                icon=folium.Icon(color='blue', icon='home', prefix='fa'),
            ).add_to(m)

        st.subheader("Top 10 Pubs Map")
        st_folium(m, width=700, height=500)

    def run_script():    
        # specify the streamlit scaffolding
        st.title('Halfway')
        st.title('Because friendship is about compromise \n')


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
        answer_for_map = sorted_user_times.copy()
        orig_columns = sorted_user_times.columns
        
        col_list = []
        for column in orig_columns:
            # new_column = 'User ' + str(column) + ' Travel Time (Mins)'
            if column == 'all_combined_time':
                new_column = 'Total Travel Time (Mins)'
            else:
                new_column = 'User ' + str(column) + ' Travel Time (Mins)'
            col_list.append(new_column)

        sorted_user_times.columns = col_list
        # sorted_user_times = np.round(sorted_user_times,2)

        user_locations = [
            (location_entry['user_input_latitude' + str(i)], location_entry['user_input_longitude' + str(i)])
            for i in range(numentries)
            ]

        return sorted_user_times, user_locations, answer_for_map



    answer, user_locations, answer_for_map = run_script()
    st.write('Click any column to sort')
    st.write(answer)
    # st.write(len(answer))
    # print(answer)
    orig_pubs = get_pubs_data()
    plot_best_pubs(orig_pubs, answer_for_map, user_locations)


if __name__ == "__main__":
    main()







