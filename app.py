# sidebar.py
from os import read
from re import S
import re
import dash
import dash_bootstrap_components as dbc
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import pandas as pd
from dash import Dash, Input, Output, State, callback, dash_table, ALL, MATCH
import dash_leaflet as dl
import dash_leaflet.express as dlx
from dash_extensions.javascript import arrow_function
from dash_extensions.javascript import assign
import json
import time
import warnings
import logging
from dash.exceptions import PreventUpdate
from flask_caching import Cache

from app_state import App_State
import dataIO
import stylesheet as ss
import constants 
import structures as struct


######################################################################################
app = dash.Dash(__name__, external_stylesheets=["custom.css"])
server = app.server

######################################################################################
### Data prep functions


request_form_url = "https://uob.sharepoint.com/:x:/r/teams/grp-UKLLCResourcesforResearchers/Shared%20Documents/General/1.%20Application%20Process/2.%20Data%20Request%20Forms/Data%20Request%20Form.xlsx?d=w01a4efd8327f4092899dbe3fe28793bd&csf=1&web=1&e=reAgWe"
# request url doesn't work just yet
study_df = dataIO.load_study_request()
linked_df = dataIO.load_linked_request()
schema_df = pd.concat([study_df[["Study"]].rename(columns = {"Study":"Data Directory"}).drop_duplicates().dropna(), pd.DataFrame([["NHSD"]], columns = ["Data Directory"])])
study_info_and_links_df = dataIO.load_study_info_and_links()

app_state = App_State(schema_df)

def load_or_fetch_map(study):
    returned_data = app_state.get_map_data(study) # memorisation of polygons
    if not returned_data: # if no saved map data, returns False
        try:
            returned_data = dataIO.get_map_overlays(study)
        except IOError:
            print("Unable to load map file {}.geojson".format(study))
        app_state.set_map_data(study, returned_data)
    return returned_data
    
    
def get_study_tables(schema):
    return study_df.loc[study_df["Study"] == schema]
        
######################################################################################

######################################################################################
### page asset templates

# Titlebar ###########################################################################
titlebar = struct.main_titlebar(app, "Data Discoverability Resource")

# Left Sidebar #######################################################################

sidebar_catalogue = struct.make_sidebar_catalogue(study_df)
sidebar_title = struct.make_sidebar_title()
sidebar_footer = struct.make_sidebar_footer()
sidebar_left = struct.make_sidebar_left(sidebar_title, sidebar_catalogue, sidebar_footer)

# Context bar #########################################################################

context_bar_div = struct.make_context_bar()

# Body ################################################################################

# Main div template ##################################################################
maindiv = struct.make_body()
schema_record = struct.make_variable_div("active_schema")
table_record = struct.make_variable_div("active_table")
shopping_basket_op = struct.make_variable_div("shopping_basket", [])
open_schemas = struct.make_variable_div("open_schemas", [])

hidden_body = struct.make_hidden_body()

# Variable Divs ####################################################################

###########################################
### Layout
app.layout = struct.make_app_layout(titlebar, sidebar_left, context_bar_div, maindiv, [schema_record, table_record, shopping_basket_op, open_schemas, hidden_body])
print("Built app layout")
###########################################
### Actions

### DOCUMENTATION BOX #####################
@app.callback(
    Output('doc_title', "children"),
    Input('active_schema','data'),
    prevent_initial_call=True
)
def update_doc_header(schema):
    header = struct.make_section_title("Documentation: {}".format(schema))
    return header


@app.callback(
    Output('schema_description_div', "children"),
    Input('active_schema','data'),
    prevent_initial_call=True
)
def update_schema_description(schema):
    print("CALLBACK: DOC BOX - updating schema description")

    if schema != "None":
        schema_info = study_info_and_links_df.loc[study_info_and_links_df["Study Schema"] == schema]
        if schema == "NHSD":
            schema_info = "Generic info about nhsd"
            return schema_info
        else:      
            return struct.make_schema_description(schema_info)
    else:
        return ["Placeholder schema description, null schema - this should not be possible when contextual tabs is implemented"]


@app.callback(
    Output('table_description_div', "children"),
    Input('active_schema','data'),
    prevent_initial_call=True
)
def update_tables_description(schema):
    '''
    Replace contents of description box with table information 
    '''
    print("CALLBACK: DOC BOX - updating table description")

    if schema != "None":
        tables = get_study_tables(schema)
        if schema == "NHSD": # Expand to linked data branch
            schema_info = "Generic info about nhsd table"
            return schema_info
        else: # Study data branch
            return struct.data_doc_table(tables, "table_desc_table")
    else:
        return ["Placeholder table description, null schema - this should not be possible when contextual tabs is implemented"]


### METADATA BOX #####################
@app.callback(
    Output('metadata_title', "children"),
    Input('active_table','data'),
    prevent_initial_call=True
)
def update_doc_header(table):
    header = struct.make_section_title("Metadata: {}".format(table))
    return header


@app.callback(
    Output('table_meta_desc_div', "children"),
    Input('active_table', 'data'),
    State('active_schema', 'data'),
    prevent_initial_call=True
)
def update_table_data(table, schema):
    print("CALLBACK: META BOX - updating table description")
    #pass until metadata block ready
    if schema != "None" and table != "None":
        tables = get_study_tables(schema)
        tables = tables.loc[tables["Block Name"] == table.split("-")[1]]
        if schema == "NHSD": # Expand to linked data branch
            return html.P("NHSD placeholder text")
        else: # Study data branch
            return struct.metadata_doc_table(tables, "table_desc_table")
    else:
        # Default (Section may be hidden in final version)
        return "Placeholder metadata desc, null schema, null table - this should be impossible. Bug code 101."


@app.callback(
    Output('table_metadata_div', "children"),
    Input('active_table','data'),
    Input("values_toggle", "value"),
    Input("metadata_search", "value"),
    prevent_initial_call=True
)
def update_table_metadata(table, values_on, search):
    print("CALLBACK: META BOX - updating table metadata")

    table_id = table
    if table== "None":
        return ["Placeholder table metadata, null table - this should not be possible when contextual tabs is implemented"]
    try:
        metadata_df = dataIO.load_study_metadata(table_id)
    except FileNotFoundError: # Study has changed 
        print("Failed to load {}.csv".format(table_id))
        print("Preventing update in Meta box table metadata")
        raise PreventUpdate

    if type(values_on) == list and len(values_on) == 1:
        metadata_df = metadata_df[["Block Name", "Variable Name", "Variable Description", "Value", "Value Description"]]
        if type(search) == str and len(search) > 0:
            metadata_df = metadata_df.loc[
            (metadata_df["Block Name"].str.contains(search, flags=re.IGNORECASE)) | 
            (metadata_df["Variable Name"].str.contains(search, flags=re.IGNORECASE)) | 
            (metadata_df["Variable Description"].str.contains(search, flags=re.IGNORECASE)) |
            (metadata_df["Value"].astype(str).str.contains(search, flags=re.IGNORECASE)) |
            (metadata_df["Value Description"].str.contains(search, flags=re.IGNORECASE))
            ]
    else:
        metadata_df = metadata_df[["Block Name", "Variable Name", "Variable Description"]].drop_duplicates()
        if type(search) == str and len(search) > 0:
            metadata_df = metadata_df.loc[
            (metadata_df["Block Name"].str.contains(search, flags=re.IGNORECASE)) | 
            (metadata_df["Variable Name"].str.contains(search, flags=re.IGNORECASE)) | 
            (metadata_df["Variable Description"].str.contains(search, flags=re.IGNORECASE)) 
            ]

    return struct.metadata_table(metadata_df, "metadata_table")

### MAP BOX #################

@app.callback(
    Output('map_title', "children"),
    Input('active_schema','data'),
    prevent_initial_call=True
)
def update_map_header(schema):
    header = struct.make_section_title("Coverage: {}".format(schema))
    return header


@app.callback(
    Output('map_region', "data"),
    Output('map_object', 'zoom'),
    Input('body','children'), # Get it to trigger on first load to get past zoom bug
    Input('active_schema','data'),
    prevent_initial_call=True
)
def update_doc_header(_, schema):
    map_data = load_or_fetch_map(schema)
    if not map_data:
        return None, 6
    return map_data, 6


#########################
@app.callback(

    Output("context_tabs","children"),
    Input('active_schema','data'),
    Input('active_table','data'),
    prevent_initial_call=True
)
def context_tabs(schema, table):
    #print("DEBUG, context_tabs {} {}, {} {}".format(schema, type(schema), table, type(table)))
    if schema != "None":
        if table != "None":
            return [dcc.Tab(label='Documentation', value="Documentation"),
            dcc.Tab(label='Metadata', value='Metadata'),
            dcc.Tab(label='Coverage', value='Map')]
        else:
            return [dcc.Tab(label='Documentation', value="Documentation"),
            dcc.Tab(label='Coverage', value='Map')]
    else:
        return [dcc.Tab(label='Introduction', value="Introduction")]


@app.callback(
    Output("body", "children"),
    Output("hidden_body","children"),
    Input("context_tabs", "value"),
    State("body", "children"),
    State("hidden_body","children"),
    prevent_initial_call=True
)
def body_sctions(tab, active_body, hidden_body):
    print("CALLBACK: BODY, activating", tab)
    sections_states = {}
    for section in active_body + hidden_body:
        section_id = section["props"]["children"][1]["props"]["id"]
        sections_states[section_id] = section

    a_tab_is_active = False
    sections = app_state.sections
    active = []
    inactive = []
    for section in sections.keys():
        if section in tab:
            active.append(section)
            a_tab_is_active = True
        else:
            inactive.append(section)

    # Check: if no tabs are active, run landing page
    if not a_tab_is_active:
        print("TODO: landing page:")
        return [sections_states["Landing"]],  [sections_states[s_id] for s_id in active]

    return [sections_states[s_id] for s_id in active], [sections_states[s_id] for s_id in inactive]


@app.callback(
    Output('active_schema','data'),
    Output("open_schemas", "data"),
    Input("schema_accordion", "active_item"),
    State("active_schema", "data"),
    State("open_schemas", "data"),
    prevent_initial_call = True
)# NOTE: is this going to be slow? we are pattern matching all schema. Could we bring it to a higher level? like the list group? Or will match save it
def sidebar_schema(schemas, schema, open_schemas):
    print("CALLBACK: sidebar schema click")
    # print("DEBUG, sidebar_schema {} {}, {} {}".format(schemas, type(schemas), schema, type(schema), open_schemas, type(open_schemas)))
    if not schemas:
        return schema, []

    if open_schemas == None:
        open_schemas = []

    new_schemas = [sch for sch in schemas if sch not in open_schemas]

    if len(new_schemas) == 1:
        print("Opened new schema:", new_schemas[0])
        schema = new_schemas[0]
        
    elif len(new_schemas) == 0:
        print("no new schemas")
        # Keep current schema for simplicity
    else:
        raise Exception("Error 1733")

    open_schemas = schemas
    return schema, open_schemas



@app.callback(
    Output('active_table','data'),
    Output({"type": "table_tabs", "index": ALL}, 'value'),
    Input({"type": "table_tabs", "index": ALL}, 'value'),
    State("active_table", "data"),

    prevent_initial_call = True
)
def sidebar_table(tables, table):
    print("CALLBACK: sidebar table click")
    active = [t for t in tables if t!= "None"]
    if len(active) == 0:
        return "None", tables
    elif len(active) != 1:
        active = [t for t in active if t != table ]
        if len(active) == 0:
            return table, tables
        tables = [(t if t in active else "None") for t in tables]
        if len(active) != 1:
            raise 

    table = active[0]
    return active[0], tables 
    

@app.callback(
    Output("sidebar_list_div", "children"),
    Input("search_button", "n_clicks"),
    Input("main_search", "value"),
    State("open_schemas", "data"),
    State("shopping_basket", "data"),
    State("active_table", "data"),
    prevent_initial_call = True
    )
def main_search(_, search, open_schemas, shopping_basket, table):
    '''
    Version 1: search by similar text in schema, table name or keywords. 
    these may be branched into different search functions later, but for now will do the trick
    Do we want it on button click or auto filter?
    Probs on button click, that way we minimise what could be quite complex filtering
    '''
    print("CALLBACK: main search")

    if type(search)!=str or search == "":
        return struct.build_sidebar_list(study_df, shopping_basket, open_schemas, table)

    sub_list = study_df.loc[
        (study_df["Study"].str.contains(search, flags=re.IGNORECASE)) | 
        (study_df["Block Name"].str.contains(search, flags=re.IGNORECASE)) | 
        (study_df["Keywords"].str.contains(search, flags=re.IGNORECASE)) | 
        (study_df[constants.keyword_cols[1]].str.contains(search, flags=re.IGNORECASE)) |
        (study_df[constants.keyword_cols[2]].str.contains(search, flags=re.IGNORECASE)) |
        (study_df[constants.keyword_cols[3]].str.contains(search, flags=re.IGNORECASE)) |
        (study_df[constants.keyword_cols[4]].str.contains(search, flags=re.IGNORECASE))
        ]

    return struct.build_sidebar_list(sub_list, shopping_basket, open_schemas, table)


@app.callback(
    Output('shopping_basket','data'),
    Input({"type": "shopping_checklist", "index" : ALL}, "value"),
    State("shopping_basket", "data"),
    prevent_initial_call=True
    )
def shopping_cart(selected, shopping_basket):
    print("CALLBACK: Shopping cart")

    selected = [i[0] for i in selected if i !=[]]
    shopping_basket = selected

    return shopping_basket


@app.callback(
    Output('sb_download','data'),
    Input("save_button", "n_clicks"),
    State("shopping_basket", "data"),
    prevent_initial_call=True
    )
def save_shopping_cart(_, shopping_basket):
    '''
    input save button
    Get list of selected checkboxes - how? can just save shopping cart as is, list of ids
    
    '''
    print("CALLBACK: Save shopping cart")
    # TODO insert checks to not save if the shopping basket is empty or otherwise invalid
    fileout = dataIO.basket_out(shopping_basket)
    
    return dcc.send_data_frame(fileout.to_csv, "shopping_basket.csv")

if __name__ == "__main__":
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    pd.options.mode.chained_assignment = None
    warnings.simplefilter(action="ignore",category = FutureWarning)
    app.run_server(port=8888, debug = True)
    
''''
thoughts on efficiency:
    index throughout
    using match rather than all will be a big improvement.
    tables must be ided by index not key. 
    We currently use key. 
    Thats fine, we can have a dictionary of table key to index setup at the start or even in pre
    Table must always have same index or search will break it.
    can also use index in hidden divs

    This doesn't answer the question of how we efficiently set a list item active and set all others inactive.
    I don't have any ideas for this one just yet. 
    Well. We could make a new callback chain
    Send the old table to a holder
    update - invert active on that index
    update the same callback with the new table
    update - invert active on that index.
    Could work. Bit complex, but its getting that way in general.
    Best wait for the merge at 2:30 though. hour and a half. Go scran. 

    1. Give every table an id (may as well do for study too)
'''