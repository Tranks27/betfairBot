#!/home/ubuntu/betfairBot/venv/bin/python3
# START
'''#!/usr/bin/env python3'''
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
import logging
import certs.passwords as secret
from logging.handlers import TimedRotatingFileHandler

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
        
    logging.debug("lay_options_ids = %s", lay_options_ids)
    
    lay_selection_id = lay_options_ids[lay_selection_index]
    logging.info("lay_selection_id = %d", lay_selection_id)
    chosen_row_df = runners_df.loc[runners_df['Selection ID'] == lay_selection_id]
    [fav_price] = chosen_row_df['Best Lay Price'].values
    logging.info("Chosen fav_price = %s", fav_price)

    return lay_selection_id, fav_price

def clearFileContents(fname):
    ## Clear the contents of the output file
    with open(fname, 'w') as f:
        #f.truncate()
        logging.info("Cleared contents from the output file -> %s", fname)
          
    return

def failGracefully(error='N/A'):
    logging.error("Error: {0}".format(error) )
    logging.info("Moving to next match")
    time.sleep(60)
    logging.info("********************************************************\n\n\n")


if __name__ == "__main__":
    ## Clear file contents #TODO: save the logs and keep a copy in a storage somewhere
    # clearFileContents(xxx) # cronlogs.log maybe?
    # clearFileContents(constants.OUT_FILE) # debug.log
    clearFileContents('debug.log') # debug.log
    clearFileContents(constants.PL_FILE) #Profit_loss.csv

    #######################################
    # Init logging
    #######################################
    logging.root.handlers = [] ## this makes sure it works logging system is already initialized somewhere else
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[
            TimedRotatingFileHandler("timedDebug.log", when='H', interval=12),
	    # logging.FileHandler("debug.log"), # log to file
            #logging.StreamHandler() # log to stdout
            ]
    )

    #######################################
    # Non-interactive login to betfair API
    #######################################
    # Change this certs path to wherever you're storing your certificates
    certs_path = str(os.getcwd()) + "/certs/"
    # Change these login details to your own
    my_username = secret.USERNAME
    my_password = secret.PASSWORD
    # my_app_key = secret.API_KEY_DEMO #demo
    my_app_key = secret.API_KEY_LIVE #live

    trading = betfairlightweight.APIClient(username=my_username,
                                        password=my_password,
                                        app_key=my_app_key,
                                        certs=certs_path)

    trading.login()
    logging.info("Successfully logged in")
    #######################################
    # Start the program
    #######################################
    ## TODO
    debug = False  # Print the data frames
    completion_cnt = 0
    success_flag = True
    liability_options = [2,50]
    end_of_day_cnt = 0
    lost_game_flag = False
    feeling_lucky = False
    lucky_cnt = 0

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
        if len(gb_gh_events) == 0:
            logging.error("No UK Greyhounds events found")
            end_of_day_cnt = end_of_day_cnt +1

            if end_of_day_cnt > 2: # after three tries, end the program
                logging.info("See you tomorrow. Have a good day")
                trading.logout()
                exit() #exit gracefully
            else:
                logging.info("Try again")
                continue
        else:
            end_of_day_cnt = 0
        
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
            logging.info("Sleeping for " + str(time_to_sleep) + " seconds")
            time.sleep(time_to_sleep) #TODO
            logging.info("Sleeping done")
        else:
            logging.info("Don't need to sleep")

        #######################################
        # Get odds from NEDS
        #######################################
        lay_selection_index = utils.choose_lay_option_neds(myRaceVenue)

        if(lay_selection_index < 0):
            failGracefully()
            continue
        else:
            logging.info("Lay option found successfully = %d" , lay_selection_index)

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
            logging.error("Error occurred in choose_lay_option_bf()")
            failGracefully(e)
            continue

        if fav_price > constants.MAX_FAV_PRICE:
            logging.error("Minimum Price too high. SKIP!!!")
            failGracefully()
            continue
        # %%
        #######################################
        # Choose the liability amount
        # random from a list of 10 options
        #######################################
        ## Include double luck runs
        if lucky_cnt == 0:
            feeling_lucky = np.random.choice([True,False], size=1, p=[0.10, 0.90]) # 10% lucky

            if feeling_lucky == True:
                lucky_cnt = 2 # to run 2 high stakes game in a row
                feeling_lucky = False

                logging.info("Feeling lucky run#%d", 2 - lucky_cnt)
                liability_amount = liability_options[1]
                lucky_cnt = lucky_cnt - 1

            else:
                ## if the last game was lost, bet 1500 else proceed normally
                if lost_game_flag == False:
                    [liability_amount] = np.random.choice(liability_options, size=1, p=[0.80, 0.20]) #80% and 20% probabilities
                    logging.info("Chosen Liability amount = $%d", liability_amount)

                else:
                    liability_amount = liability_options[1]
                    lost_game_flag = False
        else:
            logging.info("Feeling lucky run#%d", 2 - lucky_cnt)
            liability_amount = liability_options[1]
            lucky_cnt = lucky_cnt - 1

        logging.info("Final Chosen Liability amount = %d", liability_amount)
            
        
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
        logging.info("order_filter = %s", order_filter)

        #######################################
        # Create a place instruction filter
        #######################################
        instructions_filter = filters.place_instruction(
            selection_id = str(lay_selection_id),
            side="LAY",
            order_type = "LIMIT", # fixed price order
            limit_order=order_filter
        )
        logging.info("instructions_filter = %s", instructions_filter)


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
                logging.info("single_current_order = %s", single_current_order)

                unmatched_size = single_current_order['sizeRemaining']
                logging.info('unmatched size = %s', unmatched_size)

                ## if there's unmatched order, replace it with new price, else set the fullyMatched flag
                if float(unmatched_size) != 0:
                    logging.info("Order is not fully matched yet")

                    ## Get the new best Lay price
                    lay_selection_id, fav_price = choose_lay_option_bf(price_filter, lay_selection_index)

                    ## Replace the unmatched order with the new price
                    replace_instructions_filter = filters.replace_instruction(
                        bet_id= single_current_order['betId'],
                        new_price= fav_price
                    )
                    logging.info("replace intructions filter: %s", replace_instructions_filter)

                    newOrder = trading.betting.replace_orders(
                            market_id = myRaceID,
                            customer_ref='Naing_maker_Replaced',
                            instructions=[replace_instructions_filter]
                        )

                    logging.info("Replaced order report: %s", newOrder)
                    time.sleep(5)
                else:
                    logging.info("Full order matched")
                    fullyMatched_flag = True
                    success_flag = True
        except IndexError as e:
            logging.error("The current orders might have been cleared since the race started")
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
        check_cnt = 0
        try:
            while settled_flag == False:
                cleared_orders = trading.betting.list_cleared_orders(
                    bet_status="SETTLED",
                    market_ids=[myRaceID])

                if len(cleared_orders._data['clearedOrders']) != 0:
                    settled_flag = True

                    # Create a DataFrame from the orders
                    betResult = pd.DataFrame(cleared_orders._data['clearedOrders'])
                    logging.info("betResult = %s", betResult)

                    betOutcome = betResult['betOutcome'][0]
                    profit = 0
                    for i in betResult['profit']:
                        profit = profit + float(i)

                    ## if the game is lost, bet more in the next game
                    if profit < 0:
                        lost_game_flag = True

                    ## Record the results into a csv file
                    utils.write_to_file(constants.PL_FILE, myRaceID, betOutcome, profit, start_time)

                    completion_cnt = completion_cnt + 1
                    logging.info("Completion count = %d", completion_cnt)
                    

                else:
                    logging.info("Sleep 60 seconds before checking again if market is settled")
                    time.sleep(60) # TODO:Check again in 60 seconds
                    check_cnt = check_cnt + 1
                    if check_cnt > 10:
                        logging.info("Assuming market is settled. NEXT game!!!")
                        settled_flag = True

        except Exception as e:
            logging.info("Writing to file FAILED")
            failGracefully(e)
            continue


        randomSleep = np.random.randint(60,180)
        logging.info("Sleeping for some time before starting the next game = %d seconds", randomSleep)
        time.sleep(randomSleep)
    
    logging.info("%d games have been played. BYE BYE and Good luck", constants.NUM_GAMES)
        



