#from Ebay.ItemOrganization.ProductList import ProductList
from Ebay.ItemOrganization.queryList import queryList
from Ebay.Site_Operations.ebayFunctions_Grand import *
#aboutALink, getEbayLink

"""
DESCRIPTION OF HIGH LEVEL OPERATIONS

process of downloading html and iterating over pages
   request the link and download the html
   scrape data from the html
   export the data

process of importing and displaying the data
   import the data into a series of ProductList() objects
   per ProductList() object, graph its contents
   print all the graphs into a single pdf sheet
"""

#set up the web request client

from scraper_api import ScraperAPIClient
#client = ScraperAPIClient('c733663048589db82005534b6739c32e')
#client = ScraperAPIClient('cbbdd094d7401d8912b09341e37be9b1')

def whack_shit():
    """
    Print the total number of collected items. How many items are we tracking for every product? How big is the sample size?

    NOTE: THIS METHOD WILL NEED TO BE CHANGED. IMPORTPRODUCTDATA AND EXPORTPRODUCTDATA HAVE BEEN DELETED.
    """
    lengthList = []
    count = 0
    for query in totalQueries.queryCollection:
        length = 0

        query.importProductData(query.csvProductListAuction)
        length += len(query.productCollection.itemList)

        query.importProductData(query.csvProductListBIN)
        length += len(query.productCollection.itemList)
        #lengthList.append(length)

        if length < 500:
            print(f"{query.name:<30}{length}")
            count += 1

def test_export_function(client, totalQueries):
    """
    Does the new_export function work as intended?
    """


    query = totalQueries.queryCollection[0]
    print("collecting: ", query.name)

    length_of_auction_list, length_of_csv = [], [] # a list of numbers. the numbers represent the size of each list as the for loop cycles.

    for i in range(4):

        #data for Auction listings
        print(f"\n{query.name} AUCTION")
        tempList = ProductList()
        aboutALink(client, query.linkAuction, tempList)

        #after we populate tempList
        length_of_auction_list.append( len(tempList.itemList) )

        importList = ProductList()
        tempList.new_export(query.csvProductListAuction, importList)

        #after we populate the csv file
        length_of_csv.append( len(importList.itemList) )

        print("length for AUCTION", len(tempList.itemList))

    print(length_of_auction_list)
    print(length_of_csv)
    print("finished data collection")


#totalQueries = data_import()
#data_collection(client, totalQueries)
#test_export_function(client, totalQueries)
#data_visualization(totalQueries)


totalQueries = queryList()
totalQueries.importData()

#totalQueries.data_collection(client)
#totalQueries.data_visualization(client)