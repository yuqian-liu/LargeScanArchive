from PhilipsSeriesExport import scanner_db, export, pacs_utils
from shutil import rmtree
import os

export_dir = 'E:\\export\\classic_series\\'
db = scanner_db.PatientDB()

# get series_iuid, pkg_name tuple list of series in local drive
series_exported = {}
series_pkgs = [ f for f in os.listdir(export_dir) if f.endswith(".zip")]
for pkg in series_pkgs:
    series_iuid = pkg.split[:-4]
    pkg_name = os.path.join(export_dir,pkg)
    series_exported[series_iuid] = pkg_name
    print(pkg_name)

# get series, frame number, patient name triple from patientDB in scanner
frame_num_scanner, s_oid = db.get_all_series_frame_number()

# if not complete in PACS, export to G://Export folder,
# if ready in PACS, delete the package
for i, oid in enumerate(s_oid):
    fnum_s = frame_num_scanner[i]
    if fnum_s > 16000:
        s_iuid = db.get_series_iuid_by_oid(oid)
        fnum_pacs = pacs_utils.check_frame_number_pacs(s_iuid)
        s_iuid, s_desc, patient_name = db.get_series_by_oid(s_oid[i])
        print("Series lacking frames: " + patient_name[0] + ", series: " + s_desc[0] + ", " + fnum_s + ":" + fnum_pacs)
        # export series lacking frames and not in local drive
        if fnum_pacs < fnum_s and s_iuid not in series_exported.keys():
            print("Export")
            seriesid, examid, patientid = db.get_OIDs_by_iuid(s_iuid)
            plf = export.PhilipsLogFile()
            pe = plf.extract_exam(examid[0])
            file_list, name = pe.collect_series_files(seriesid[0])
            export.zip_and_clean(file_list, s_iuid)
        elif fnum_pacs == fnum_s:
            print("Delete")
            rmtree(series_exported.get(s_iuid))

# copy packages to another server








