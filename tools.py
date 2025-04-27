from typing import List, Dict
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig

from langchain_core.vectorstores import InMemoryVectorStore
from langchain_ollama.embeddings import OllamaEmbeddings
from langchain_core.documents import Document

import json
import os

from unit_price import UnitPrice

import asyncio

async def search_and_extract_products_by_merchant(merchants:str | List[str], search_query:str)-> List[Dict]:
    """Search the merchant's website on the search_query (item)

    Args:
        merchants (UNION[str, List(str)]):  name or names of the merchants, value of merchant can be one from this list ["ASDA", "Tesco", "Sainsburys", "Ocado"]
        search_query (str): the item user wants to search on the merchant's website

    Returns:
        List[Dict]: List of items from each merchant that are most similar to the search query.
    """

    if isinstance(merchants, str):
        merchants = [merchants]
    
    results = {}

    for merchant in merchants:
        # Initialize browser config
        browser_config = BrowserConfig(browser_type="chromium", headless=True)

        # Read config
        config_file_path = os.path.join(os.path.dirname(__file__),"config.json")
        with open(config_file_path, 'r') as file:
            config = json.load(file)
        
        merchant_config = config["supermarkets"][merchant]

        # Initialize crawler config with JSON CSS extraction strategy
        crawler_config = CrawlerRunConfig(
            wait_for=merchant_config["crawler_config"]["wait_for"],
            extraction_strategy=JsonCssExtractionStrategy(
                schema=merchant_config["crawler_config"]["schema"]
            )
        )

        # encode search_query if has ' ' in it
        search_query = '%20'.join(search_query.split(' '))

        url = merchant_config["search_url"] + search_query

        print("========================")
        print("Search url:")
        print(url)
        print("========================")
        
        # Use context manager for proper resource handling
        async with AsyncWebCrawler(config=browser_config) as crawler:

            # Extract the data
            result = await crawler.arun(url=url, config=crawler_config)

            # Process and print the results
            if result and result.extracted_content:
                # Parse the JSON string into a list of products
                results[merchant] = [dict(x, **{'merchant':merchant}) for x in json.loads(result.extracted_content)]

    return await get_best_k_matching_items(results, search_query)
        
async def get_best_k_matching_items(data:Dict[str, List[Dict[str, str]]], search_query:str, k:int=3) -> List[Dict]:
    """find k most similar items that matches the search query. 

    Args:
        data (Dict[str, List[Dict[str, str]]]): items found on the merchant's website. dictionary key is the name of merchant. dictionary value is list of items found. 
                                        Items found can be multiple items. each item is representated by a dictionary. 
                                        The inner dictionary key can include --
                                                item_name - name of the item found.
                                                pack_size - size of each pack.
                                                price - price of the item found.
                                                price_per_unit - price per unit.
                                                merchant - merchant name.
        search_query (str): user search query used to search on the merchant's website.
        k (int, optional): number of best matching items. Defaults to 3.

    Returns:
        List[Dict]: List of k items from each merchant that are most similar to the search query. return list should has size k*len(data).
    """

    results = []

    for key, value in data.items():

        vector_store = InMemoryVectorStore(OllamaEmbeddings(model='llama3.2'))
        documents = [Document(page_content=x['item_name'], metadata=x) for x in value]
        await vector_store.aadd_documents(documents)
        result = await vector_store.asimilarity_search(query=search_query,k=k)
    
        results += [x.metadata for x in result]

    unit_price = UnitPrice()
    
    results = [x for x in results if 'price_per_unit' in x]

    [x.update(price_per_unit = unit_price.parse_unit_price(x['price_per_unit'])) for x in results]

    return results

