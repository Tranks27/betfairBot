# %%
# Import libraries
import betfairlightweight
from betfairlightweight import filters
import pandas as pd
import numpy as np
import os
import datetime
import json
import pytz
import time
from IPython.display import display

# Project libraries
import utils
import constants

# Change this certs path to wherever you're storing your certificates
certs_path = "/home/naing/certs/"
# Change these login details to your own
my_username = constants.USERNAME
my_password = constants.PASSWORD
my_app_key = constants.API_KEY_DEMO #demo
# my_app_key = constants.API_KEY_LIVE #live

trading = betfairlightweight.APIClient(username=my_username,
                                       password=my_password,
                                       app_key=my_app_key,
                                       certs=certs_path)

trading.login()

## TODO
debug = True # Print the data frames
completion_flag = False # completion flag
completion_cnt = 0
while(completion_cnt < 10):
    # %%
    #######################################
    # Filter out only greyhoud races
    #######################################
    gh_racing_id = constants.GH_RACING_ID #Greyhound racing ID
    greyhound_racing_filter = filters.market_filter(
        event_type_ids=[gh_racing_id],
        market_countries=['GB'],
        market_type_codes=['FORECAST'],
        market_start_time={
            'to': (datetime.datetime.utcnow() + datetime.timedelta(hours=6)).strftime("%Y-%m-%dT%TZ") #sydtime 5pm to 7am next day for GB gh races
        }
    )
    #  This returns a list
    gb_gh_events = trading.betting.list_events(
        filter=greyhound_racing_filter)

    if debug:
        # Create a DataFrame with all the events by iterating over each event object
        gb_gh_events_df = pd.DataFrame({
            'Event Name': [event_object.event.name for event_object in gb_gh_events],
            'Event ID': [event_object.event.id for event_object in gb_gh_events],
            'Event Venue': [event_object.event.venue for event_object in gb_gh_events],
            'Country Code': [event_object.event.country_code for event_object in gb_gh_events],
            'Time Zone': [event_object.event.time_zone for event_object in gb_gh_events],
            'Open Date': [event_object.event.open_date for event_object in gb_gh_events],
            'Market Count': [event_object.market_count for event_object in gb_gh_events]
        })

        display(gb_gh_events_df)

    # %%
    #######################################
    #TODO: extract a list of IDs for the forecast markets
    #######################################
    fc_venue_ids = []
    fc_venue_names = []
    for eventObj in gb_gh_events:
        fc_venue_ids.append(eventObj.event.id)
        fc_venue_names.append(eventObj.event.name)

    fc_venue_ids, fc_venue_names


    # %%
    #######################################
    ## Filter out the next 5 upcoming games
    #######################################
    market_catalogue_filter = filters.market_filter(
        event_ids=fc_venue_ids)

    market_catalogues = trading.betting.list_market_catalogue(
        filter=market_catalogue_filter,
        market_projection= ['MARKET_START_TIME', 'EVENT'],
        max_results='5',
        sort='FIRST_TO_START'
    )

    ## show the dataframes if set
    if debug:
        market_types_venueOfTheDay_df = pd.DataFrame({
            'Market Name': [market_cat_object.market_name for market_cat_object in market_catalogues],
            'Market ID': [market_cat_object.market_id for market_cat_object in market_catalogues],
            'Market Start Time': [market_cat_object.market_start_time for market_cat_object in market_catalogues],
            'Total Matched': [market_cat_object.total_matched for market_cat_object in market_catalogues],
            'Venue': [market_cat_object.event.venue for market_cat_object in market_catalogues]
            
        })

        display(market_types_venueOfTheDay_df)

    # %%
    #######################################
    ## Check the start time of the next game
    ## and sleep until 15 seconds before the game
    #######################################
    time_gap, myRaceID, myRaceVenue = utils.get_next_market(market_catalogues)
    # assert myRaceID == 0, "ERROR: myRaceID = 0" #TODO: remove in production

    if(time_gap > datetime.timedelta(seconds=constants.PREBET_DELAY)):
        time_to_sleep = (time_gap - datetime.timedelta(seconds=constants.PREBET_DELAY)).seconds
        print("Sleeping for " + str(time_to_sleep) + " seconds")
        # time.sleep(time_to_sleep)
        print("Sleeping done")
    else:
        print("Don't need to sleep")

    # %%
    #######################################
    # Get a list of lay options
    #######################################
    # Create a price filter. Get all traded and offer data
    price_filter = filters.price_projection(
        price_data=['EX_BEST_OFFERS']
    )

    # Request market books
    market_books = trading.betting.list_market_book(
        market_ids=[myRaceID],
        price_projection=price_filter
    )

    # Grab the first market book from the returned list as we only requested one market 
    market_book = market_books[0]
    runners_df = utils.process_runner_books(market_book.runners)
    if debug:
        display(runners_df)

    #TODO: extract a list of IDs for the lay options
    lay_options_ids = []
    for obj in market_book.runners:
        lay_options_ids.append(obj.selection_id)
        
    # if debug:
    #     print(lay_options_ids)

    #######################################
    # Get odds from NEDS
    #######################################
    lay_selection_index = utils.choose_lay_option(myRaceVenue)

    if(lay_selection_index == -1):
        print("ERROR!!! 2 same odds found")
        assert()
        
    elif(lay_selection_index == -2):
        print("ERROR!!! less than 6 runners")
        # assert()

    elif(lay_selection_index == -3):
        print("ERROR!!! NEDS API failed")
        assert()
    else:
        print("Lay option found successfully")
        print(lay_selection_index)

    lay_selection_id = lay_options_ids[lay_selection_index]
    print("lay_selection_id = " + str(lay_selection_id))
    fav_price = runners_df.loc[runners_df['Best Lay Price'].idxmin(), 'Best Lay Price']



    # %%
    #######################################
    # Choose the liability amount
    # random from a list of 10 options
    #######################################
    liability_options = []

    if(len(liability_options) == 0):
        liability_options = [20, 20, 20, 20, 20, 20, 20, 20, 100, 100] #not sure why this can't be moved into constants.py
    print("liability_options [BEFORE] = ", liability_options, ", LENGTH =", len(liability_options))

    [liability_amount] = np.random.choice(liability_options, size=1)
    print("Chosen Liability amount = $", liability_amount)

    liability_options.remove(liability_amount)
    print("liability_options [AFTER] = ", liability_options, ", LENGTH =", len(liability_options))

    # %%
    #######################################
    # Choose order type (limit order or market_on_close order - choose the latter)
    #######################################
    order_filter = filters.limit_order(
        price=fav_price,
        persistence_type='LAPSE',
        bet_target_type='PAYOUT',
        bet_target_size=liability_amount 
    )
    print(order_filter)

    #######################################
    # Create a place instruction filter
    #######################################
    instructions_filter = filters.place_instruction(
        selection_id = str(lay_selection_id),
        side="LAY",
        order_type = "LIMIT", # fixed price order
        limit_order=order_filter
    )
    print(instructions_filter)


    # %%
    #######################################
    # Place the order
    #######################################
    order = trading.betting.place_orders(
        market_id = myRaceID,
        customer_strategy_ref='Naing_maker',
        instructions=[instructions_filter]
    )

    # %%
    #######################################
    # List the cleared orders
    #######################################
    myRaceID = 1.200450524 # lost raceID

    # time.sleep(5)
    # current_orders = trading.betting.list_current_orders(
    #     customer_strategy_refs=['Naing_maker']).__dict__
    # data = pd.DataFrame(current_orders['currentOrders']).head()
    # print(current_orders)

    #######################################
    # Check if the last bet has settled and note the result
    #######################################
    settled_flag = False
    while settled_flag == False:
        cleared_orders = trading.betting.list_cleared_orders(
            bet_status="SETTLED",
            market_ids=[myRaceID])

        if len(cleared_orders._data['clearedOrders']) != 0:
            settled_flag = True

            # Create a DataFrame from the orders
            betResult = pd.DataFrame(cleared_orders._data['clearedOrders'])
            print(betResult)

            betOutcome = betResult['betOutcome'][0]
            profit = 0
            for i in betResult['profit']:
                profit = profit + float(i)

            ## Record the results into a csv file
            utils.write_to_file(constants.F_NAME, myRaceID, betOutcome, profit)

            completion_flag = True # we are ready for next game

        else:
            print("Sleep 60 seconds before checking again if market is settled")
            time.sleep(5) # TODO:Check again in 60 seconds
        


