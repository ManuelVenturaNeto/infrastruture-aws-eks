import pyarrow as pa
import pyarrow.csv

COTAHIST = "https://bvmf.bmfbovespa.com.br/InstDados/SerHist/COTAHIST_A{year}.ZIP"
LISTED = "https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall"
COMPANIES = f"{LISTED}/GetInitialCompanies/{{payload}}"
SUPPLEMENT = f"{LISTED}/GetListedSupplementCompany/{{payload}}"
LANGUAGE = "pt-br"
PAGE_SIZE = 120
NEVER_LISTED = "31/12/9999"
EVENTS_FILE = "events.parquet"
FIRST_YEAR = 1986

TEXT, INT, PRICE, DATE = "text", "int", "price", "date"
QUOTE_RECORD = "01"
PRICE_SCALE = 100.0
DELIMITER = "\x01"

LAYOUT = (
    ("trade_date", 3, 10, DATE),
    ("bdi_code", 11, 12, TEXT),
    ("ticker", 13, 24, TEXT),
    ("market_type", 25, 27, TEXT),
    ("company_name", 28, 39, TEXT),
    ("specification", 40, 49, TEXT),
    ("forward_term", 50, 52, TEXT),
    ("currency", 53, 56, TEXT),
    ("open_price", 57, 69, PRICE),
    ("high_price", 70, 82, PRICE),
    ("low_price", 83, 95, PRICE),
    ("average_price", 96, 108, PRICE),
    ("close_price", 109, 121, PRICE),
    ("best_bid_price", 122, 134, PRICE),
    ("best_ask_price", 135, 147, PRICE),
    ("total_trades", 148, 152, INT),
    ("total_quantity", 153, 170, INT),
    ("total_volume", 171, 188, PRICE),
    ("strike_price", 189, 201, PRICE),
    ("correction_indicator", 202, 202, TEXT),
    ("expiration_date", 203, 210, DATE),
    ("quote_factor", 211, 217, INT),
    ("strike_points", 218, 230, INT),
    ("isin_code", 231, 242, TEXT),
    ("distribution_number", 243, 245, INT),
)

READ_OPTIONS = pyarrow.csv.ReadOptions(
    column_names=["line"], encoding="latin-1", block_size=64 << 20
)
PARSE_OPTIONS = pyarrow.csv.ParseOptions(delimiter=DELIMITER, quote_char=False)
CONVERT_OPTIONS = pyarrow.csv.ConvertOptions(column_types={"line": pa.string()})
EVENTS_SCHEMA = pa.schema(
    [
        ("issuing_company", pa.string()),
        ("isin_code", pa.string()),
        ("label", pa.string()),
        ("factor", pa.float64()),
        ("last_date_prior", pa.date32()),
        ("approved_on", pa.date32()),
    ]
)
