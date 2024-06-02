TITLE = "Pokémon TCG API"

ERROR_200 = "Everything worked as expected."
ERROR_400 = "Bad Request. Your request is either malformed, or is missing one or more required fields."
ERROR_402 = "The parameters were valid but the request failed."
ERROR_403 = "The user doesn't have permissions to perform the request."
ERROR_404 = "The requested resource was not found."
ERROR_429 = "The rate limit has been exceeded."
ERROR_500 = "Something went wrong on our end."

ROUTE_CARD = "Fetch the details of a single card."
ROUTE_SEARCH_CARD = "Search for one or many cards given a search query."
ROUTE_SET = "Fetch the details of a single set."
ROUTE_SEARCH_SET = "Search for one or many sets given a search query."
ROUTE_TYPES = "Get all possible types"
ROUTE_SUBTYPES = "Get all possible subtypes"
ROUTE_SUPERTYPES = "Get all possible supertypes"
ROUTE_RARITIES = "Get all possible rarities"

PATH_CARD_ID = "The Id of the card"
PATH_SET_ID = "The Id of the set"

QUERY_SELECT = (
    "A comma delimited list of fields to return in the response (ex. ?select=id,name). "
    "By default, all fields are returned if this query parameter is not used."
)
QUERY_SEARCH_Q = "The search query."
QUERY_SEARCH_PAGE = "The page of data to access."
QUERY_SEARCH_PAGESIZE = "The maximum amount of cards to return."
QUERY_SEARCH_ORDERBY = "The field(s) to order the results by."
