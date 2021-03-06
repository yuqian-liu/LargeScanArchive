from PhilipsSeriesExport import scanner_db, export, pacs_utils
from shutil import rmtree
import os
import logging
from datetime import datetime

export_dir = 'E:\\export\\classic_series\\'
logging.basicConfig(filename = "G:\\Site\\LargeScanArchive-main\\" + "{:%Y-%m-%d}.log".format(datetime.now()), format='%(asctime)s %(message)s', filemode='w')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

db = scanner_db.PatientDB()
series_pkgs = [ f for f in os.listdir(export_dir) if f.endswith(".zip")]
series_exported = {}
for pkg in series_pkgs:
    series_iuid = pkg[:-4]
    pkg_name = os.path.join(export_dir,pkg)
#    os.remove(pkg_name)
    series_exported[series_iuid] = pkg
    print(pkg_name)

# get series, frame number, patient name triple from patientDB in scanner
frame_num_scanner, s_oid = db.get_all_series_frame_number()

# if not complete in PACS, export to G://Export folder,
# if ready in PACS, delete the package

for i, oid in enumerate(s_oid):
    fnum_s = frame_num_scanner[i]
    if int(fnum_s) > 16384:
        s_iuid, s_desc, patient_name = db.get_series_by_oid(s_oid[i])
        fnum_pacs = pacs_utils.check_frame_number_pacs(s_iuid[0])
        if fnum_pacs == '' :
            fnum_pacs = '0'
        logger.debug("Series: " + patient_name[0] + ", series: " + s_desc[0] + ", frames in scanner and PACS: " + fnum_s + "/" + fnum_pacs)
        # export series lacking frames and not in local drive
        #if int(fnum_pacs) < int(fnum_s) :
        if s_iuid[0] not in series_exported.keys():
            logger.debug("Not in E://Export, exporting...")
            seriesid, examid, patientid = db.get_OIDs_by_iuid(s_iuid[0])
            plf = export.PhilipsLogFile()
            pe = plf.extract_exam(examid[0])
            file_list, name = pe.collect_series_files(seriesid[0])
            logger.debug("Package name: " + s_iuid[0] + ".zip")
            export.zip_and_clean(file_list, s_iuid[0])
        else:
            logger.debug("Exported as" + s_iuid[0] + ".zip")
            series_exported.pop(s_iuid[0])

for pkg in series_exported:
    rmtree(series_exported.get(pkg))








