class App_State():
    def __init__(self) -> None:
        self.schema = None
        self.table = None

        self.tables_df = None
        self.descs_df = None
        self.vals_df = None
        self.sidebar_clicks = {}


    def get_tables_df(self):
        return self.tables_df

    def set_tables_df(self, tables_df):
        self.tables_df = tables_df

    def get_descs_df(self):
        return self.descs_df

    def set_descs_df(self, descs_df):
        self.descs_df = descs_df

    def get_vals_df(self):
        return self.vals_df

    def set_vals_df(self, vals_df):
        self.vals_df = vals_df

    def set_sidebar_clicks(self, index, nclick):
        if index not in self.sidebar_clicks:
            self.sidebar_clicks[index] = 0
        else:
            self.sidebar_clicks[index] = nclick

    def get_sidebar_clicks(self, index):
        return self.sidebar_clicks[index]

    def get_table_clicks(self, table_id, nclick):
        if table_id not in self.sidebar_clicks:
            self.sidebar_clicks[table_id] = 0
        else:
            self.sidebar_clicks[table_id] = nclick

    def get_sidebar_clicks(self, table_id):
        return self.sidebar_clicks[table_id]
