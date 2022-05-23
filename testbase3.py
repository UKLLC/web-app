# sidebar.py
from os import read
from re import S
from sre_parse import State
import dash
import dash_bootstrap_components as dbc
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import pandas as pd
from dash import Dash, Input, Output, State, callback, dash_table, ALL

from app_state import App_State
import read_data_request

###########################################
### Styles
 
app = dash.Dash(external_stylesheets=["https://ukllc.ac.uk/assets/css/bootstrap.min.css?v=1650990372"])
TITLEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "width": "100%",
    "height": "5rem",
    "padding": "1rem 0.5rem",
    "background-color": "black",
    "color": "white",
    "textAlign":"center",
    "zIndex":1
}
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": "5rem",
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "overflow": "scroll",
}
BOX_STYLE = {
    "width": "45%",
    "height": "20rem",
    "min-width": "25rem",
    "background-color": "#f8f9fa",
    "overflow": "scroll",
    "margin-top": "1rem",
    "margin-bottom":"0rem",
    "margin-left":"1rem",
    "margin-right":"1rem",
    "display":"inline-block",
    "zIndex":0
}
ROW_STYLE = {
    "height": "100%",
}
CONTENT_STYLE = {
    "position": "relative",
    "top": "5rem",
    "margin-left": "15rem",

    "height": "100%",

}
###########################################

###########################################
### Data prep functions
request_form_url = "https://uob.sharepoint.com/:x:/r/teams/grp-UKLLCResourcesforResearchers/Shared%20Documents/General/1.%20Application%20Process/2.%20Data%20Request%20Forms/Data%20Request%20Form.xlsx?d=w01a4efd8327f4092899dbe3fe28793bd&csf=1&web=1&e=reAgWe"
# request url doesn't work just yet
study_df = read_data_request.load_study_request()
linked_df = read_data_request.load_linked_request()
schema_df = pd.concat([study_df[["Study"]].rename(columns = {"Study":"Data Directory"}).drop_duplicates().dropna(), pd.DataFrame([["NHSD"]], columns = ["Data Directory"])])
study_info_and_links_df = read_data_request.load_study_info_and_links()


def get_study_tables(schema):
    return study_df.loc[study_df["Study"] == schema]

DATA_DESC_COLS = ["Timepoint: Data Collected","Timepoint: Keyword","Number of Participants Invited (n=)","Number of Participants Included (n=)","Block Description","Links"]

app_state = App_State()
##########################################

###########################################
### page asset templates
titlebar = html.Div([html.H1("Data Discoverability Resource", className="title")],style = TITLEBAR_STYLE)

def single_col_table(df, id):
    return dash_table.DataTable(
            id=id,
            data=df.to_dict('records'),
            editable=False,
            
            column_selectable="single",
            row_selectable=False,
            row_deletable=False,
            style_cell={'textAlign': 'left'}
            )

def quick_table(df, id):
    return dash_table.DataTable(
            id=id,
            data=df.to_dict('records'),
            columns=[{"name": i, "id": i} for i in df.columns], 
            editable=False,
            row_selectable=False,
            row_deletable=False,
            style_cell={'textAlign': 'left','overflow': 'hidden',
            'textOverflow': 'ellipsis',
            'maxWidth': 0},
            )

def make_sidebar():
    sidebar_children = []
    schema_df = pd.concat([study_df[["Study"]].rename(columns = {"Study":"Data Directory"}).drop_duplicates().dropna(), pd.DataFrame([["NHSD"]], columns = ["Data Directory"])])
    for i, row in schema_df.iterrows():
        schema = row["Data Directory"]

        tables = get_study_tables(schema)["Block Name"]

        schema_children = dbc.Collapse(html.Div([html.Ul(id = schema+"_tables_list",
        children = [html.Div([
            html.Li(table, style={"border":"dotted"})],id={
            'type': 'sidebar_table_item',
            "value":schema+"-"+table
        }) for table in tables],
        style = {"list-style-type":"none", "margin-left": "0.5rem", "padding": 0})],)
        , id={
            'type': 'schema_collapse',
            'index': i
        },
        style={"border":"dotted"},
        is_open=False)

        sidebar_children += [html.Div([html.Li(schema)], id={
            'type': 'schema_item',
            'index': i
        },
        style={"border":"dotted", "padding": "0.25rem"})] + [schema_children]
    return html.Ul(sidebar_children, style = {"list-style-type":"none", "margin": 0, "padding": 0})

sidebar = html.Div([
        make_sidebar()],
        style =SIDEBAR_STYLE,
        id = "sidebar_div")

maindiv = html.Div(
    id="body",
    children=[
        # first row
        html.Div([
            html.Div([
                html.H2("Tables"),
                html.Hr(),
                html.Div([
                html.P("Table list")
                ], id = "tables_text"),
            ],
            style=BOX_STYLE,
            id="tables_div"
            ),

            html.Div([
                html.H2("Description"),
                html.Hr(),
                html.Div([
                html.P("Select a schema...")
                ], id = "description_text1"),
                html.Div([
                ], id = "description_text2"),
            ],
            style= BOX_STYLE,
            id="description_div"
            ),
        ],
        id = "row1",
        style = ROW_STYLE
        ),

        # second row
        html.Div([
            html.Div([
                html.H2("Variables"),
                html.Hr(),
                html.Div([
                html.P("Variables list...")
                ], id = "variables_text"),
            ],
            style=BOX_STYLE
            ),
            html.Div([
                html.H2("Values"),
                html.Hr(),
                html.Div([
                html.P("Values list...")
                ], id = "values_text"),
            ],
            style=BOX_STYLE
            )
            ],
        id = "row2",
        style = ROW_STYLE)
    ],
    style=CONTENT_STYLE
    )


schema_record = html.Div([],id = {"type":"active_schema", "content":"None"})
table_record = html.Div([], id = {"type":"active_table", "content":"None"})

###########################################

###########################################
### Layout
app.layout = html.Div([titlebar, sidebar, maindiv, schema_record, table_record])
###########################################

###########################################
### Actions


@app.callback(
    Output({'type': 'schema_collapse', 'index': ALL}, 'is_open'),
    Output({'type': 'active_schema', 'content': ALL}, 'id'),
    Input({'type': 'active_schema', 'content': ALL}, 'id'),
    Input({'type': 'schema_item', 'index': ALL}, 'n_clicks'),
    State({"type": "schema_collapse", "index" : ALL}, "is_open"),
)
def sidebar_collapse(current_schema, values, collapse):

    schema = current_schema[0]["content"]
    for (i, value) in enumerate(values):
        if value == None: 
            app_state.set_sidebar_clicks(i, 0)
        else:
            stored = app_state.get_sidebar_clicks(i)
            if stored != value:
                collapse[i] = not collapse[i]
                if collapse[i]:
                    schema = schema_df["Data Directory"].iloc[i]
                    print("opened", schema)
                print("Action on index {}, schema {}. Stored {}, current {}".format(i, schema, stored, value))

            app_state.set_sidebar_clicks(i, value)
    print(schema)

    return collapse, [{"type":"active_schema", "content":schema}]


@app.callback(
    Output('tables_text', "children"),
    Input({'type': 'sidebar_table_item', "value":ALL}, 'n_clicks'),
    Input({'type': 'sidebar_table_item', "value":ALL}, 'id'),
)
def update_tables_table(table_nclicks, table_values):

    nclick_dict = {}
    for clicks, id in zip(table_nclicks, table_values):
        nclick_dict[id["value"]] = clicks

    for key, value in nclick_dict.items():
        schema = key.split("-")[0]
        table = key.split("-")[1:]
        if value == None: 
            app_state.set_sidebar_clicks(key, 0)
        else:
            stored = app_state.get_sidebar_clicks(key)
            app_state.set_sidebar_clicks(key, value)
            if stored != value:
                print("Action on table {}. Stored {}, current {}".format(key, schema, stored, value))
                if schema == "nhsd":
                    return "TODO: NHSD branch"
                else:
                    tables_df = get_study_tables(schema)[["Block Name"]]
                    app_state.set_tables_df(tables_df)
                    return single_col_table(tables_df, id = "tables_table")


        

@app.callback(
    Output('description_text1', "children"),
    Input({'type': 'active_schema', 'content': ALL}, 'id'),
)
def update_schema_description(schema):
    print("ACTIVE SCHEMA:",schema)
    schema = schema[0]["content"]
    if schema != "None":
        print(study_info_and_links_df)
        schema_info = study_info_and_links_df.loc[study_info_and_links_df["Study Schema"] == schema]
        print(schema_info)
        if schema == "NHSD":
            schema_info = "Generic info about nhsd"
            return schema_info
        else:
            out_text = []
            for col in schema_info.columns:
                out_text.append(html.B("{}:".format(col)))
                out_text.append(" {}".format(schema_info[col].values[0]))
                out_text.append(html.Br())
            return [html.Hr(), html.P(out_text)]

    else:
        return "Select a schema or table for more information..."

@app.callback(
    Output('description_text2', "children"),
    Input('sidebar_table', "active_cell"),
    Input('tables_table', "active_cell")
)
def update_table_description(sidebar_in, tables_in):
    if sidebar_in and tables_in:
        schema = schema_df.iloc[sidebar_in["row"]].values[0]
        table_row = get_study_tables(schema).iloc[tables_in["row"]]
        if schema == "NHSD":
            schema_info = "Generic info about nhsd table"
            return schema_info
        else:
            out_text = []
            for col in DATA_DESC_COLS:
                out_text.append(html.B("{}:".format(col)))
                out_text.append(" {}".format(table_row[col]))
                out_text.append(html.Br())
            return [html.Hr(), html.P(out_text)]
    else:
        return 


@app.callback(
    Output('variables_text', "children"),
    Input('sidebar_table', "active_cell"),
    Input('tables_table', "active_cell")
)
def update_table_variables(sidebar_in, tables_in):
    if sidebar_in and tables_in:
        schema = schema.iloc[sidebar_in["row"]].values[0]
        if schema == "NHSD":
            schema_info = "variables for nhsd"
            return schema_info
        else:
            table = app_state.get_tables_df().iloc[tables_in["row"]]["Block Name"]
            descs_df = pd.read_csv("metadata\\{}\\{}_description.csv".format(schema,table))[["variable_name", "variable_label"]]
            app_state.set_descs_df(descs_df)
            return quick_table(descs_df, "variables_table")
    else:
        return 


@app.callback(
    Output('values_text', "children"),
    Input('sidebar_table', "active_cell"),
    Input('tables_table', "active_cell"),
    Input('variables_table', "active_cell")
)
def update_variables_values(sidebar_in, tables_in, variable_in):
    if sidebar_in and tables_in and variable_in:
        schema = schema_df.iloc[sidebar_in["row"]].values[0]
        table = app_state.get_tables_df().iloc[tables_in["row"]].values[0]
        variable = app_state.get_descs_df().iloc[variable_in["row"]].values[0]
        
        full_vals_df = pd.read_csv("metadata\\{}\\{}_values.csv".format(schema,table))[["variable_name", "value_value", "value_label"]]
        vals_df = full_vals_df.loc[full_vals_df["variable_name"] == variable].drop(columns = ["variable_name"])
        app_state.set_vals_df(vals_df)
        if len(vals_df) > 0:
            return quick_table(vals_df, "values_table")
        else:
            return "No values available for {}.{}: {}".format(schema, table, variable)
    else:
        return 

###########################################



'''
how to gen a sidebar list
first, every list item must be in a div for formatting
we figure out the fully expanded list then collapse table part
1. organise schema + tables into list in schema order
2. enclose all tables for a schema in a div - this div can be collapsed

We have a problem - we have to figure out a substitue for "active cell"
if we use type = sidebar_schema and type = sidebar_table we can listen for each (look at pattern-matching docs). We can also set the id of each div to the useful value of its contents so we can locate it!
'''#





if __name__ == "__main__":
    app.run_server(port=8888)
