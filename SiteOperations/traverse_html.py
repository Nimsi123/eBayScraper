import bs4
import pandas as pd

from eBayScraper.SiteOperations.clean_entries import clean_title, clean_price, clean_shipping, clean_date
from eBayScraper.SiteOperations import printer
from eBayScraper.ItemOrganization.timer import timer
from eBayScraper.data_files.directories import BAD_LISTING_DIR

def find_element(html, element_type, attr_key, attr_value):
    """Returns the FIRST element found in the html code block for which the element's value at attr_key matches the attr_value.

    :param html: The HTML block to search.
    :type html: 
    :param element_type: The HTML tag to search for.
    :type element_type: str
    :param attr_key: The key of an element's attribute.
    :type attr_key: str
    :param attr_val: If the element's value at key equals attr_value, we have our match.
    :type attr_val: str
    :returns: An HTML element within `html` that satisfies the condition. Returns None if an element is not found.
    :rtype: bs4.element.Tag or None
    """

    for element in html.find_all(element_type):
        if element.get(attr_key) == None:
            continue
        else:
            class_name = (element.get(attr_key))[0]

        if class_name.find(attr_value) != -1 and element.contents != None:
            return element

    return None

def get_listings_iteration(html):
    """Returns the total number of listings for the query and the number of page iterations.

    :param html: the webpage's entire html
    :type html: 
    :returns: Returns the total number of listings for the query and the number of page iterations.
    :rtype: tuple
    """
    strip_comma = lambda entry: entry.replace(',', '')
    temp_num = extract(html, "h1", "srp-controls__count-heading", strip_comma)
    
    try:
        total_listings = int(temp_num)
    except Exception as e:
        print(f"Cannot find total listings")
        print("{0:30}: {1}\n".format("extract", temp_num))
        raise e
        #return None, None
    
    total_listings = int(temp_num)

    if total_listings == 0:
        return None, None

    #ebay won't show us more that 10,000 items from their page even though there might be more to look at
    max_iteration = min(50, int(total_listings/200 +1))

    return total_listings, max_iteration

def next_link(old_link):
    """Given an old link to an eBay page, returns a link to the next page.

    :param old_link: The previous link
    :type old_link: str
    :returns: The next link.
    :rtype: str
    """

    if old_link.find("&_pgn=") == -1:
        return old_link + "&_pgn=2"
    else:
        end = old_link.find("&_pgn=") + len("&_pgn=")
        return old_link[:end] + str((int(old_link[end:]) + 1))

def extract(html, element_type, class_name, clean_func):
    """ Searches ``html`` for the contents of the first html tag of ``element_type`` and ``class_name``. 
    Before returning the html contents, clean the value with the ``clean_func``.
    
    :param html: a block of code representing a single listing
    :type html:
    :param element_type: The element type of the html tag to search for. For example, ``div``.
    :type element_type: str
    :param class_name: The class name of the html tag to search for.
    :type class_name: str
    :param clean_func: The function that converts the web text into a usable, readable format in the underlying data structure.
    :type clean_func: function
    :returns: The return value of clean_func on the inner contents on the found html tag. Returns None if nothing is found.
    :rtype: Ranges from str to int to datetime.datetime. 
    """

    raw = find_element(html, element_type, "class", class_name)
    
    if raw == None:
        return None

    while type(raw) == bs4.Tag:
        #go deeper in a nest
        raw = raw.contents[0]

    return clean_func(str(raw)) #usable format for my algorithm

def is_overlapping(date_stored, date_appended):
    """Determines whether date_stored is more into the past than date_appended. That is, date_appended is closer to the present day.

    :param date_stored, date_appended: Dates in time.
    :type date_stored, date_appended: datetime.datetime
    :returns: True if date_appended is closer to present day than date_stored.
    :rtype: bool
    """
    if (date_stored and date_appended) and (date_appended < date_stored):
        printer.overlap(date_appended, date_stored)
        return True

def get_data(listing):
    """Returns all meaningfull item data from the html block.

    :param listing: html block containing item data for a single listing.
    :type listing:
    :returns: the title, price, shipping, and date values of the listing.
    :rtype: tuple
    """
    title = extract(listing, "h3", "s-item__title", clean_title)
    price = extract(listing, "span", "s-item__price", clean_price)
    shipping = extract(listing, "span", "s-item__shipping", clean_shipping)
    date = extract(listing, "div", "s-item__title--tagblock", clean_date)

    return title, price, shipping, date
    
#@timer
def search_listings(html, print_stats = False):
    """Yields item data from listings in a single page's html.
    
    :param html: html code for an entire webpage
    :type html:
    :param print_stats: Determines whether to print updates on the scraping process
    :type print_stats: bool
    :yields: the title, total_cost and date associated with a single listing on the html page.
    """
    element_type, class_code = "li", "s-item"
    bad_listing_store = pd.read_csv(BAD_LISTING_DIR)

    counter = dict([("added", 0), ("skipped_early", 0), ("class_code", 0), ("bad", 0)])

    for listing in html.find_all(element_type):
        if listing.get("class") == None:
            counter["skipped_early"] += 1
            continue
        else:
            class_name = listing.get("class")[0]

        if class_name == class_code:
            title, price, shipping, date = get_data(listing)

            #if all([attr is not None for attr in [title, price, date, shipping]]):
            if all([type(attr) is not list for attr in [title, price, date, shipping]]):
                total_cost = round(price+shipping, 2)
                yield title, total_cost, date
                counter["added"] += 1
            else:
                title, price, date, shipping = [item[0] if type(item) == list else item for item in [title, price, date, shipping]]
                bad_listing_store = bad_listing_store.append({
                    "title": title,
                    "price": price,
                    "shipping": shipping,
                    "date": date
                    }, ignore_index=True)

                counter["bad"] += 1
        else:
            counter["class_code"] += 1

    bad_listing_store.drop_duplicates().to_csv(BAD_LISTING_DIR, index = None)

    if print_stats:
        num_listings = len(html.find_all(element_type))
        printer.page_stats_one(num_listings, **counter)
