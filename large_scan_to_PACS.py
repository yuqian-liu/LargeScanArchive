import argparse
from shutil import copyfile, copytree, rmtree
from PhilipsSeriesExport import scanner_db, export, archive

# clean up series that already in PACS

# iterate g://Export/large_scans

archive.check_frame_number_pacs()
archive.clear_zip()
rmtree("DICOM")

# Export new series
db = scanner_db.PatientDB()
series_list = db.get_all_large_scans()

# if not complete in PACS, export to G://Export folder
for series_iuid in series_list :
    frame_number_scanner = db.get_series_frame_number_scanner(series_iuid)
    frame_number_pacs = archive.check_frame_number_pacs()
    if frame_number_pacs < frame_number_scanner :
        mrseries = db.get_series_OID(series_iuid).split("_")
        seriesid = examid = mrseries[1]
        examid = mrseries[2]
        plf = export.PhilipsLogFile()
        pe = plf.extract_exam(examid)
        export.export_series(pe, seriesid)





