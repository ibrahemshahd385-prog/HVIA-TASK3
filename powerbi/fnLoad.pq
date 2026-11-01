// Cottonil – Power Query loader (paste in: Home > Transform data > New Source > Blank Query > Advanced Editor). Name it fnLoad.
// Parameter first: Home > Manage Parameters > New → Name: DataFolder · Type: Text ·
//   Value: C:\Users\start\OneDrive\Desktop\HVIA-TASK3\powerbi\data\   (keep the last backslash)
// Then for each CSV: New Source > Blank Query →  = fnLoad("fact_sales_line")  and rename the query to the same name.
(TableName as text) as table =>
let
    Source   = Csv.Document(File.Contents(DataFolder & TableName & ".csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    TypeOf   = (c as text) as type =>
        let l = Text.Lower(c) in
        if List.Contains({"has_discount", "before_opening", "is_full_fy", "in_sales_data"}, l) then type logical
        else if l = "date" or Text.EndsWith(l, "_date") or l = "month_start" then type date
        else if List.Contains({"fy", "month_num", "quantity", "quantity_units", "return_quantity", "items_count", "closing_units",
                               "impressions", "clicks", "orders_attributed", "capacity_units", "page"}, l) then Int64.Type
        else if Text.Contains(l, "_egp") or List.Contains({"forecast_3m", "safety_stock", "stock_on_hand", "to_buy", "current_pattern_buys",
                               "months_of_stock", "send_next_month", "sent_per_month_fy2026"}, l) then type number
        else type text,
    Typed    = Table.TransformColumnTypes(Promoted, List.Transform(Table.ColumnNames(Promoted), each {_, TypeOf(_)}), "en-US")
in
    Typed
