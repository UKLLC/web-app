import time
from elasticsearch import Elasticsearch
from urllib.parse import urlparse

def searchbox_connect():
    
    url = urlparse("https://paas:42e48b21cfd2609467edf2b1ace1c0be@gimli-eu-west-1.searchly.com")
    ######## test
    es = Elasticsearch(
        ["https://paas:42e48b21cfd2609467edf2b1ace1c0be@gimli-eu-west-1.searchly.com"],
        http_auth=(url.username, url.password),
        scheme=url.scheme,
        port=url.port,
    )
    return es


if __name__ == "__main__":


    all_query2 = {
        "query": {
            "bool" : {
                "filter":[{
                        "bool" : {
                            "should" : [{"term" : { "source" : "ukhls"}}] 
                        }
                    },
                    
                ],
                
                

                }
            }
        }

    ######################################################################################
    ### Data prep functions

    es = searchbox_connect()

    r2 = es.search(index="index_var", body=all_query2, size = 1000)
    search_results = []
    
    for hit in r2["hits"]["hits"]:
        search_results.append([hit["_source"]["source"], hit["_source"]["table"], hit["_source"]["variable_name"], hit["_source"]["variable_description"]])

    print(search_results)
