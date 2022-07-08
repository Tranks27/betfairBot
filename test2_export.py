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

# %%
def filter_gh_races(gh_racing_id):
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

    return gb_gh_events

def get_upcoming_games(num_games, market_catalogue_filter):
    market_catalogues = trading.betting.list_market_catalogue(
        filter=market_catalogue_filter,
        market_projection= ['MARKET_START_TIME', 'EVENT'],
        max_results=str(num_games),
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

    return market_catalogues

def choose_lay_option_bf(price_filter, lay_selection_index):
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

    # Extract a list of IDs for the lay options
    lay_options_ids = []
    for obj in market_book.runners:
        lay_options_ids.append(obj.selection_id)
        
    if debug:
        print(lay_options_ids)
    
    lay_selection_id = lay_options_ids[lay_selection_index]
    print("lay_selection_id = " + str(lay_selection_id))
    picked_row_df = runners_df.loc[runners_df['Selection ID'] == lay_selection_id]
    [fav_price] = picked_row_df['Best Lay Price'].values
    print("Chosen fav_price = ", fav_price)

    return lay_selection_id, fav_price

def clearOutputFile(fname):
    ## Clear the contents of the output file
    with open(fname, 'r+') as f:
        f.truncate()
        print("Cleared contents from the output file -> ", fname)
          
    return

def failGracefully(error='N/A'):
    print("Error: ", error)
    print("Moving to next match")
    print("********************************************************", end='\n\n\n')


if __name__ == "__main__":
    # Change this certs path to wherever you're storing your certificates
    certs_path = str(os.getcwd()) + "/certs/"
    # Change these login details to your own
    my_username = constants.USERNAME
    my_password = constants.PASSWORD
    # my_app_key = constants.API_KEY_DEMO #demo
    my_app_key = constants.API_KEY_LIVE #live

    trading = betfairlightweight.APIClient(username=my_username,
                                        password=my_password,
                                        app_key=my_app_key,
                                        certs=certs_path)

    trading.login()

    ## TODO
    debug = True # Print the data frames
    completion_cnt = 0
    success_flag = True
    liability_options = []
    clearOutputFile(constants.F_NAME)

    while(completion_cnt < constants.NUM_GAMES):
        ## if some error occured, sleep for a while not to repeat the same game
        if success_flag != True:
            time.sleep(30)
            success_flag = True
        # %%
        #######################################
        # Filter out only greyhoud races
        #######################################
        gb_gh_events = filter_gh_races(constants.GH_RACING_ID)#Greyhound racing ID

        # %%
        #######################################
        # Extract a list of IDs for the forecast markets
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

        market_catalogues = get_upcoming_games(5, market_catalogue_filter) 

        # %%
        #######################################
        ## Check the start time of the next game
        ## and sleep until 15 seconds before the game
        #######################################
        start_time, time_gap, myRaceID, myRaceVenue = utils.get_next_market(market_catalogues)
        # assert myRaceID == 0, "ERROR: myRaceID = 0" #TODO: remove in production

        if(time_gap > datetime.timedelta(seconds=constants.PREBET_DELAY)):
            time_to_sleep = (time_gap - datetime.timedelta(seconds=constants.PREBET_DELAY)).seconds
            print("Sleeping for " + str(time_to_sleep) + " seconds")
            time.sleep(time_to_sleep) #TODO
            print("Sleeping done")
        else:
            print("Don't need to sleep")

        #######################################
        # Get odds from NEDS
        #######################################
        lay_selection_index = utils.choose_lay_option_neds(myRaceVenue)

        if(lay_selection_index == -1):
            print("ERROR!!! 2 same odds found")
            failGracefully()
            continue
            
        elif(lay_selection_index == -2):
            print("ERROR!!! less than 6 runners")
            failGracefully()
            continue

        elif(lay_selection_index == -3):
            print("ERROR!!! NEDS API failed")
            failGracefully()
            continue
        else:
            print("Lay option found successfully = ", lay_selection_index)

        # %%
        #######################################
        # Get a list of lay options from betfair
        #######################################
        # Create a price filter. Get all traded and offer data
        price_filter = filters.price_projection(
            price_data=['EX_BEST_OFFERS']
        )
        try:
            lay_selection_id, fav_price = choose_lay_option_bf(price_filter, lay_selection_index)
        except Exception as e:
            print("Error occurred in choose_lay_option_bf()")
            failGracefully(e)
            continue

        # %%
        #######################################
        # Choose the liability amount
        # random from a list of 10 options
        #######################################
        if(len(liability_options) == 0):
            # liability_options = [5, 5, 5, 5, 5, 5, 5, 5, 100, 100] #not sure why this can't be moved into constants.py
            liability_options = [50, 50, 50, 50, 50, 50, 50, 50, 50, 1000] #not sure why this can't be moved into constants.py
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
            price=str(fav_price),
            persistence_type='LAPSE',
            bet_target_type='PAYOUT',
            bet_target_size=str(liability_amount) 
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
        # Make sure the order is matched fully
        #######################################
        # utils.ensure_order_matched(myRaceID, lay_selection_index, price_filter)
        fullyMatched_flag = False
        try:
            while fullyMatched_flag == False:
                ## get the current order
                current_orders = trading.betting.list_current_orders(
                    market_ids=[myRaceID])
                single_current_order = current_orders._data['currentOrders'][0]
                print(single_current_order)

                unmatched_size = single_current_order['sizeRemaining']
                print('unmatched size = ', unmatched_size)

                ## if there's unmatched order, replace it with new price, else set the fullyMatched flag
                if float(unmatched_size) != 0:
                    print("Order is not fully matched yet")

                    ## Get the new best Lay price
                    lay_selection_id, fav_price = choose_lay_option_bf(price_filter, lay_selection_index)

                    ## Replace the unmatched order with the new price
                    replace_instructions_filter = filters.replace_instruction(
                        bet_id= single_current_order['betId'],
                        new_price= fav_price
                    )
                    print("replace intructions filter: ", replace_instructions_filter)

                    newOrder = trading.betting.replace_orders(
                            market_id = myRaceID,
                            customer_ref='Naing_maker_Replaced',
                            instructions=[replace_instructions_filter]
                        )

                    print("Replaced order report: ", newOrder)
                    time.sleep(5)
                else:
                    print("Full order matched")
                    fullyMatched_flag = True
                    success_flag = True
        except IndexError as e:
            print("The current orders might have been cleared since the race started")
            failGracefully(e)
            continue
        except Exception as e:
            failGracefully(e)
            continue
        #######################################
        # Check if the last bet has settled and note the result
        # Only if the previous race is settled, start next game 
        #######################################
        settled_flag = False    
        try:
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
                    utils.write_to_file(constants.F_NAME, myRaceID, betOutcome, profit, start_time)

                    completion_cnt = completion_cnt + 1
                    

                else:
                    print("Sleep 60 seconds before checking again if market is settled")
                    time.sleep(60) # TODO:Check again in 60 seconds
        except Exception as e:
            print("Writing to file FAILED")
            failGracefully(e)
            continue


        randomSleep = np.random.randint(60,180)
        print("Sleeping for some time before starting the next game = ", randomSleep, " seconds")
        time.sleep(randomSleep)
        


