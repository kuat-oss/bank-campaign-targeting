# Builds excel/campaign_roi_model.xlsx from excel/segments.csv.
# All calculations are Excel formulas, so the assumptions can be changed in the file.
# usage: python excel/build_workbook.py
import csv
from pathlib import Path

from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation

HERE = Path(__file__).resolve().parent
SRC = HERE / "segments.csv"
OUT = HERE / "campaign_roi_model.xlsx"

BLUE = "2F6FDB"
INPUT_FILL = PatternFill("solid", fgColor="FFF4CC")
HEAD_FILL = PatternFill("solid", fgColor="E8EEF9")
GREEN_FILL = PatternFill("solid", fgColor="DFF2E8")
RED_FILL = PatternFill("solid", fgColor="FBE3E1")
BOLD = Font(bold=True)
TITLE = Font(bold=True, size=14)
MUTED = Font(color="656D76", italic=True)
THIN = Border(bottom=Side(style="thin", color="D0D5DB"))
EUR = '"€"#,##0'
EUR2 = '"€"#,##0.00'
PCT = "0.0%"
INT = "#,##0"


def header(ws, row, labels):
    for i, label in enumerate(labels, start=1):
        c = ws.cell(row=row, column=i, value=label)
        c.font = BOLD
        c.fill = HEAD_FILL
        c.alignment = Alignment(horizontal="center", wrap_text=True, vertical="center")
    ws.row_dimensions[row].height = 30


def build():
    rows = list(csv.DictReader(SRC.open()))
    wb = Workbook()

    # ---------------- Inputs ----------------
    inp = wb.active
    inp.title = "Inputs"
    inp["A1"] = "Campaign ROI model"
    inp["A1"].font = TITLE
    inp["A2"] = "Yellow cells are assumptions. Change them and every other sheet updates."
    inp["A2"].font = MUTED
    items = [
        (4, "Average deposit size", 5000, EUR, "Assumption"),
        (5, "Net interest margin the bank earns on it", 0.015, "0.0%", "Assumption"),
        (6, "Years the deposit is held", 2, "0", "Assumption"),
        (7, "Value of one new deposit to the bank", "=B4*B5*B6", EUR, "Formula: deposit x margin x years"),
        (8, "Cost of one call (agent time + phone)", 5, EUR2, "Assumption"),
        (9, "Break-even conversion rate", "=B8/B7", "0.00%", "A segment must convert above this to pay for its calls"),
        (11, "Campaign year to analyze", 2008, "0", "2008, 2009, 2010 or All"),
        (12, "Maximum calls per client", 3, "0", "Calls after this number are skipped in the plan"),
    ]
    for r, label, value, fmt, note in items:
        inp.cell(row=r, column=1, value=label)
        c = inp.cell(row=r, column=2, value=value)
        c.number_format = fmt
        if note == "Assumption" or r in (11, 12):
            c.fill = INPUT_FILL
        else:
            c.font = BOLD
        inp.cell(row=r, column=3, value=note).font = MUTED
    dv_year = DataValidation(type="list", formula1='"2008,2009,2010,All"', allow_blank=False)
    dv_att = DataValidation(type="list", formula1='"1,2,3,4"', allow_blank=False)
    inp.add_data_validation(dv_year)
    inp.add_data_validation(dv_att)
    dv_year.add("B11")
    dv_att.add("B12")
    inp["A14"] = "Source: UCI Bank Marketing dataset, 41,188 calls (May 2008 - Nov 2010). Costs and deposit values are not in the data."
    inp["A14"].font = MUTED
    inp.column_dimensions["A"].width = 44
    inp.column_dimensions["B"].width = 14
    inp.column_dimensions["C"].width = 60

    # ---------------- Data ----------------
    data = wb.create_sheet("Data")
    header(data, 1, ["Year", "Score", "Attempt", "Calls", "Subscriptions", "Attempt #", "In selected year",
                     "Score is profitable", "In plan"])
    for i, r in enumerate(rows, start=2):
        data.cell(row=i, column=1, value=int(r["campaign_year"]))
        data.cell(row=i, column=2, value=int(r["score"]))
        data.cell(row=i, column=3, value=str(r["attempt_bucket"]))
        data.cell(row=i, column=4, value=int(r["calls"])).number_format = INT
        data.cell(row=i, column=5, value=int(r["subscriptions"])).number_format = INT
        data.cell(row=i, column=6, value=f'=IF(C{i}="4+",4,VALUE(C{i}))')
        data.cell(row=i, column=7, value=f'=OR(Inputs!$B$11="All",A{i}=Inputs!$B$11)')
        data.cell(row=i, column=8, value=f"=INDEX('By score'!$H$5:$H$11,MATCH(B{i},'By score'!$A$5:$A$11,0))>0")
        data.cell(row=i, column=9, value=f"=AND(G{i},H{i},F{i}<=Inputs!$B$12)")
    last = len(rows) + 1
    data.freeze_panes = "A2"
    for col, w in zip("ABCDEFGHI", [8, 8, 9, 10, 13, 10, 14, 16, 10]):
        data.column_dimensions[col].width = w

    D = f"Data!$D$2:$D${last}"
    E = f"Data!$E$2:$E${last}"
    YEAR = f"Data!$G$2:$G${last}"

    def segment_sheet(name, title, key_label, keys, key_col, note):
        ws = wb.create_sheet(name)
        ws["A1"] = title
        ws["A1"].font = TITLE
        ws["A2"] = '="Year: "&Inputs!B11&"   |   value per deposit "&TEXT(Inputs!B7,"€#,##0")&"   |   cost per call "&TEXT(Inputs!B8,"€#,##0.00")'
        ws["A2"].font = MUTED
        header(ws, 4, [key_label, "Calls", "Subscriptions", "Conversion", "Revenue", "Call cost", "Profit",
                       "Profit per call", "Decision", "Max cost per call to break even"])
        first = 5
        for j, k in enumerate(keys):
            r = first + j
            ws.cell(row=r, column=1, value=k)
            match = f'{key_col},$A{r}'
            ws.cell(row=r, column=2, value=f"=SUMIFS({D},{YEAR},TRUE,{match})").number_format = INT
            ws.cell(row=r, column=3, value=f"=SUMIFS({E},{YEAR},TRUE,{match})").number_format = INT
            ws.cell(row=r, column=4, value=f"=IFERROR(C{r}/B{r},0)").number_format = PCT
            ws.cell(row=r, column=5, value=f"=C{r}*Inputs!$B$7").number_format = EUR
            ws.cell(row=r, column=6, value=f"=B{r}*Inputs!$B$8").number_format = EUR
            ws.cell(row=r, column=7, value=f"=E{r}-F{r}").number_format = EUR
            ws.cell(row=r, column=8, value=f"=IFERROR(G{r}/B{r},0)").number_format = EUR2
            ws.cell(row=r, column=9, value=f'=IF(B{r}=0,"-",IF(G{r}>0,"Call","Skip"))')
            ws.cell(row=r, column=10, value=f"=D{r}*Inputs!$B$7").number_format = EUR2
            for c in range(1, 11):
                ws.cell(row=r, column=c).border = THIN
        end = first + len(keys) - 1
        t = end + 1
        ws.cell(row=t, column=1, value="Total").font = BOLD
        for col, fmt in [("B", INT), ("C", INT), ("E", EUR), ("F", EUR), ("G", EUR)]:
            c = ws[f"{col}{t}"]
            c.value = f"=SUM({col}{first}:{col}{end})"
            c.number_format = fmt
            c.font = BOLD
        ws[f"D{t}"] = f"=IFERROR(C{t}/B{t},0)"
        ws[f"D{t}"].number_format = PCT
        ws[f"D{t}"].font = BOLD
        ws.conditional_formatting.add(f"I{first}:I{end}", CellIsRule(operator="equal", formula=['"Call"'], fill=GREEN_FILL))
        ws.conditional_formatting.add(f"I{first}:I{end}", CellIsRule(operator="equal", formula=['"Skip"'], fill=RED_FILL))
        ws.conditional_formatting.add(f"G{first}:G{end}", CellIsRule(operator="lessThan", formula=["0"], fill=RED_FILL))
        ws.cell(row=t + 2, column=1, value=note).font = MUTED
        ws.column_dimensions["A"].width = 16
        for col in "BCDEFGHI":
            ws.column_dimensions[col].width = 14
        ws.column_dimensions["J"].width = 18
        return ws

    segment_sheet(
        "By score", "Profit by scorecard score", "Score", list(range(-1, 6)), f"Data!$B$2:$B${last}",
        "Score = 3 if subscribed last campaign, -1 if refused last campaign, +1 mobile number, "
        "+1 student/retired/under 25/60+. See src/campaign/scorecard.py.",
    )
    segment_sheet(
        "By attempt", "Profit by call attempt", "Call number", ["1", "2", "3", "4+"], f"Data!$C$2:$C${last}",
        "Each row is the n-th call to the same client within one campaign.",
    )

    # ---------------- Summary ----------------
    s = wb.create_sheet("Summary", 1)
    s["A1"] = "Call everyone vs call by plan"
    s["A1"].font = TITLE
    s["A2"] = '="Year: "&Inputs!B11&". Plan = only profitable score levels, at most "&Inputs!B12&" calls per client."'
    s["A2"].font = MUTED
    header(s, 4, ["", "Call everyone", "Plan", "Difference"])
    IN_PLAN = f"Data!$I$2:$I${last}"
    lines = [
        ("Calls", f"=SUMIFS({D},{YEAR},TRUE)", f"=SUMIFS({D},{IN_PLAN},TRUE)", INT),
        ("Subscriptions", f"=SUMIFS({E},{YEAR},TRUE)", f"=SUMIFS({E},{IN_PLAN},TRUE)", INT),
        ("Conversion", "=IFERROR(B6/B5,0)", "=IFERROR(C6/C5,0)", PCT),
        ("Revenue", "=B6*Inputs!$B$7", "=C6*Inputs!$B$7", EUR),
        ("Call cost", "=B5*Inputs!$B$8", "=C5*Inputs!$B$8", EUR),
        ("Profit", "=B8-B9", "=C8-C9", EUR),
    ]
    for i, (label, a, b, fmt) in enumerate(lines, start=5):
        s.cell(row=i, column=1, value=label).font = BOLD if label == "Profit" else Font()
        for col, v in (("B", a), ("C", b)):
            c = s[f"{col}{i}"]
            c.value = v
            c.number_format = fmt
        d = s[f"D{i}"]
        d.value = f"=C{i}-B{i}"
        d.number_format = "+0.0%;-0.0%" if fmt == PCT else (f"+{fmt};-{fmt}" if fmt != INT else "+#,##0;-#,##0")
        for col in "ABCD":
            s[f"{col}{i}"].border = THIN
    s["A12"] = "Calls saved"
    s["B12"] = "=IFERROR(1-C5/B5,0)"
    s["B12"].number_format = PCT
    s["A13"] = "Subscriptions kept"
    s["B13"] = "=IFERROR(C6/B6,0)"
    s["B13"].number_format = PCT
    s["A15"] = "Change the year, the maximum calls per client or the cost assumptions on the Inputs sheet."
    s["A15"].font = MUTED
    s.column_dimensions["A"].width = 20
    for col in "BCD":
        s.column_dimensions[col].width = 16

    # no cached values are stored, so ask Excel to calculate everything on open
    wb.calculation.fullCalcOnLoad = True
    wb.save(OUT)
    print(f"wrote {OUT.relative_to(HERE.parent)} with {len(rows)} data rows")


if __name__ == "__main__":
    build()
