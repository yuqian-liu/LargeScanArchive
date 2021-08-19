from PhilipsSeriesExport import export
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Philips Series Export Tool')
    parser.add_argument('mrseries', help='MRSERIES_SeriesID_ExamID')
    parser.add_argument('-o','--out', help='file output types', default='XLORDS',choices='XLORDS')
    args = parser.parse_args()

    '''
        X = xml/rec files
        L = data/list files
        O = log file
        R = lab/raw files
        D = DICOM file
        S = sin file
    '''

    # set output file types
    if 'X' not in args.out:
        export.FileOutput.XMLREC = False
    if 'L' not in args.out:
        export.FileOutput.DATALIST = False
    if 'O' not in args.out:
        export.FileOutput.LOG = False
    if 'R' not in args.out:
        export.FileOutput.LABRAW = False
    if 'D' not in args.out:
        export.FileOutput.DICOM = False
    if 'S' not in args.out:
        export.FileOutput.SIN = False

    # extract the exam ID
    if not args.mrseries.upper().startswith('MRSERIES'):
        raise ValueError('mrseries must start with "MRSERIES_SeriesID_ExamID"')

    mrseries = args.mrseries.split('_')
    seriesid = examid = mrseries[1]
    examid = mrseries[2]

    plf = export.PhilipsLogFile()
    pe = plf.extract_exam(examid)

    export.export_series(pe,seriesid)