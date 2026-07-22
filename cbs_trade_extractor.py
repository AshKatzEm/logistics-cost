"""
CBS Foreign Trade Monthly Data Extractor
==========================================

Scans a directory of CBS xlsx releases and extracts rows into
monthly_trade_data.csv (created if it doesn't exist; new periods appended,
existing periods left alone on rerun).

File types handled (matched by substring in filename):
  - "ta2"  -> Imports by commodity category
  - "ta3"  -> Exports by commodity category
  - "td1"  -> Trade by country (current month snapshot only)
  - "te4"  -> Fisher volume indices (import/export)

All row/column positions below are EXCEL row/column numbers (1-indexed,
letters for columns) exactly as specified against the current CBS
template. These are FIXED positions, not dynamically detected - if CBS
changes their template layout in a future release, these will need
updating (the row deletions were counted against a specific reference
file - see project notes).

OUTPUT SCHEMA NOTES
--------------------
- 'Month' is the full English month name (roman numeral translated).
- 'Year' is forward-filled from the sparse year cells in the source sheet.
- 'date' is added as YYYY-MM-01 00:00 (first of month, midnight) so this
  file can be joined against other datasets that use a full
  "YYYY-MM-DD HH:MM" timestamp column - join by truncating the other
  dataset's timestamp down to its month.
- Country columns from td1 are named "{Country}_Import" / "{Country}_Export"
  using CBS's own country-name spelling verbatim (including footnote
  markers like "(1)"), with any internal whitespace collapsed to a single
  underscore. NOTE: CBS repeats "Other Countries" once per region, so
  several duplicate-named columns are expected and preserved as-is
  (pandas supports duplicate column labels) - not deduplicated.
"""

from __future__ import annotations

import argparse
import glob
import os
import re

import pandas as pd

ROMAN_TO_NUM = {
    "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6,
    "VII": 7, "VIII": 8, "IX": 9, "X": 10, "XI": 11, "XII": 12,
}
NUM_TO_MONTH_NAME = {
    1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
    7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December",
}


def slugify(name: str) -> str:
    """Collapse any run of whitespace into a single underscore."""
    return re.sub(r"\s+", "_", str(name).strip())


def excel_rows_to_drop(*specs) -> set[int]:
    """
    Convert a mix of single excel row numbers and (start, end) inclusive
    ranges (1-indexed, as seen in Excel) into a set of 0-indexed pandas
    row positions to drop.
    """
    drop = set()
    for spec in specs:
        if isinstance(spec, tuple):
            start, end = spec
            drop.update(range(start - 1, end))  # excel 1-indexed -> pandas 0-indexed
        else:
            drop.add(spec - 1)
    return drop


def forward_fill_year(series: pd.Series) -> pd.Series:
    """
    CBS sheets have a year value only in the row where the year changes;
    all rows below (until the next year value) are blank - but 'blank' is
    often a whitespace string (' '), not true NaN. Normalize then ffill.
    Non-numeric text above the data block (titles, headers) is left as-is;
    callers should only read this column for rows within the known data
    range, where every value will have resolved to a valid year by then.
    """
    cleaned = series.apply(lambda v: v.strip() if isinstance(v, str) else v)
    cleaned = cleaned.replace("", pd.NA)
    cleaned = cleaned.ffill()
    return cleaned


# ------------------------------------------------------------------
# TA2 - Imports by category
# ------------------------------------------------------------------

# for each file which has "ta2" in the name
# drop all excel rows 1-19
# drop all rows 33 - 77
# now there should be 13 columns
# FTB Import Returned (-)
# FTB Import Other
# FTB Import Ships and aircraft
# FTB Import Diamonds rough and working net
# FTB Import Fuels
# FTB Import Investment goods
# FTB Import Raw materials
# FTB Import Consumer goods
# FTB Import  excl. ships aircraft, diamonds and fuels
# FTB Import Total excl. ships aircraft and diamonds
# FTB Import Total
# Month [need to translate the roman numeral into english month name]
# Year [there is only one cell with year, we need many cells to have the year. for example there is a cell with 2025, all cells below that cell are 2025 data until there is a cell with 2026, then all cells below that are 2026]

# each row of these columns will be exported to our dataframe. Make sure the column names have "_" isnstead of " "

TA2_COLUMNS = [
    "FTB Import Returned (-)",
    "FTB Import Other",
    "FTB Import Ships and aircraft",
    "FTB Import Diamonds rough and working net",
    "FTB Import Fuels",
    "FTB Import Investment goods",
    "FTB Import Raw materials",
    "FTB Import Consumer goods",
    "FTB Import  excl. ships aircraft, diamonds and fuels",
    "FTB Import Total excl. ships aircraft and diamonds",
    "FTB Import Total",
]


def extract_ta2(path: str) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="a2", header=None)

    period_col, year_col = 11, 12
    df[year_col] = forward_fill_year(df[year_col])

    drop = excel_rows_to_drop((1, 19), (33, 77))
    keep = df.drop(index=[i for i in drop if i < len(df)])

    out = keep[[c for c in range(11)]].copy()
    out.columns = [slugify(c) for c in TA2_COLUMNS]
    out["Month"] = keep[period_col].apply(lambda r: NUM_TO_MONTH_NAME[ROMAN_TO_NUM[r.strip()]])
    out["Year"] = keep[year_col].astype(float).astype(int).values
    return out


# ------------------------------------------------------------------
# TA3 - Exports by category
# ------------------------------------------------------------------
# for each file which has "ta3" in the name
# drop all excel rows 1-20
# drop all rows 34 - 77
# now there should be 13 columns
# FTB Export Returned (-)
# FTB Export Wholesale of diamonds
# FTB Export Working of diamonds
# FTB Export Other
# FTB Export Manufacturing, mining  & quarrying excl.working diamonds
# FTB Export Agriculture, forestry and fishing 
# FTB Export Total excl. ships, aircraft and diamonds
# FTB Export Total
# Month [need to translate the roman numeral into english month name]
# Year [there is only one cell with year, we need many cells to have the year. for example there is a cell with 2025, all cells below that cell are 2025 data until there is a cell with 2026, then all cells below that are 2026]


# each row of these columns will be exported to our dataframe. Make sure the column names have "_" isnstead of " "



TA3_COLUMNS = [
    "FTB Export Returned (-)",
    "FTB Export Wholesale of diamonds",
    "FTB Export Working of diamonds",
    "FTB Export Other",
    "FTB Export Manufacturing, mining  & quarrying excl.working diamonds",
    "FTB Export Agriculture, forestry and fishing",
    "FTB Export Total excl. ships, aircraft and diamonds",
    "FTB Export Total",
]


def extract_ta3(path: str) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="a3", header=None)

    period_col, year_col = 8, 9
    df[year_col] = forward_fill_year(df[year_col])

    drop = excel_rows_to_drop((1, 20), (34, 77))
    keep = df.drop(index=[i for i in drop if i < len(df)])

    out = keep[[c for c in range(8)]].copy()
    out.columns = [slugify(c) for c in TA3_COLUMNS]
    out["Month"] = keep[period_col].apply(lambda r: NUM_TO_MONTH_NAME[ROMAN_TO_NUM[r.strip()]])
    out["Year"] = keep[year_col].astype(float).astype(int).values
    return out

# for each file which has "te4" in the name
# if it has 7 columns:
# delete rows 1-28, 41, 42
#delete columns B, C, E

# if it has 5 columns:
# delete rows 1-28, 41, 42
# delete column B

# now in either case, left with 4 columns:
# fisher_export_volume,
#fisher_import_volume, 
# Month [need to translate the roman numeral into english month name]
# Year [there is only one cell with year, we need many cells to have the year. for example there is a cell with 2025, all cells below that cell are 2025 data until there is a cell with 2026, then all cells below that are 2026]

# each row of these columns will be exported to our dataframe. Make sure the column names have "_" isnstead of " "


def extract_te4(path: str) -> pd.DataFrame:
    """
    Handles two known CBS template variants:
      - 5 columns: [export_vol, import_excl_fuels, import_vol, period, year]
        -> drop col B (index 1); keep export(0), import(2), period(3), year(4)
      - 7 columns: [export_excl, export_total, import_excl_fuels,
                     import_excl_diamonds, import_total, period, year]
        -> drop cols B,C,E (indices 1,2,4); keep A(0), D(3), period(5), year(6)

    Data rows are identified by content, not fixed row numbers: the
    second-to-last column (the period column) must contain a single roman
    numeral (e.g. "III", "IV") with no dash - this excludes quarterly rows
    like "I-III" and annual/title rows.
    """
    df = pd.read_excel(path, sheet_name="te1V", header=None)
    ncols = df.shape[1]
    period_col = ncols - 2
    year_col = ncols - 1

    if ncols == 5:
        export_col, import_col = 0, 2
    elif ncols == 7:
        export_col, import_col = 0, 3
    else:
        raise ValueError(f"Unrecognized te4 layout: {ncols} columns (expected 5 or 7)")

    df[year_col] = forward_fill_year(df[year_col])

    def is_single_roman(v) -> bool:
        return isinstance(v, str) and v.strip() in ROMAN_TO_NUM

    mask = df[period_col].apply(is_single_roman)
    keep = df[mask]

    out = pd.DataFrame({
        "fisher_export_volume": keep[export_col].values,
        "fisher_import_volume": keep[import_col].values,
    })
    out["Month"] = keep[period_col].apply(lambda r: NUM_TO_MONTH_NAME[ROMAN_TO_NUM[r.strip()]]).values
    out["Year"] = keep[year_col].astype(float).astype(int).values
    return out


# ------------------------------------------------------------------
# TD1 - Trade by country (current-month snapshot, one row)
# ------------------------------------------------------------------
# for each file which has "td1" in the name
# Save 2 values:
# Month 5D = month
# Year 6D = year

# drop all rows which do not have an int in their cell in the col A [country code]

# delete all columns except B, D, J 

# there are three columns left in the excel sheet. Now make two columns for the row we want to extract based on the following:
# "{country_name_from_column_1_row_1}_Import" = {value_from column_2_row_1}
#"{country_name_from_column_1_row_1}_Export" = {value_from column_3_row_1}
# Also add a "month" and "year" column using the previously saved values
# when the extraction is done, the columns of the data row should be 
"""
# Month [we saved this when we open the file,need to translate the roman numeral into english month name]
# Year [we saved this when we opened the file]
Austria Import,
Italy Import,
Ireland Import,
Estonia Import,
Bulgaria Import,
Belgium Import,
Germany Import,
Denmark Import,
Netherlands Import,
Hungary Import,
Greece Import,
Luxembourg Import,
Latvia Import,
Lithuania Import,
Malta Import,
Slovenia Import,
Slovakia Import,
Spain Import,
Poland Import,
Portugal Import,
Finland Import,
Czechia Import,
France Import,
Cyprus Import,
Croatia Import,
Romania Import,
Sweden Import,
Iceland Import,
Norway Import,
Switzerland Import,
Ukraine Import,
Albania Import,
...
Papua New Guinea Export,
Fiji Export,
Other Countries Export,
Unclassified Export,
"""
# So we're generating only one row of data from this file, and it will have all of the above columns and one row of values for those columns. Make sure the column names have "_" isnstead of " " 

def extract_td1(path: str) -> pd.DataFrame:
    """
    Extracts the current-month country breakdown as one wide row.
    Data rows are identified by content: column A (index 0) must hold a
    numeric country code. Only columns B (name), D (import), J (export)
    are kept.

    CBS repeats the label "Other Countries" once per continent/region
    (e.g. "Other Countries" under Europe, under Asia, under Africa...).
    These are summed into a single Other_Countries_Import /
    Other_Countries_Export column rather than kept as separate
    same-named columns.
    """
    df = pd.read_excel(path, sheet_name="table", header=None)

    # Month/year come from fixed cells, saved before any row filtering.
    month_raw = str(df.iloc[4, 3]).strip()   # cell D5
    year_raw = df.iloc[5, 3]                 # cell D6
    month_name = NUM_TO_MONTH_NAME[ROMAN_TO_NUM[month_raw]]
    year = int(year_raw)

    codes = pd.to_numeric(df[0], errors="coerce")
    keep = df[codes.notna()]
    keep = keep[[1, 3, 9]]
    keep.columns = ["country", "import_val", "export_val"]
    keep = keep[keep["country"].notna()]

    totals: dict[str, float] = {}
    order: list[str] = []
    for _, row in keep.iterrows():
        country = slugify(row["country"])
        for direction, val in (("Import", row["import_val"]), ("Export", row["export_val"])):
            col = f"{country}_{direction}"
            if col not in totals:
                totals[col] = 0.0
                order.append(col)
            if pd.notna(val):
                totals[col] += val

    col_names = ["Month", "Year"] + order
    values = [month_name, year] + [totals[c] for c in order]
    return pd.DataFrame([values], columns=col_names)


# ------------------------------------------------------------------
# MAIN PIPELINE
# ------------------------------------------------------------------

def dedup_columns(columns: list[str]) -> list[str]:
    """
    CBS repeats names like 'Other_Countries_Import' once per region, so the
    country-breakdown row has genuine duplicate column names. Pandas
    supports duplicate labels in memory, but round-tripping through CSV
    does not survive that (pd.read_csv auto-renames duplicates with a
    '.1' suffix, which then no longer matches the in-memory frame's raw
    duplicate names on the next run, breaking concat).

    This applies the same disambiguation pandas' CSV reader would (suffix
    '.1', '.2', ...), deterministically, so a freshly-extracted frame and
    a CSV-loaded frame always agree on column names.
    """
    seen = {}
    result = []
    for col in columns:
        if col not in seen:
            seen[col] = 0
            result.append(col)
        else:
            seen[col] += 1
            result.append(f"{col}.{seen[col]}")
    return result


def add_date_column(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    month_num = df["Month"].map({v: k for k, v in NUM_TO_MONTH_NAME.items()})
    df["date"] = pd.to_datetime(
        df["Year"].astype(str) + "-" + month_num.astype(str).str.zfill(2) + "-01 00:00"
    ).dt.strftime("%Y-%m-%d %H:%M")
    return df


def process_directory(input_dir: str) -> pd.DataFrame:
    extractors = {"ta2": extract_ta2, "ta3": extract_ta3, "te4": extract_te4, "td1": extract_td1}
    frames_by_type = {k: [] for k in extractors}

    for path in sorted(glob.glob(os.path.join(input_dir, "*.xlsx"))):
        fname = os.path.basename(path).lower()
        for key, fn in extractors.items():
            if key in fname:
                print(f"Processing {fname} as {key}...")
                try:
                    frames_by_type[key].append(fn(path))
                except Exception as e:
                    print(f"  FAILED: {e}")
                break

    merged_by_type = {}
    for key, frames in frames_by_type.items():
        if not frames:
            merged_by_type[key] = pd.DataFrame(columns=["Month", "Year"])
            continue
        combined = pd.concat(frames, ignore_index=True)
        # Overlapping months across multiple files: keep the last one seen
        # (later-processed file assumed to be a more recent/revised release).
        combined = combined.drop_duplicates(subset=["Month", "Year"], keep="last")
        merged_by_type[key] = combined

    for key, df in merged_by_type.items():
        merged_by_type[key] = df.set_index(["Year", "Month"])

    result = pd.concat(
        [merged_by_type["ta2"], merged_by_type["ta3"], merged_by_type["te4"], merged_by_type["td1"]],
        axis=1,
    )
    result.columns = dedup_columns(list(result.columns))
    result = result.reset_index()
    result = add_date_column(result)

    # Put date/Year/Month first
    other_cols = [c for c in result.columns if c not in ("date", "Year", "Month")]
    result = result[["date", "Year", "Month"] + other_cols]
    return result


def append_to_csv(new_df: pd.DataFrame, out_path: str) -> None:
    if os.path.exists(out_path) and os.stat(out_path).st_size > 0:
        existing = pd.read_csv(out_path)
        already = set(zip(existing["Year"], existing["Month"]))
        new_rows = new_df[~new_df.apply(lambda r: (r["Year"], r["Month"]) in already, axis=1)]
        combined = pd.concat([existing, new_rows], ignore_index=True)
    else:
        combined = new_df
    combined = combined.sort_values(["Year", "Month"], key=lambda s: s if s.name == "Year" else s.map(
        {v: k for k, v in NUM_TO_MONTH_NAME.items()}
    ))
    combined.to_csv(out_path, index=False)
    print(f"Wrote {len(combined)} total rows to {out_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir", help="Directory containing CBS xlsx files (ta2/ta3/td1/te4)")
    parser.add_argument("--out", default="monthly_trade_data.csv")
    args = parser.parse_args()

    result = process_directory(args.input_dir)
    append_to_csv(result, args.out)


if __name__ == "__main__":
    main()
