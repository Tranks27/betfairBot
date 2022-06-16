# # pick the random venue
# import random
# random_pick = random.randint(1,len(fc_venue_ids))
# # random_pick = 1
# venueOfTheDay_name = fc_venue_names[random_pick]
# venueOfTheDay_id = fc_venue_ids[random_pick]

# venueOfTheDay_name, venueOfTheDay_id


# market_types_filter = filters.market_filter(event_ids=[venueOfTheDay_id])

# market_types = trading.betting.list_market_types(
#     filter=market_types_filter
# )

# market_types_venueOfTheDay = pd.DataFrame({
#     'Market Type': [market_type_object.market_type for market_type_object in market_types],
# })
# market_types_venueOfTheDay


####################################################################################################################