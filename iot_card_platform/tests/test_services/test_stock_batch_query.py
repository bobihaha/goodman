from app.crud.stock_crud import StockSummaryCRUD


def test_stock_batch_query_normalizes_input_order_and_duplicates():
    normalized, duplicates = StockSummaryCRUD._parse_iccid_query([
        " 8986112520609490919 ",
        "",
        "8986112520609490920",
        "8986112520609490919",
    ])

    assert normalized == [
        "8986112520609490919",
        "8986112520609490920",
    ]
    assert duplicates == ["8986112520609490919"]
